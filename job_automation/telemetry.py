"""
telemetry.py — Opt-in anonymous aggregate data sharing.

Only sends aggregate patterns — NEVER resume text, URLs, company names,
user location, or any PII.

Opt-in via .env:
    TELEMETRY_OPT_IN=true

What IS sent (when opted in):
  - Profile domain category (tech_management / developer / finance)
  - Score distribution stats (mean, percentiles — no raw scores)
  - Apply rate by score bucket
  - Domain match accuracy
  - Which date window was typically needed

What is NEVER sent:
  - Resume text
  - Job URLs
  - Company names
  - User location
  - Any PII
"""

import os
import json
import requests
from datetime import datetime

TELEMETRY_ENDPOINT  = "https://your-domain.com/api/telemetry"
TELEMETRY_OPT_IN_KEY = "TELEMETRY_OPT_IN"


def is_opted_in() -> bool:
    """Return True only when user has explicitly set TELEMETRY_OPT_IN=true."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return os.getenv(TELEMETRY_OPT_IN_KEY, "false").lower() == "true"


def send_aggregate_signal(insights: dict, profile_domain: str) -> bool:
    """
    POST anonymised aggregate signal to telemetry endpoint if opted in.
    Called weekly or after N feedback points are accumulated.

    Returns True if the payload was sent, False otherwise (including when
    opted out — this is not an error).
    Telemetry failure NEVER propagates — it is always silently swallowed.
    """
    if not is_opted_in():
        return False

    payload = {
        "app_version":  "1.0",
        "timestamp":    datetime.now().isoformat()[:10],  # date only
        "profile_domain": profile_domain,
        "insights": {
            "suggested_threshold":   insights.get("suggested_threshold"),
            "apply_rate_by_score":   insights.get("apply_rate_by_score"),
            "domain_match_accuracy": insights.get("domain_match_accuracy"),
            "total_feedback_points": insights.get("total_feedback_points"),
        },
    }

    try:
        requests.post(TELEMETRY_ENDPOINT, json=payload, timeout=3)
        return True
    except Exception:
        pass  # Telemetry failure must never affect the main app
    return False


def check_for_prompt_updates() -> bool:
    """
    Pull the latest scoring_config.json from GitHub.

    If the remote version number is higher than the local file, download
    and overwrite it.  The next GroqAnalyzer instantiation will pick up the
    new thresholds and domain signals automatically.

    Returns True if an update was applied, False otherwise.
    Replace YOUR_USERNAME with your actual GitHub username before use.
    """
    CONFIG_URL = (
        "https://raw.githubusercontent.com/harshgarg020695-glitch/job-finder-ai"
        "/main/scoring_config.json"
    )
    LOCAL_CONFIG = "scoring_config.json"

    try:
        resp = requests.get(CONFIG_URL, timeout=5)
        if resp.status_code != 200:
            return False

        remote = resp.json()

        local_version = 0
        if os.path.exists(LOCAL_CONFIG):
            with open(LOCAL_CONFIG) as f:
                local_version = json.load(f).get("version", 0)

        if remote.get("version", 0) > local_version:
            with open(LOCAL_CONFIG, "w") as f:
                json.dump(remote, f, indent=2)
            print(f"[Config] Updated scoring config to v{remote['version']}")
            return True

    except Exception:
        pass  # Config update failure must never affect the main app

    return False
