"""
company_filter.py — strip staffing-agency and hidden-employer listings
before they waste Groq quota.

Two signals trigger removal:
  1. Company name matches a known staffing/body-shop keyword.
  2. Description contains "our client" / "for our client" / "confidential company"
     (recruiter-speak for an employer they won't name).
"""

STAFFING_KEYWORDS: list[str] = [
    # Global staffing majors
    "crossover",
    "syntel",
    "mastech",
    "igate",
    "kforce",
    " staffing",          # leading space avoids "Amazon Staffing" edge case
    "manpower",
    "adecco",
    "randstad",
    "kelly services",
    "allegis",
    # Indian IT body shops / contract-staffing
    "quess corp",
    "quess it",
    "teamlease",
    "firstsource",
    # Job-board aggregators that post fake/scraped listings
    "hireminthub",
    "hirequill",
    "talent500",
    "naukri.com",         # catch the catch-all "Naukri.com" company placeholder
]

_HIDDEN_EMPLOYER_SIGNALS: list[str] = [
    "our client",
    "for our client",
    "client company",
    "confidential company",
    "client organization",
    "our esteemed client",
]


def company_filter(jobs: list) -> list:
    """
    Return jobs with staffing agencies and hidden-employer listings removed.
    Modifies nothing — returns a new list.
    """
    kept: list = []
    removed = 0

    for job in jobs:
        company_lower = (job.get("company") or "").lower()
        desc_lower    = (job.get("description") or "").lower()

        is_staffing = any(kw in company_lower for kw in STAFFING_KEYWORDS)
        is_hidden   = any(sig in desc_lower for sig in _HIDDEN_EMPLOYER_SIGNALS)

        if is_staffing or is_hidden:
            removed += 1
        else:
            kept.append(job)

    if removed:
        print(f"[CompanyFilter] Removed {removed} staffing-agency / hidden-employer listings")

    return kept
