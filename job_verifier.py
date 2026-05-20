"""
Job URL verifier — checks HTTP status and basic title match for each job.
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

_TIMEOUT = 8


def verify_job_url(job: dict) -> dict:
    """
    Check whether a job's apply_link is reachable.

    Returns:
        {
            "title": str,
            "company": str,
            "url": str,
            "status_code": int | None,
            "reachable": bool,
            "error": str | None
        }
    """
    url = job.get('apply_link') or job.get('url', '')
    result = {
        "title": job.get('title', 'Unknown'),
        "company": job.get('company', 'Unknown'),
        "url": url,
        "status_code": None,
        "reachable": False,
        "error": None,
    }

    if not url or url == '#':
        result["error"] = "No URL"
        return result

    try:
        resp = requests.head(url, headers=_HEADERS, timeout=_TIMEOUT,
                             allow_redirects=True)
        result["status_code"] = resp.status_code
        result["reachable"] = resp.status_code < 400
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)[:60]}"
    except Exception as e:
        result["error"] = str(e)[:80]

    return result


def verify_all_jobs(jobs: list, max_workers: int = 5) -> list:
    """
    Verify all jobs in parallel.

    Returns list of verification dicts (same order as input).
    """
    results = [None] * len(jobs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(verify_job_url, job): i
            for i, job in enumerate(jobs)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                job = jobs[idx]
                results[idx] = {
                    "title": job.get('title', 'Unknown'),
                    "company": job.get('company', 'Unknown'),
                    "url": job.get('apply_link') or job.get('url', ''),
                    "status_code": None,
                    "reachable": False,
                    "error": str(e)[:80],
                }

    return results


if __name__ == "__main__":
    test_jobs = [
        {"title": "Product Manager", "company": "LinkedIn",
         "apply_link": "https://www.linkedin.com/jobs/"},
        {"title": "Data Scientist", "company": "Naukri",
         "apply_link": "https://www.naukri.com/jobs"},
        {"title": "Broken Link", "company": "Test",
         "apply_link": "https://thisdomaindoesnotexist12345.com/job/999"},
    ]

    print("Verifying test jobs...")
    results = verify_all_jobs(test_jobs)
    for r in results:
        status = f"HTTP {r['status_code']}" if r['status_code'] else r.get('error', 'Unknown')
        icon = "✅" if r['reachable'] else "❌"
        print(f"{icon} {r['title']} @ {r['company']} — {status}")
