# Naukri job search via SerpAPI google_jobs engine
# —————————————————————————————————————————————————————
# History of failed direct-scraping approaches (May 2026):
#   • Playwright headless  → blocked by Akamai TLS fingerprinting
#   • Playwright + stealth → same Akamai block
#   • Direct API (/jobapi/v3/search) → 406 "recaptcha required"
#   • RSS feeds (/rss/jobs/*.rss) → discontinued; returns HTML
#   • shine.com / foundit / timesjobs RSS → dead or HTML-only
#
# Current approach: SerpAPI google_jobs engine (direct, no SerperJobFinder wrapper).
# Naukri jobs appear prominently in Google Jobs results for Indian queries.
# SerperJobFinder is intentionally bypassed here because its date_posted:today
# chip causes timeouts on broad queries.

import os
import sys
import requests as _requests

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

_SERPAPI_URL = "https://serpapi.com/search.json"
_SERPER_URL  = "https://google.serper.dev/search"


def _hours_to_tbs(hours: int) -> str:
    """Convert hours window to Google tbs date-range filter string."""
    if hours <= 24:
        return "qdr:d"    # past day
    elif hours <= 72:
        return "qdr:w"    # /search has no 3-day granularity; use week as closest
    elif hours <= 168:
        return "qdr:w"    # past week
    elif hours <= 720:
        return "qdr:m"    # past month
    return ""             # no date filter


def _serpapi_search(query: str, serpapi_key: str, max_results: int,
                    tbs: str = "") -> list[dict]:
    """Call SerpAPI google_jobs and return normalised job dicts."""
    try:
        params = {
            "engine":   "google_jobs",
            "q":        query,
            "location": "India",
            "api_key":  serpapi_key,
            "num":      max_results,
        }
        if tbs:
            params["tbs"] = tbs

        r = _requests.get(_SERPAPI_URL, params=params, timeout=20)

        if r.status_code != 200:
            print(f"  [google_jobs_india]SerpAPI HTTP {r.status_code}")
            return []

        data = r.json()
        if "error" in data:
            print(f"  [google_jobs_india]SerpAPI error: {data['error']}")
            return []

        return _normalise_serpapi(data.get("jobs_results", []))

    except Exception as e:
        print(f"  [google_jobs_india]SerpAPI error: {e}")
        return []


def _serper_search(query: str, serper_key: str, max_results: int,
                   tbs: str = "") -> list[dict]:
    """Call Serper.dev /search (organic web results) and parse job listings."""
    try:
        body: dict = {
            "q":   f"{query} jobs site:naukri.com",
            "num": max(max_results, 10),
        }
        if tbs:
            body["tbs"] = tbs

        r = _requests.post(_SERPER_URL, headers={
            "X-API-KEY":    serper_key,
            "Content-Type": "application/json",
        }, json=body, timeout=15)

        if r.status_code != 200:
            print(f"  [google_jobs_india]Serper HTTP {r.status_code}")
            return []

        organic = r.json().get("organic", [])
        jobs: list[dict] = []
        for item in organic:
            title_raw = item.get("title", "")
            link      = item.get("link", "")
            snippet   = item.get("snippet", "")

            # Common format: "Job Title - Company | Naukri.com"
            parts   = title_raw.split(" - ")
            title   = parts[0].strip() if parts else title_raw
            company = parts[1].split("|")[0].strip() if len(parts) > 1 else ""

            jobs.append({
                "title":       title,
                "company":     company,
                "location":    "",
                "url":         link,
                "description": snippet,
                "skills":      [],
                "posted":      "",
                "source":      "google_jobs_india",
            })

        return jobs

    except Exception as e:
        print(f"  [google_jobs_india]Serper error: {e}")
        return []


def _best_link(apply_options: list) -> str:
    """Pick the best apply URL from SerpAPI's apply_options list."""
    try:
        from platform_filter import best_trusted_link, BLOCKED
        trusted = best_trusted_link(apply_options)
        if trusted:
            return trusted
        for opt in apply_options:
            lnk = opt.get("link", "")
            if not any(b in lnk.lower() for b in BLOCKED):
                return lnk
        return apply_options[0].get("link", "") if apply_options else ""
    except ImportError:
        return apply_options[0].get("link", "") if apply_options else ""


def _normalise_serpapi(items: list) -> list[dict]:
    out = []
    for item in items:
        options = item.get("apply_options", [])
        url = _best_link(options) if options else ""
        if not url and item.get("job_id"):
            url = f"https://www.google.com/search?ibp=htl;jobs&q={item['job_id']}"

        desc = item.get("description", "")
        if not desc:
            highlights = item.get("job_highlights", [])
            desc = " ".join(
                part for h in highlights for part in h.get("items", [])
            )

        exts = item.get("detected_extensions", {})
        out.append({
            "title":       item.get("title", "Unknown").strip(),
            "company":     item.get("company_name", "Unknown").strip(),
            "location":    item.get("location", "").strip(),
            "url":         url,
            "description": desc,
            "skills":      [],
            "posted":      exts.get("posted_at", ""),
            "source":      "google_jobs_india",
        })
    return out


def _normalise_serper(items: list) -> list[dict]:
    out = []
    for item in items:
        related = item.get("related_links", [])
        url = related[0].get("link", "") if related else item.get("link", "")

        posted = ""
        for ext in item.get("extensions", []):
            if any(w in ext for w in ("ago", "day", "hour", "week")):
                posted = ext
                break

        out.append({
            "title":       item.get("title", "Unknown").strip(),
            "company":     item.get("company", "Unknown").strip(),
            "location":    item.get("location", "").strip(),
            "url":         url,
            "description": item.get("description", ""),
            "skills":      [],
            "posted":      posted,
            "source":      "google_jobs_india",
        })
    return out


class NaukriScraper:
    """
    Fetches Indian job listings via SerpAPI / Serper google_jobs engine.

    Fetches Indian jobs via Serper (primary, 2,500/month free) or
    SerpAPI google_jobs engine (fallback, 100/month free).
    Source label: "google_jobs_india" (Naukri/Shine/Foundit appear prominently).

    Primary: Serper (SERPER_API_KEY) → Fallback: SerpAPI (SERPAPI_KEY).
    """

    def search(
        self,
        keyword: str,
        location: str = "india",
        max_results: int = 30,
        hours_old: int = 168,
    ) -> list[dict]:
        serpapi_key = os.getenv("SERPAPI_KEY", "")
        serper_key  = os.getenv("SERPER_API_KEY", "")

        if not serpapi_key and not serper_key:
            print("  [google_jobs_india] No SERPER_API_KEY or SERPAPI_KEY set — returning []")
            return []

        tbs   = _hours_to_tbs(hours_old)
        query = f"{keyword} {location}"
        print(f"  [google_jobs_india] Searching Google Jobs: {query!r} (tbs={tbs or 'none'})")

        jobs: list[dict] = []

        # Serper is primary (2,500 free/month vs SerpAPI's 100)
        if serper_key:
            jobs = _serper_search(query, serper_key, max_results, tbs=tbs)
            print(f"  [google_jobs_india] Serper returned {len(jobs)} jobs")

        if not jobs and serpapi_key:
            print("  [google_jobs_india] Falling back to SerpAPI…")
            jobs = _serpapi_search(query, serpapi_key, max_results, tbs=tbs)
            print(f"  [google_jobs_india] SerpAPI returned {len(jobs)} jobs")

        # Deduplicate by title+company
        seen: set[str] = set()
        unique: list[dict] = []
        for j in jobs:
            k = j["title"].lower() + "|" + j["company"].lower()
            if k not in seen:
                seen.add(k)
                unique.append(j)

        result = unique[:max_results]
        print(f"  [google_jobs_india]{len(result)} jobs after dedup")
        return result

    def fetch_description(self, url: str) -> str:
        """Full JD fetch blocked by Akamai — description snippet is in search() results."""
        return ""
