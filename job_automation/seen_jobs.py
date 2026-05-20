"""
seen_jobs.py — cross-run deduplication via a persistent URL store.

Each job URL is stored in seen_jobs.json at the project root.
On each search run, jobs whose URL is already in the file are filtered out,
and newly returned jobs are added to the file.

Public API:
    load_seen()          → set[str]  (all seen URLs)
    save_seen(urls)      → None      (write full set back to file)
    filter_seen(jobs)    → list      (remove already-seen jobs)
    mark_seen(jobs)      → None      (persist new URLs)
    clear_seen()         → None      (delete the file — fresh start)
"""

from __future__ import annotations
import json
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN_FILE = os.path.join(_PROJECT_ROOT, "seen_jobs.json")


def load_seen() -> set[str]:
    """Return the set of all previously seen job URLs."""
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(urls: set[str]) -> None:
    """Write the full set of seen URLs back to disk."""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, indent=2)


def filter_seen(jobs: list) -> tuple[list, int]:
    """
    Remove jobs whose URL is already in seen_jobs.json.

    Returns (new_jobs, skipped_count).
    """
    seen = load_seen()
    new_jobs: list = []
    skipped = 0
    for job in jobs:
        url = (job.get("url") or job.get("apply_link") or "").strip()
        if url and url in seen:
            skipped += 1
        else:
            new_jobs.append(job)
    return new_jobs, skipped


def mark_seen(jobs: list) -> None:
    """Add URLs from jobs to seen_jobs.json (merges with existing)."""
    seen = load_seen()
    for job in jobs:
        url = (job.get("url") or job.get("apply_link") or "").strip()
        if url:
            seen.add(url)
    save_seen(seen)
    print(f"[SeenJobs] Saved {len(seen)} total seen URLs → {SEEN_FILE}")


def clear_seen() -> None:
    """Delete the seen_jobs.json file (fresh start)."""
    if os.path.exists(SEEN_FILE):
        os.remove(SEEN_FILE)
        print(f"[SeenJobs] Cleared {SEEN_FILE}")
    else:
        print("[SeenJobs] Nothing to clear — file does not exist")
