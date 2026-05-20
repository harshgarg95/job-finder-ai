"""
Platform filter — keeps jobs from trusted job boards and company career pages,
rejects scrapers and low-quality aggregators.
"""

import logging
_log = logging.getLogger('platform_filter')

# Substrings that indicate a trusted platform (checked against the full URL)
TRUSTED = [
    'linkedin.com',
    'naukri.com',
    'indeed.com', 'indeed.co.in',
    'glassdoor.com', 'glassdoor.co.in',
    'shine.com',
    'instahyre.com',
    'hirist.com',
    'cutshort.io',
    'foundit.in',
    'iimjobs.com',
    'wellfound.com',
    'angellist.com',
    'timesjobs.com',
    'monster.com', 'monsterindia.com',
    'efinancialcareers.com',
    # Aggregators that appear frequently in JobSpy / SerpAPI results and are legit
    'talent.com',
    'jobrapido.com',
    'trabajo.org',
    'bebee.com',
    'jobgether.com',
    'hireminthub.com',
    'dayonejobs.com',
    'apna.co',
    # Company career-page patterns
    'careers.',   # careers.adobe.com, careers.google.com …
    '/careers/',  # company.com/careers/…
    'jobs.',      # jobs.apple.com …
    '/jobs/',     # company.com/jobs/…
    'greenhouse.io',
    'lever.co',
    'workday.com',
    'myworkdayjobs.com',
    'smartrecruiters.com',
    'icims.com',
    'taleo.net',
    'brassring.com',
    'successfactors.com',
]

# Substrings that indicate an untrusted aggregator (checked first — higher priority)
# NOTE: talent.com / jobrapido / bebee moved to TRUSTED — they appear in real JobSpy results
BLOCKED = [
    'jooble',
    'neuvoo',
    'adzuna',
    'jora.com',
    'trovit',
    'remotara',
    'gigpro',
    'whatjobs',
    'jobstack',
    'bayt.com',
    'careerjet',
    'ziprecruiter',
    'simplyhired',
    'snagajob',
    'lensa.com',
    'getwork.com',
    'jobsora',
    'mitula',
]


def is_trusted(url: str) -> bool:
    """Return True if the URL is from a trusted platform."""
    lower = url.lower()
    for b in BLOCKED:
        if b in lower:
            _log.warning(f"BLOCKED ({b}): {url[:80]}")
            return False
    for t in TRUSTED:
        if t in lower:
            _log.debug(f"TRUSTED ({t}): {url[:80]}")
            return True
    _log.warning(f"UNKNOWN (rejected): {url[:80]}")
    return False


def best_trusted_link(apply_options: list) -> str | None:
    """
    Given SerpAPI's apply_options list, return the URL of the best trusted option.
    Priority: LinkedIn > Naukri > Indeed > Glassdoor > other trusted > None
    """
    priority = ['linkedin', 'naukri', 'indeed', 'glassdoor', 'shine',
                'instahyre', 'hirist', 'cutshort', 'foundit', 'iimjobs',
                'glassdoor.co.in', 'wellfound', 'greenhouse', 'lever',
                'workday', 'myworkday', 'smartrecruiters', 'icims',
                'careers.', '/careers/', 'jobs.', '/jobs/']

    # First pass — preferred platforms in priority order
    for keyword in priority:
        for opt in apply_options:
            link = opt.get('link', '')
            title = opt.get('title', '').lower()
            if keyword in link.lower() or keyword in title:
                if not any(b in link.lower() for b in BLOCKED):
                    return link

    # Second pass — any trusted link
    for opt in apply_options:
        link = opt.get('link', '')
        if is_trusted(link):
            return link

    return None


def filter_jobs(jobs: list, skip_filter: bool = False) -> list:
    """Remove jobs whose URL is from an untrusted platform.

    Args:
        jobs:        List of job dicts with 'url' or 'apply_link' keys.
        skip_filter: When True, return all jobs unchanged (use for sources
                     like JobSpy/LinkedIn/Indeed that already return direct,
                     trusted URLs — no aggregator noise to filter).
    """
    if skip_filter:
        _log.info(f"FILTER SKIPPED (skip_filter=True) — passing {len(jobs)} jobs through")
        return jobs

    _log.info(f"{'='*60}")
    _log.info(f"FILTERING {len(jobs)} JOBS BY PLATFORM")
    _log.info(f"{'='*60}")

    kept, dropped = [], []
    for job in jobs:
        url = job.get('url') or job.get('apply_link', '')
        if is_trusted(url):
            kept.append(job)
        else:
            dropped.append(job)
            _log.warning(f"REJECTED: {job.get('title','?')[:40]} @ {job.get('company','?')[:30]} — {url[:70]}")

    _log.info(f"TRUSTED: {len(kept)}  |  REJECTED: {len(dropped)}  |  Total in: {len(jobs)}")
    return kept
