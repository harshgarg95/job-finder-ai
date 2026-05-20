"""
salary_filter.py — extract salary from job descriptions and filter low-pay roles.

Target salary range : ₹23–25 LPA
Filter threshold    : ₹18 LPA  (jobs explicitly stating below this are removed)
Jobs with no salary stated → always kept (can't know without seeing JD)

Handles formats:
  "25 LPA", "25 lakhs", "25L CTC"
  "20-30 LPA", "₹20-30 lakhs"
  "2500000" annual in INR
  "2.5L to 3L"
"""

from __future__ import annotations
import re
from typing import Optional, Tuple

# ── Salary targets (LPA) ──────────────────────────────────────────────────
TARGET_MIN_LPA  = 23
TARGET_MAX_LPA  = 25
FILTER_BELOW_LPA = 18   # jobs explicitly stating < this are removed


# ── Extraction ─────────────────────────────────────────────────────────────

# Range: "20-30 LPA", "20 to 30 lakhs", "₹20–30L", "₹25 LPA to ₹30 LPA"
_RANGE_RE = re.compile(
    r'(?:₹|rs\.?\s*)?'
    r'(\d+(?:\.\d+)?)\s*'
    r'(?:l(?:akh)?s?|lpa|ctc|l\b)?'
    r'\s*(?:to|-|–)\s*'
    r'(?:₹|rs\.?\s*)?'           # optional currency symbol before 2nd number
    r'(\d+(?:\.\d+)?)\s*'
    r'(?:l(?:akh)?s?|lpa|ctc|per annum|pa\b)',
    re.IGNORECASE,
)

# Single: "25 LPA", "25 lakhs", "25L CTC"
_SINGLE_RE = re.compile(
    r'(?:₹|rs\.?\s*)?'
    r'(\d+(?:\.\d+)?)\s*'
    r'(?:l(?:akh)?s?|lpa|ctc|per annum)',
    re.IGNORECASE,
)


_FALSE_POSITIVE_BEFORE = [
    '%', 'percent', 'accuracy', 'score', 'growth', 'increase',
    'reduce', 'improve', 'achieve', 'complete', 'success', 'rate',
    'no.', 'number', 'funding', 'revenue', 'raised',
]


def _is_salary_context(text: str, match_start: int) -> bool:
    """
    Return True when the matched number appears in a salary context.
    Guards against false positives from percentages, counts, funding figures.
    """
    before = text[max(0, match_start - 60): match_start]
    after  = text[match_start: min(len(text), match_start + 30)]

    # Reject if preceded by percentage/non-salary indicators
    if any(fp in before for fp in _FALSE_POSITIVE_BEFORE):
        return False

    # Reject "100 per cent" / "100% …" patterns that leak through
    if re.search(r'\b100\s*%', before[-10:] + after[:5]):
        return False

    return True


def extract_salary_lpa(text: str) -> Optional[Tuple[float, float]]:
    """
    Extract salary range from any text field.
    Returns (min_lpa, max_lpa) or None.

    Guards:
      - Sanity cap: never return > 99 LPA (avoids false positives from
        headcount, percentages, funding numbers)
      - Context guard: _is_salary_context() rejects matches preceded by
        percentage/count indicators
    """
    if not text:
        return None

    text_lower = text.lower()

    # ── Try range pattern — iterate all matches, take first valid ──────────
    for m in _RANGE_RE.finditer(text_lower):
        lo, hi = float(m.group(1)), float(m.group(2))
        # Convert raw INR (e.g. 2500000 → 25)
        if hi > 200:
            lo /= 100_000
            hi /= 100_000
        # Sanity cap: > 99 LPA is unrealistic for India IC/mgmt roles
        if lo > 99 or hi > 99:
            continue
        if not _is_salary_context(text_lower, m.start()):
            continue
        return (round(lo, 1), round(hi, 1))

    # ── Try single-value pattern ───────────────────────────────────────────
    for m in _SINGLE_RE.finditer(text_lower):
        val = float(m.group(1))
        if val > 200:
            val /= 100_000
        if val > 99:
            continue
        if not _is_salary_context(text_lower, m.start()):
            continue
        return (round(val, 1), round(val, 1))

    return None


def salary_label(min_lpa: Optional[float], max_lpa: Optional[float]) -> str:
    """Human-readable label for the salary range."""
    if min_lpa is None:
        return "Not stated"
    if min_lpa == max_lpa:
        return f"₹{min_lpa:.0f} LPA"
    return f"₹{min_lpa:.0f}–{max_lpa:.0f} LPA"


# ── Filter ─────────────────────────────────────────────────────────────────

def salary_filter(jobs: list) -> list:
    """
    Annotate jobs with salary fields and remove jobs clearly below threshold.

    Fields added to each job:
      salary_min_lpa  — float or None
      salary_max_lpa  — float or None
      salary_label    — "₹20–30 LPA" / "Not stated"
      salary_fit      — "in_target_range" | "below_target_negotiable" |
                        "too_low" | "unknown"

    Jobs with salary_fit="too_low" are dropped.
    """
    kept    : list = []
    removed : int  = 0

    for job in jobs:
        desc  = job.get("description", "") or ""
        title = job.get("title", "")       or ""

        # Try description first, fall back to title line
        salary_range = extract_salary_lpa(desc) or extract_salary_lpa(title)

        if salary_range:
            lo, hi = salary_range
            job["salary_min_lpa"] = lo
            job["salary_max_lpa"] = hi
            job["salary_label"]   = salary_label(lo, hi)

            if lo >= TARGET_MIN_LPA or hi >= TARGET_MIN_LPA:
                job["salary_fit"] = "in_target_range"
            elif hi >= FILTER_BELOW_LPA:
                job["salary_fit"] = "below_target_negotiable"
            else:
                # Explicitly below the filter floor — skip
                job["salary_fit"] = "too_low"
                removed += 1
                continue
        else:
            job["salary_min_lpa"] = None
            job["salary_max_lpa"] = None
            job["salary_label"]   = "Not stated"
            job["salary_fit"]     = "unknown"

        kept.append(job)

    if removed:
        print(f"[Salary Filter] Removed {removed} jobs explicitly below "
              f"₹{FILTER_BELOW_LPA} LPA")

    breakdown: dict[str, int] = {}
    for j in kept:
        fit = j.get("salary_fit", "unknown")
        breakdown[fit] = breakdown.get(fit, 0) + 1
    print(f"[Salary Filter] Kept {len(kept)} jobs: {breakdown}")

    return kept
