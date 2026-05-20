#!/usr/bin/env python3
"""
Run daily to verify all scrapers are working.
Usage:   python healthcheck.py
Cron:    0 9 * * * cd /Users/harshgarg/Desktop/job-finder-ai && python healthcheck.py
"""
import sys
sys.path.insert(0, ".")

from job_automation.aggregator import JobAggregator

agg = JobAggregator()
results = {}
FAIL_THRESHOLD = 2  # minimum jobs to consider a platform healthy

for platform, keyword, location in [
    ("linkedin",          "program manager", "Hyderabad"),
    ("indeed",            "product manager", "Hyderabad"),
    ("google_jobs_india", "program manager", "Hyderabad"),
]:
    try:
        # 14-day window for connectivity check; location "Hyderabad" avoids
        # over-filtering that would give false negatives on a pan-India query
        jobs = agg.search(keyword, location, max_per_platform=5,
                          platforms=[platform], hours_old=336,
                          skip_seen_filter=True)
        count = len(jobs)
        status = "OK" if count >= FAIL_THRESHOLD else "LOW"
        results[platform] = {"count": count, "status": status}
    except Exception as e:
        results[platform] = {"count": 0, "status": f"ERROR: {str(e)[:100]}"}

print("\n=== HEALTHCHECK RESULTS ===")
all_ok = True
for platform, result in results.items():
    icon = "OK" if result["status"] == "OK" else ("LOW" if result["status"] == "LOW" else "FAIL")
    label = {"OK": "✅ OK", "LOW": "⚠️ LOW", "FAIL": "❌ ERROR"}.get(icon, "❌")
    print(f"  {label} {platform:<22}: {result['count']} jobs  {result['status'] if icon == 'FAIL' else ''}")
    if icon != "OK":
        all_ok = False

if all_ok:
    print("\n✅ All platforms healthy")
    sys.exit(0)
else:
    print("\n❌ One or more platforms need attention — check scrapers")
    sys.exit(1)
