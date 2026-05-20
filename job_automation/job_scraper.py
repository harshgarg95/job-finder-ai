"""
job_scraper.py — unified scraper for LinkedIn, Indeed, and Naukri.

Public API:
    scrape_jobs(keyword, location, platforms, max_results) -> list[dict]

Each returned dict has keys:
    title, company, location, url, description, skills, posted, source

Platforms:
    linkedin / indeed  →  python-jobspy (fast, API-backed)
    naukri             →  NaukriScraper (JSON API w/ cookies, Playwright fallback)
    all                →  all three (default)
"""

from __future__ import annotations
import os
import pandas as pd
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


# ── Shared helpers ─────────────────────────────────────────────────────────

def _safe(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _normalise_jobspy_row(row: pd.Series) -> dict:
    """Convert a JobSpy DataFrame row to the shared job-dict schema."""
    skills_raw = row.get("job_function") or row.get("skills") or []
    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    elif isinstance(skills_raw, list):
        skills = skills_raw
    else:
        skills = []

    return {
        "title":       _safe(row.get("title", "Unknown")),
        "company":     _safe(row.get("company", "Unknown")),
        "location":    _safe(row.get("location", "")),
        "url":         _safe(row.get("job_url", "")),
        "description": _safe(row.get("description", "")),
        "skills":      skills,
        "posted":      _safe(row.get("date_posted") or row.get("date_posted_utc", "")),
        "source":      _safe(row.get("site", "unknown")).lower(),
    }


# ── Platform scrapers ──────────────────────────────────────────────────────

class JobScraper:
    """
    Wraps python-jobspy for LinkedIn and Indeed, and NaukriScraper for Naukri.

    Preferred entry point: the module-level scrape_jobs() function.
    Use the class directly only when you need the per-platform methods.
    """

    JOBSPY_PLATFORMS = frozenset(["linkedin", "indeed"])

    # ── JobSpy (LinkedIn + Indeed) ─────────────────────────────────────────
    def scrape_jobspy(
        self,
        keyword: str,
        location: str = "Hyderabad, India",
        platforms: Optional[list[str]] = None,
        max_results: int = 30,
        hours_old: int = 168,
        linkedin_fetch_description: bool = True,
    ) -> list[dict]:
        """
        Fetch LinkedIn and/or Indeed jobs via python-jobspy.

        Args:
            keyword:    Search query / job title.
            location:   City or region string.
            platforms:  Subset of ["linkedin", "indeed"].
            max_results: Max results per platform.
            hours_old:  Only return jobs posted within this many hours (default 168 = 7 days).
            linkedin_fetch_description: Fetch full JDs from LinkedIn (slower).

        Returns:
            List of normalised job dicts.
        """
        if platforms is None:
            platforms = ["linkedin", "indeed"]

        platforms = [p for p in platforms if p in self.JOBSPY_PLATFORMS]
        if not platforms:
            return []

        try:
            from jobspy import scrape_jobs as _scrape  # type: ignore
        except ImportError:
            raise RuntimeError(
                "python-jobspy not installed. Run: pip install python-jobspy"
            )

        print(f"  [JobSpy] Searching {platforms} for '{keyword}' in '{location}' "
              f"(max {max_results}/platform, hours_old={hours_old})…")

        try:
            df: pd.DataFrame = _scrape(
                site_name=platforms,
                search_term=keyword,
                location=location,
                results_wanted=max_results,
                hours_old=hours_old,
                linkedin_fetch_description=linkedin_fetch_description,
                country_indeed="India",
                verbose=0,
            )
        except Exception as e:
            print(f"  [JobSpy] scrape_jobs failed: {e}")
            return []

        if df is None or df.empty:
            print("  [JobSpy] No results returned.")
            return []

        jobs = [_normalise_jobspy_row(row) for _, row in df.iterrows()]

        for p in platforms:
            n = sum(1 for j in jobs if j["source"] == p)
            print(f"  [JobSpy]   {p}: {n} jobs")

        return jobs

    # ── Naukri ─────────────────────────────────────────────────────────────
    def scrape_naukri(
        self,
        keyword: str,
        location: str = "Hyderabad, India",
        max_results: int = 30,
        hours_old: int = 168,
    ) -> list[dict]:
        """
        Fetch Naukri jobs via NaukriScraper (SerpAPI google_jobs engine).

        Returns:
            List of normalised job dicts (source="naukri").
        """
        try:
            from job_automation.naukri_scraper import NaukriScraper
        except ImportError:
            from naukri_scraper import NaukriScraper

        scraper = NaukriScraper()
        jobs = scraper.search(
            keyword=keyword,
            location=location,
            max_results=max_results,
            hours_old=hours_old,
        )
        print(f"  [Naukri] {len(jobs)} jobs returned")
        return jobs

    # ── Main unified method ────────────────────────────────────────────────
    def scrape(
        self,
        keyword: str,
        location: str = "Hyderabad, India",
        platforms: Optional[list[str]] = None,
        max_results: int = 30,
        hours_old: int = 168,
    ) -> list[dict]:
        """
        Scrape all requested platforms and return a combined list.

        Args:
            keyword:     Job title or search query.
            location:    City / region.
            platforms:   List from ["linkedin", "indeed", "naukri", "all"].
                         "all" expands to all three. Defaults to ["all"].
            max_results: Per-platform cap.
            hours_old:   Only return jobs posted within this many hours (default 168 = 7 days).

        Returns:
            Combined list of job dicts (NOT deduplicated — use aggregator for that).
        """
        if platforms is None:
            platforms = ["all"]

        # Expand "all"
        expanded: list[str] = []
        for p in platforms:
            if p == "all":
                expanded.extend(["linkedin", "indeed", "naukri"])
            else:
                expanded.append(p)
        platforms = list(dict.fromkeys(expanded))  # preserve order, drop dupes

        all_jobs: list[dict] = []

        # JobSpy platforms
        jobspy_plats = [p for p in platforms if p in self.JOBSPY_PLATFORMS]
        if jobspy_plats:
            all_jobs.extend(
                self.scrape_jobspy(
                    keyword=keyword,
                    location=location,
                    platforms=jobspy_plats,
                    max_results=max_results,
                    hours_old=hours_old,
                )
            )

        # Naukri
        if "naukri" in platforms:
            all_jobs.extend(
                self.scrape_naukri(
                    keyword=keyword,
                    location=location,
                    max_results=max_results,
                    hours_old=hours_old,
                )
            )

        return all_jobs


# ── Module-level convenience function ──────────────────────────────────────

def scrape_jobs(
    keyword: str,
    location: str = "Hyderabad, India",
    platforms: Optional[list[str]] = None,
    max_results: int = 30,
    hours_old: int = 168,
) -> list[dict]:
    """
    Convenience wrapper — creates a JobScraper and calls .scrape().

    Usage:
        from job_automation.job_scraper import scrape_jobs

        jobs = scrape_jobs("product manager", "Hyderabad",
                           platforms=["linkedin"], max_results=5)
        for j in jobs:
            print(j["title"], j["company"], j["url"])

    Platform choices: "linkedin", "indeed", "naukri", "all"
    """
    return JobScraper().scrape(
        keyword=keyword,
        location=location,
        platforms=platforms if platforms is not None else ["all"],
        max_results=max_results,
        hours_old=hours_old,
    )
