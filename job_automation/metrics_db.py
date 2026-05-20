"""
metrics_db.py — SQLite-backed metrics storage for Job Finder AI.

Tables:
  runs        — one row per deep_search() invocation
  job_results — one row per job returned in a run
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "scrutinizer.db"


def init_db() -> None:
    """Create tables if they don't exist; migrate existing tables with new columns."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp                TEXT,
        keyword                  TEXT,
        location                 TEXT,
        resume_hash              TEXT,
        total_jobs               INTEGER,
        window_used              TEXT,
        runtime_seconds          REAL,
        groq_batch_calls         INTEGER,
        groq_premium_calls       INTEGER,
        keyword_only_count       INTEGER,
        json_parse_errors        INTEGER,
        score_min                REAL,
        score_max                REAL,
        score_mean               REAL,
        score_median             REAL,
        jobs_above_60            INTEGER,
        jobs_above_70            INTEGER,
        jobs_above_80            INTEGER,
        by_platform              TEXT,
        role_filter_removed      INTEGER,
        experience_filter_removed INTEGER,
        company_filter_removed   INTEGER,
        location_filter_removed  INTEGER,
        desc_quality_complete    INTEGER,
        desc_quality_sparse      INTEGER,
        desc_quality_missing     INTEGER,
        links_live               INTEGER,
        links_dead               INTEGER,
        links_unchecked          INTEGER
    )""")

    # Migrate: add new columns if they don't exist yet (safe on existing DBs)
    for col, coltype in [
        ("domain_strong",     "INTEGER"),
        ("domain_moderate",   "INTEGER"),
        ("domain_weak",       "INTEGER"),
        ("applyable_count",   "INTEGER"),
        ("remote_count",      "INTEGER"),
        ("wrong_roles_found", "INTEGER"),
    ]:
        try:
            conn.execute(f"ALTER TABLE runs ADD COLUMN {col} {coltype}")
        except Exception:
            pass  # Column already exists

    c.execute("""
    CREATE TABLE IF NOT EXISTS job_results (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id                INTEGER,
        title                 TEXT,
        company               TEXT,
        location              TEXT,
        source                TEXT,
        score                 REAL,
        scored_by             TEXT,
        freshness_label       TEXT,
        description_quality   TEXT,
        description_word_count INTEGER,
        role_mismatch_reason  TEXT,
        url                   TEXT,
        link_status           TEXT,
        FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")

    conn.commit()
    conn.close()


def save_run(run_data: dict, jobs: list) -> int:
    """
    Persist a search run and its jobs.  Returns the run_id (auto-increment).
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    scores = [j.get("score", 0) for j in jobs if j.get("score") is not None]
    sorted_scores = sorted(scores)

    qm = run_data.get("quality_metrics", {})

    c.execute("""
    INSERT INTO runs (
        timestamp, keyword, location, resume_hash,
        total_jobs, window_used, runtime_seconds,
        groq_batch_calls, groq_premium_calls, keyword_only_count,
        json_parse_errors,
        score_min, score_max, score_mean, score_median,
        jobs_above_60, jobs_above_70, jobs_above_80,
        by_platform,
        role_filter_removed, experience_filter_removed,
        company_filter_removed, location_filter_removed,
        desc_quality_complete, desc_quality_sparse, desc_quality_missing,
        links_live, links_dead, links_unchecked,
        domain_strong, domain_moderate, domain_weak,
        applyable_count, remote_count, wrong_roles_found
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        run_data.get("keyword"),
        run_data.get("location"),
        run_data.get("resume_hash"),
        len(jobs),
        run_data.get("window_used"),
        run_data.get("runtime_seconds"),
        run_data.get("groq_batch_calls", 0),
        run_data.get("groq_premium_calls", 0),
        run_data.get("keyword_only_count", 0),
        run_data.get("json_parse_errors", 0),
        min(scores) if scores else 0,
        max(scores) if scores else 0,
        sum(scores) / len(scores) if scores else 0,
        sorted_scores[len(sorted_scores) // 2] if sorted_scores else 0,
        sum(1 for s in scores if s >= 60),
        sum(1 for s in scores if s >= 70),
        sum(1 for s in scores if s >= 80),
        json.dumps(run_data.get("by_platform", {})),
        run_data.get("role_filter_removed", 0),
        run_data.get("experience_filter_removed", 0),
        run_data.get("company_filter_removed", 0),
        run_data.get("location_filter_removed", 0),
        sum(1 for j in jobs if j.get("description_quality") == "complete"),
        sum(1 for j in jobs if j.get("description_quality") in (
            "sparse", "no_requirements_listed")),
        sum(1 for j in jobs if j.get("description_quality") in (
            "missing", "too_short")),
        run_data.get("links_live", 0),
        run_data.get("links_dead", 0),
        len(jobs),   # all unchecked until link check runs
        qm.get("domain_strong", 0),
        qm.get("domain_moderate", 0),
        qm.get("domain_weak", 0),
        qm.get("applyable_count", 0),
        qm.get("remote_count", 0),
        qm.get("wrong_roles", 0),
    ))

    run_id = c.lastrowid

    for job in jobs:
        c.execute("""
        INSERT INTO job_results (
            run_id, title, company, location, source, score,
            scored_by, freshness_label, description_quality,
            description_word_count, role_mismatch_reason, url, link_status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            run_id,
            job.get("title"), job.get("company"), job.get("location"),
            job.get("source"), job.get("score"), job.get("scored_by"),
            job.get("freshness_label"), job.get("description_quality"),
            job.get("description_word_count", 0),
            job.get("role_mismatch_reason", ""),
            job.get("url"),
            job.get("link_status", "unchecked"),
        ))

    conn.commit()
    conn.close()
    return run_id


def get_trend_report(last_n_runs: int = 10) -> list:
    """Return rows from the last N runs for trend analysis."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    SELECT timestamp, keyword, total_jobs, score_mean, score_median,
           jobs_above_60, jobs_above_70, window_used, runtime_seconds,
           keyword_only_count, json_parse_errors,
           COALESCE(domain_strong, 0),
           COALESCE(domain_moderate, 0),
           COALESCE(domain_weak, 0),
           COALESCE(applyable_count, 0),
           COALESCE(remote_count, 0),
           COALESCE(wrong_roles_found, 0)
    FROM runs ORDER BY id DESC LIMIT ?
    """, (last_n_runs,))
    rows = c.fetchall()
    conn.close()
    return rows


def update_link_results(run_id: int, jobs: list) -> None:
    """Back-fill link_status for jobs in a run after link-checking completes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    live  = sum(1 for j in jobs if j.get("link_status") == "live")
    dead  = sum(1 for j in jobs if j.get("link_status") == "dead")
    unchecked = sum(1 for j in jobs if j.get("link_status", "unchecked") == "unchecked")

    c.execute("""
    UPDATE runs SET links_live=?, links_dead=?, links_unchecked=?
    WHERE id=?
    """, (live, dead, unchecked, run_id))

    for job in jobs:
        url    = job.get("url", "")
        status = job.get("link_status", "unchecked")
        if url:
            c.execute("""
            UPDATE job_results SET link_status=?
            WHERE run_id=? AND url=?
            """, (status, run_id, url))

    conn.commit()
    conn.close()
