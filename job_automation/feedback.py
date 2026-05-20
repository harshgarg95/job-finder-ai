"""
feedback.py — Local feedback capture and self-learning calibration.

No PII. No network calls. Runs always.

Tables:
  search_runs       — one row per deep_search() call (hashed keyword)
  job_actions       — what user did with each job (applied/skipped/saved)
  score_calibration — aggregate apply-rate snapshots (written by calibrate())
"""

import sqlite3
import hashlib
from datetime import datetime

FEEDBACK_DB = "feedback.db"


def _hash(value: str) -> str:
    """One-way hash — can't recover original value."""
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]


# ── Schema ─────────────────────────────────────────────────────────────────

def init_feedback_db() -> None:
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS search_runs (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp        TEXT,
        keyword_hash     TEXT,
        location         TEXT,
        profile_level    TEXT,
        profile_domain   TEXT,
        total_jobs       INTEGER,
        jobs_above_70    INTEGER,
        domain_strong    INTEGER,
        domain_moderate  INTEGER,
        domain_weak      INTEGER,
        window_used      TEXT,
        runtime_seconds  REAL,
        groq_model       TEXT,
        score_mean       REAL,
        score_p25        REAL,
        score_p75        REAL
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS job_actions (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp         TEXT,
        run_id            INTEGER,
        url_hash          TEXT,
        title_pattern     TEXT,
        company_size_guess TEXT,
        score             REAL,
        domain_match      TEXT,
        source            TEXT,
        days_since_posted INTEGER,
        action            TEXT,
        FOREIGN KEY (run_id) REFERENCES search_runs(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS score_calibration (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp     TEXT,
        profile_domain TEXT,
        score_bucket  TEXT,
        applied_count INTEGER,
        skipped_count INTEGER,
        apply_rate    REAL
    )""")

    conn.commit()
    conn.close()


# ── Write helpers ──────────────────────────────────────────────────────────

def save_search_run(
    keyword: str,
    location: str,
    jobs: list,
    profile: dict,
    runtime: float,
    window: str,
) -> int:
    """
    Persist a search run summary. Returns run_id for linking job actions.
    Keyword is one-way hashed — original cannot be recovered.
    """
    init_feedback_db()
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()

    scores = sorted([float(j.get("score", 0) or 0) for j in jobs])
    n = len(scores)

    c.execute("""
    INSERT INTO search_runs (
        timestamp, keyword_hash, location, profile_level, profile_domain,
        total_jobs, jobs_above_70, domain_strong, domain_moderate, domain_weak,
        window_used, runtime_seconds, groq_model,
        score_mean, score_p25, score_p75
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        _hash(keyword),
        location,
        profile.get("level", "unknown"),
        profile.get("primary_domain", "unknown")[:50],
        n,
        sum(1 for s in scores if s >= 70),
        sum(1 for j in jobs if j.get("domain_match") == "strong"),
        sum(1 for j in jobs if j.get("domain_match") == "moderate"),
        sum(1 for j in jobs if j.get("domain_match") == "weak"),
        window,
        round(runtime, 1),
        "llama-3.1-8b-instant",
        sum(scores) / n if n else 0,
        scores[n // 4]     if n >= 4 else 0,
        scores[3 * n // 4] if n >= 4 else 0,
    ))

    run_id = c.lastrowid
    conn.commit()
    conn.close()
    return run_id


def record_job_action(run_id: int, job: dict, action: str) -> None:
    """
    Record what the user did with a job.

    action: 'applied' | 'skipped' | 'saved' | 'opened_url'

    Call this when:
      - User marks a job in the CSV export (applied / skipped)
      - Frontend hits POST /api/record-action
    """
    init_feedback_db()

    # Anonymised title pattern — keeps role category, drops proper nouns
    title = (job.get("title") or "").lower()
    title_pattern = (
        "director"    if "director"    in title else
        "manager"     if "manager"     in title else
        "consultant"  if "consultant"  in title else
        "engineer"    if "engineer"    in title else
        "analyst"     if "analyst"     in title else
        "architect"   if "architect"   in title else
        "lead"        if "lead"        in title else
        "other"
    )

    posted = job.get("posted", "")
    try:
        days_old = (datetime.now() - datetime.strptime(posted[:10], "%Y-%m-%d")).days
    except Exception:
        days_old = -1

    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO job_actions (
        timestamp, run_id, url_hash, title_pattern,
        score, domain_match, source, days_since_posted, action
    ) VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        run_id,
        _hash(job.get("url", "")),
        title_pattern,
        float(job.get("score", 0) or 0),
        job.get("domain_match", "unknown"),
        job.get("source", "unknown"),
        days_old,
        action,
    ))
    conn.commit()
    conn.close()


# ── Read / analysis ────────────────────────────────────────────────────────

def get_calibration_insights() -> dict:
    """
    Analyse accumulated feedback and return actionable recommendations.

    Returns:
      apply_rate_by_score   — dict: score bucket → {applied, skipped, apply_rate}
      suggested_threshold   — lowest bucket with ≥30% apply rate
      domain_match_accuracy — dict: domain_match value → {apply_rate, total}
      total_feedback_points — int
    """
    init_feedback_db()
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()

    # ── Apply rate by score bucket ─────────────────────────────────────────
    c.execute("""
        SELECT
            CASE
                WHEN score >= 90 THEN '90-100'
                WHEN score >= 80 THEN '80-89'
                WHEN score >= 75 THEN '75-79'
                WHEN score >= 70 THEN '70-74'
                WHEN score >= 65 THEN '65-69'
                ELSE 'below-65'
            END AS bucket,
            SUM(CASE WHEN action = 'applied' THEN 1 ELSE 0 END) AS applied,
            SUM(CASE WHEN action = 'skipped' THEN 1 ELSE 0 END) AS skipped,
            COUNT(*) AS total
        FROM job_actions
        GROUP BY bucket
        ORDER BY bucket DESC
    """)
    apply_rates: dict = {}
    for bucket, applied, skipped, total in c.fetchall():
        if total >= 3:
            apply_rates[bucket] = {
                "applied":    applied,
                "skipped":    skipped,
                "apply_rate": round(applied / total, 2),
            }

    # Recommended threshold — lowest bucket with ≥30% apply rate
    threshold_suggestion = 70  # safe default
    for bucket in sorted(apply_rates.keys(), reverse=True):
        if apply_rates[bucket]["apply_rate"] >= 0.3:
            lo = int(bucket.split("-")[0]) if "-" in bucket else 70
            threshold_suggestion = lo
            break

    # ── Domain match accuracy ─────────────────────────────────────────────
    c.execute("""
        SELECT domain_match,
               SUM(CASE WHEN action = 'applied' THEN 1 ELSE 0 END) AS applied,
               COUNT(*) AS total
        FROM job_actions
        GROUP BY domain_match
    """)
    domain_accuracy: dict = {}
    for domain, applied, total in c.fetchall():
        if total >= 3:
            domain_accuracy[domain] = {
                "apply_rate": round(applied / total, 2),
                "total":      total,
            }

    # ── Total data points ─────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM job_actions")
    total_points = c.fetchone()[0]

    conn.close()

    return {
        "apply_rate_by_score":   apply_rates,
        "suggested_threshold":   threshold_suggestion,
        "domain_match_accuracy": domain_accuracy,
        "total_feedback_points": total_points,
    }


def get_run_history(last_n: int = 10) -> list:
    """Return the last N search_runs rows (newest first)."""
    init_feedback_db()
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, location, profile_level, profile_domain,
               total_jobs, jobs_above_70, window_used, runtime_seconds, score_mean
        FROM search_runs
        ORDER BY id DESC
        LIMIT ?
    """, (last_n,))
    rows = c.fetchall()
    conn.close()
    return rows
