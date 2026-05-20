"""
link_checker.py — parallel HTTP liveness checks for job URLs.

Returns one of: live | dead | login_required | timeout | error | invalid
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

_LOGIN_SIGNALS = [
    "login", "signin", "sign-in", "auth/", "session",
    "access-denied", "unauthorized", "accounts.google",
    "linkedin.com/login", "indeed.com/account",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def check_url(url: str, timeout: int = 8) -> str:
    """
    Return liveness status for a single URL.

    'live'            — 2xx/3xx resolved to a real page
    'dead'            — 404 or 410 (posting removed)
    'login_required'  — 401/403 or redirect to login page
    'timeout'         — request timed out
    'invalid'         — empty or non-http URL
    'error'           — any other exception
    'error_NNN'       — specific HTTP error code
    """
    if not url or not url.startswith("http"):
        return "invalid"

    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers=_HEADERS,
        )
        final_url = resp.url.lower()
        code = resp.status_code

        if code in (404, 410):
            return "dead"
        if code in (401, 403):
            return "login_required"
        if code >= 400:
            return f"error_{code}"
        if any(s in final_url for s in _LOGIN_SIGNALS):
            return "login_required"
        return "live"

    except requests.exceptions.Timeout:
        return "timeout"
    except requests.exceptions.SSLError:
        return "error"
    except requests.exceptions.ConnectionError:
        return "dead"
    except Exception:
        return "error"


def check_urls_parallel(
    jobs: list,
    max_workers: int = 10,
    rate_delay: float = 0.05,
) -> list:
    """
    Check all job URLs concurrently; populate job['link_status'] in-place.

    Returns the same list with link_status set on every job.
    """
    urls = [j.get("url", "") for j in jobs]
    results: dict[int, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(check_url, url): i
            for i, url in enumerate(urls)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = "error"
            if rate_delay:
                time.sleep(rate_delay)

    for i, job in enumerate(jobs):
        job["link_status"] = results.get(i, "unchecked")

    live          = sum(1 for j in jobs if j.get("link_status") == "live")
    dead          = sum(1 for j in jobs if j.get("link_status") == "dead")
    login         = sum(1 for j in jobs if j.get("link_status") == "login_required")
    other         = len(jobs) - live - dead - login

    print(
        f"[LinkChecker] Live: {live} | Dead: {dead} | "
        f"Login-required: {login} | Other: {other}"
    )
    return jobs
