"""
groq_key_manager.py — round-robin Groq API key rotation.

Reads keys from .env in priority order:
  GROQ_API_KEY_1, GROQ_API_KEY_2, ... GROQ_API_KEY_5
  GROQ_API_KEY   (legacy single key — inserted at position 0)

On a 429:
  - Per-minute limit → key is cooled-off for 65 s, next key tried.
  - Daily quota      → key is marked exhausted until midnight UTC.

Once all keys are exhausted the caller gets a RuntimeError and should
fall back to keyword-only scoring.
"""

from __future__ import annotations
import os
import time
from datetime import datetime, timezone


class GroqKeyManager:
    """
    Manages multiple Groq API keys with automatic rotation on rate limits.
    """

    def __init__(self):
        self.keys: list[str] = self._load_keys()
        # Optimistic starting estimate — updated from response headers
        self.remaining: dict[str, int]   = {k: 14_400 for k in self.keys}
        self.exhausted_until: dict[str, float] = {}   # key → UNIX timestamp

    # ── Key loading ────────────────────────────────────────────────────────

    def _load_keys(self) -> list[str]:
        """Return deduplicated list of non-empty API keys from the environment."""
        from dotenv import load_dotenv
        load_dotenv()

        seen: set[str] = set()
        keys: list[str] = []

        # Legacy single-key first so it keeps its "primary" position
        single = (os.getenv("GROQ_API_KEY") or "").strip()
        if single and single not in seen:
            seen.add(single)
            keys.append(single)

        # Numbered keys GROQ_API_KEY_1 … GROQ_API_KEY_5
        for i in range(1, 6):
            k = (os.getenv(f"GROQ_API_KEY_{i}") or "").strip()
            if k and k not in seen:
                seen.add(k)
                keys.append(k)

        if not keys:
            raise ValueError(
                "No Groq API keys found. Set GROQ_API_KEY or GROQ_API_KEY_1 in .env"
            )

        print(f"[GroqKeyManager] Loaded {len(keys)} API key(s)")
        return keys

    # ── Key selection ──────────────────────────────────────────────────────

    def get_best_key(self) -> str:
        """
        Return the available key with the most remaining requests.
        Raises RuntimeError when every key is currently exhausted.
        """
        now = time.time()
        available = {
            k: self.remaining[k]
            for k in self.keys
            if self.exhausted_until.get(k, 0) < now
        }

        if not available:
            soonest = min(self.exhausted_until.values())
            wait    = max(0, soonest - now)
            raise RuntimeError(
                f"All {len(self.keys)} Groq key(s) exhausted. "
                f"Resets in {wait / 60:.0f} min "
                f"(midnight UTC ≈ 5:30 am IST). "
                "Falling back to keyword-only scoring."
            )

        return max(available, key=lambda k: available[k])

    # ── Header-based quota tracking ────────────────────────────────────────

    def update_from_headers(self, key: str, headers) -> None:
        """
        Parse Groq rate-limit response headers and update internal counters.
        Called after a successful API response.
        """
        try:
            remaining = int(headers.get("x-ratelimit-remaining-requests", -1))
            if remaining >= 0:
                self.remaining[key] = remaining

            reset_str = headers.get("x-ratelimit-reset-requests", "")
            if reset_str and "s" in reset_str:
                secs = float(reset_str.replace("s", "").strip())
                # > 1 hour means daily limit rather than per-minute limit
                if secs > 3600:
                    self.exhausted_until[key] = time.time() + secs
                    self.remaining[key]        = 0
        except (ValueError, TypeError):
            pass

    # ── Rate-limit markers ─────────────────────────────────────────────────

    def mark_rate_limited(self, key: str) -> None:
        """Cool-off a key for 65 s (per-minute RPM limit hit)."""
        self.exhausted_until[key] = time.time() + 65
        print(f"[GroqKeyManager] Key …{key[-6:]} hit per-minute limit — "
              f"cooling off 65 s, switching to next key.")

    def mark_daily_exhausted(self, key: str) -> None:
        """Mark a key as fully exhausted until the next midnight UTC."""
        midnight_utc = (
            datetime.now(timezone.utc)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
            + 86_400          # next midnight
        )
        self.exhausted_until[key] = midnight_utc
        self.remaining[key]       = 0
        print(f"[GroqKeyManager] Key …{key[-6:]} daily quota exhausted — "
              f"resets at midnight UTC (≈ 5:30 am IST).")

    def mark_error(self, key: str, error_str: str) -> None:
        """Dispatch to the right marker based on the error message."""
        lower = error_str.lower()
        if "daily" in lower or "quota" in lower or "tokens_per_day" in lower:
            self.mark_daily_exhausted(key)
        else:
            self.mark_rate_limited(key)

    # ── Status ─────────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, str]:
        """Human-readable status for each key (shown in healthcheck / logs)."""
        now = time.time()
        out: dict[str, str] = {}
        for i, key in enumerate(self.keys, 1):
            label = f"key_{i} (…{key[-6:]})"
            ex    = self.exhausted_until.get(key, 0)
            if ex > now:
                wait = ex - now
                out[label] = f"EXHAUSTED — resets in {wait / 60:.0f} min"
            else:
                rem = self.remaining.get(key, "?")
                out[label] = f"OK — ~{rem} requests remaining"
        return out

    @property
    def any_available(self) -> bool:
        """True when at least one key is not currently exhausted."""
        now = time.time()
        return any(self.exhausted_until.get(k, 0) < now for k in self.keys)
