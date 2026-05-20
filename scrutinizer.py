#!/usr/bin/env python3
"""
Job Finder AI — Scrutinizer
============================
Comprehensive health check, quality evaluation, and statistical report.

Usage:
  python scrutinizer.py                    # Full evaluation (includes link check)
  python scrutinizer.py --quick            # Skip link checking (faster)
  python scrutinizer.py --report-only      # Show historical stats only
  python scrutinizer.py --scenario remote  # Test remote-work scenario
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime

import requests

sys.path.insert(0, ".")


# ── Scenario definitions ───────────────────────────────────────────────────

SCENARIOS: dict[str, dict] = {
    "standard": {
        "keyword":  "AI Implementation Manager",
        "location": "Hyderabad",
        "note":     "Default search — Harsh's primary keyword + city",
    },
    "remote": {
        "keyword":  "AI Implementation Manager",
        "location": "Remote India",
        "note":     "Remote-work variant",
    },
    "developer": {
        "keyword":         "Python Developer",
        "location":        "Bangalore",
        "resume_override": (
            "Python developer, 4 years experience, Django, FastAPI, REST APIs, "
            "AWS, Docker, PostgreSQL, Redis, microservices"
        ),
        "note": "Developer profile — tests domain-switch detection",
    },
    "junior": {
        "keyword":         "Product Manager",
        "location":        "Hyderabad",
        "resume_override": (
            "Junior product manager, 1 year experience, MBA, product roadmap, "
            "user research, Jira, Figma, A/B testing"
        ),
        "note": "Junior profile — tests level calibration",
    },
    "bangalore": {
        "keyword":  "AI Implementation Manager",
        "location": "Bangalore",
        "note":     "Different city variant",
    },
}


# ══════════════════════════════════════════════════════════════════════════════

class JobFinderScrutinizer:
    """Runs all checks and prints a final summary report."""

    def __init__(self, quick: bool = False):
        self.quick      = quick
        self.results:   dict = {}
        self.start_time = time.time()
        self._run_id:   int | None = None

    # ── Orchestrator ──────────────────────────────────────────────────────

    def run_full_evaluation(self, scenario: str = "standard") -> None:
        print(f"\n{'='*65}")
        print(f"  JOB FINDER AI — SCRUTINIZER v1.0")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Scenario: {scenario}")
        print(f"{'='*65}\n")

        self._check_1_backend_health()
        self._check_2_api_quotas()
        self._check_3_scraper_health()
        self._check_4_run_test_search(scenario)
        self._check_5_output_quality()
        if not self.quick:
            self._check_6_link_validity()
        self._check_7_save_to_db()
        self._print_final_report()

    # ── Check 1: module imports + resume cache ─────────────────────────────

    def _check_1_backend_health(self) -> None:
        print("━━━ CHECK 1: Backend Health ━━━")
        checks: dict[str, str] = {}

        # Flask server
        try:
            r = requests.get("http://localhost:8000/", timeout=3)
            checks["flask_server"] = f"✅ Running (HTTP {r.status_code})"
        except Exception:
            checks["flask_server"] = "⚠️  Not running — start with: python api.py"

        # Key module imports (hybrid_scorer is at root, not in job_automation)
        for module in [
            "job_automation.aggregator",
            "hybrid_scorer",
            "groq_analyzer",
            "job_automation.naukri_scraper",
        ]:
            try:
                __import__(module)
                checks[module] = "✅ OK"
            except Exception as e:
                checks[module] = f"❌ Import error: {str(e)[:70]}"

        # Resume cache
        if os.path.exists("resume_cache.txt"):
            size = os.path.getsize("resume_cache.txt")
            checks["resume_cache.txt"] = f"✅ {size:,} chars"
        else:
            checks["resume_cache.txt"] = "❌ Missing — resume scoring will be limited"

        # Candidate profile extraction
        if os.path.exists("resume_cache.txt"):
            try:
                import time as _time
                _time.sleep(2)   # ensure ≥2s gap after any prior Groq call
                from groq_analyzer import GroqAnalyzer
                resume_text = open("resume_cache.txt").read()
                analyzer = GroqAnalyzer()
                profile = analyzer.extract_candidate_profile(resume_text)
                print(f"  Candidate profile detected:")
                print(f"    Title:    {profile.get('title', '?')}")
                print(f"    Level:    {profile.get('level', '?')} | "
                      f"{profile.get('years_experience', '?')} years")
                print(f"    Domain:   {profile.get('primary_domain', '?')[:70]}")
                print(f"    Strong signals: {profile.get('strong_match_if_jd_contains', [])[:3]}")
                print(f"    Weak signals:   {profile.get('weak_match_if_jd_contains', [])[:3]}")
                self.results['candidate_profile'] = profile
            except Exception as e:
                print(f"  Profile extraction: ❌ {str(e)[:60]}")

        # seen_jobs.json
        if os.path.exists("seen_jobs.json"):
            try:
                with open("seen_jobs.json") as f:
                    seen = json.load(f)
                checks["seen_jobs.json"] = f"ℹ️  {len(seen)} jobs remembered"
            except Exception:
                checks["seen_jobs.json"] = "⚠️  Exists but unreadable"
        else:
            checks["seen_jobs.json"] = "ℹ️  Not yet created (first run)"

        for k, v in checks.items():
            print(f"  {k:<35} {v}")

        self.results["backend_health"] = checks
        print()

    # ── Check 2: API key status ────────────────────────────────────────────

    def _check_2_api_quotas(self) -> None:
        print("━━━ CHECK 2: API Quotas ━━━")
        from dotenv import load_dotenv
        load_dotenv()

        # Groq — use GroqKeyManager so we see all keys
        try:
            from job_automation.groq_key_manager import GroqKeyManager
            mgr = GroqKeyManager()
            print(f"  Groq keys loaded: {len(mgr.keys)}")
            for label, status in mgr.get_status().items():
                icon = "✅" if "OK" in status else "❌"
                print(f"    {icon} {label}: {status}")
        except Exception as e:
            print(f"  Groq key manager: ❌ {e}")

        # Live Groq call
        try:
            from groq_analyzer import GroqAnalyzer
            ga = GroqAnalyzer()
            quota = ga.check_quota()
            remaining = quota.get("remaining_requests", "?")
            active    = quota.get("active_key", "?")
            if quota.get("status") == "ok":
                print(f"  Groq live call:   ✅ {remaining} requests remaining "
                      f"(active key {active})")
            else:
                print(f"  Groq live call:   ❌ {quota.get('message','?')[:80]}")
        except Exception as e:
            print(f"  Groq live call:   ❌ {e}")

        # SerpAPI / Serper
        for name, env_var in [("SerpAPI", "SERPAPI_KEY"), ("Serper", "SERPER_API_KEY")]:
            key = os.getenv(env_var, "")
            if key:
                print(f"  {name:<10} ✅ Key present ({key[:6]}…)")
            else:
                print(f"  {name:<10} ⚠️  No key — Naukri results will be limited")

        print()

    # ── Check 3: scraper smoke-test ────────────────────────────────────────

    def _check_3_scraper_health(self) -> None:
        print("━━━ CHECK 3: Scraper Health ━━━")
        from job_automation.aggregator import JobAggregator
        agg = JobAggregator()

        test_results: dict[str, str] = {}
        for platform in ["linkedin", "indeed", "naukri"]:
            t = time.time()
            try:
                jobs = agg.search(
                    "program manager", "India",
                    max_per_platform=3,
                    platforms=[platform],
                    skip_seen_filter=True,
                )
                elapsed = time.time() - t
                icon    = "✅" if jobs else "⚠️ "
                status  = f"{icon} {len(jobs)} jobs in {elapsed:.1f}s"
            except Exception as e:
                status = f"❌ {str(e)[:70]}"
            test_results[platform] = status
            print(f"  {platform:<20} {status}")

        self.results["scraper_health"] = test_results
        print()

    # ── Check 4: full deep_search ──────────────────────────────────────────

    def _check_4_run_test_search(self, scenario: str = "standard") -> None:
        print(f"━━━ CHECK 4: Test Search ({scenario}) ━━━")

        s = SCENARIOS.get(scenario, SCENARIOS["standard"])
        print(f"  {s['note']}")

        resume_text: str = s.get("resume_override", "")
        _using_override = bool(resume_text)
        if not resume_text:
            try:
                resume_text = open("resume_cache.txt").read()
            except FileNotFoundError:
                resume_text = (
                    "Senior AI Implementation Manager, digital transformation, "
                    "consulting, LangChain, Python, stakeholder management"
                )

        # If scenario uses a resume_override, re-extract profile from that text
        # so 5C role-quality check uses the correct domain for this scenario
        if _using_override:
            try:
                from groq_analyzer import GroqAnalyzer as _GA
                _p = _GA().extract_candidate_profile(resume_text)
                self.results["candidate_profile"] = _p
                print(f"  Profile (override): {_p.get('title','?')} | {_p.get('level','?')} | domain_key={_p.get('primary_domain','?')}")
            except Exception as _pe:
                print(f"  Profile (override): extraction failed — {_pe}")

        from job_automation.aggregator import JobAggregator

        t   = time.time()
        agg = JobAggregator()
        try:
            jobs    = agg.deep_search(
                keyword=s["keyword"],
                location=s["location"],
                resume_text=resume_text,
            )
            elapsed = time.time() - t
            meta    = agg._last_run_meta

            self.results["test_jobs"]     = jobs
            self.results["test_metadata"] = {
                "keyword":         s["keyword"],
                "location":        s["location"],
                "scenario":        scenario,
                "runtime_seconds": elapsed,
                "resume_hash":     hashlib.md5(resume_text.encode()).hexdigest()[:8],
                "window_used":     meta.get("window_used", ""),
                "by_platform":     meta.get("by_platform", {}),
                "keyword_only_count": sum(
                    1 for j in jobs if j.get("scored_by") == "keyword_only"
                ),
            }
            print(f"  ✅ {len(jobs)} jobs in {elapsed / 60:.1f} min "
                  f"| window: {meta.get('window_used','?')} "
                  f"| platform: {meta.get('by_platform',{})}")
        except Exception as e:
            import traceback
            print(f"  ❌ Search failed: {e}")
            traceback.print_exc()
            self.results["test_jobs"]     = []
            self.results["test_metadata"] = {}

        print()

    # ── Check 5: output quality analysis ──────────────────────────────────

    def _check_5_output_quality(self) -> None:
        print("━━━ CHECK 5: Output Quality (Full Analysis) ━━━")
        jobs = self.results.get("test_jobs", [])

        if not jobs:
            print("  ⚠️  No jobs to evaluate\n")
            return

        scores        = [float(j.get("score", 0) or 0) for j in jobs]
        sources       = Counter(j.get("source") for j in jobs)
        scored_by     = Counter(j.get("scored_by", "").split("+")[0] for j in jobs)
        desc_quality  = Counter(j.get("description_quality") for j in jobs)
        domain_matches = Counter(j.get("domain_match", "unknown") for j in jobs)
        loc_types     = Counter((j.get("location_type") or "On-site") for j in jobs)
        salary_fits   = Counter(j.get("salary_fit", "unknown") for j in jobs)
        freshness     = Counter(j.get("freshness_label", "Unknown") for j in jobs)
        total         = len(jobs)

        # ── 5A: Score Distribution ──────────────────────────────────────────
        print(f"\n  [5A] SCORE DISTRIBUTION")
        print(f"    Total jobs:     {total}")
        print(f"    Score range:    {min(scores):.0f}% – {max(scores):.0f}%")
        print(f"    Mean score:     {sum(scores)/total:.1f}%")
        print(f"    Jobs ≥ 70%:     {sum(1 for s in scores if s >= 70)}")
        print(f"    Jobs ≥ 80%:     {sum(1 for s in scores if s >= 80)}")
        print(f"    By platform:    {dict(sources)}")

        # ── 5B: Domain Match Analysis ───────────────────────────────────────
        print(f"\n  [5B] DOMAIN MATCH ANALYSIS")
        for match_type in ["strong", "moderate", "weak", "unknown"]:
            count = domain_matches.get(match_type, 0)
            pct   = 100 * count / max(total, 1)
            icon  = {"strong": "✅", "moderate": "🟡",
                     "weak": "❌", "unknown": "⚠️"}.get(match_type, "—")
            print(f"    {icon} {match_type:<10}: {count:>3} ({pct:.0f}%)")

        weak_pct    = 100 * domain_matches.get("weak", 0) / max(total, 1)
        unknown_pct = 100 * domain_matches.get("unknown", 0) / max(total, 1)
        if weak_pct > 15:
            print(f"    ⚠️  {weak_pct:.0f}% weak-domain jobs — scoring prompt may need calibration")
        if unknown_pct > 30:
            print(f"    ⚠️  {unknown_pct:.0f}% unknown domain — job descriptions may be too short")

        # ── 5C: Role Quality Check ──────────────────────────────────────────
        print(f"\n  [5C] ROLE QUALITY CHECK")
        # Load excluded_title_keywords from scoring_config for the detected domain
        # so the check is profile-aware (developer != tech_management wrong roles)
        _FALLBACK_WRONG_ROLE_SIGNALS = [
            "software engineer", "backend engineer", "frontend engineer",
            "sde ", "sde-", "developer", "programmer", "lead engineer",
            "forward deployed engineer", "solutions engineer",
            "bi analyst", "business intelligence analyst",
            "data analyst", "data scientist", "ml engineer",
            " l1", " l2", " l3", "trainee", "associate engineer",
            "qa engineer", "test engineer", "devops", "sre ",
        ]
        try:
            import json as _json
            _sconfig = _json.load(open("scoring_config.json")) if os.path.exists("scoring_config.json") else {}
            _profile_domain = (self.results.get("candidate_profile") or {}).get("primary_domain", "tech_management")
            _domain_cfg = _sconfig.get("domain_configs", {}).get(_profile_domain, {})
            WRONG_ROLE_SIGNALS = _domain_cfg.get("excluded_title_keywords") or _FALLBACK_WRONG_ROLE_SIGNALS
            if _domain_cfg.get("excluded_title_keywords"):
                print(f"    ℹ️  Role filter: using scoring_config excluded_title_keywords for domain '{_profile_domain}'")
            else:
                print(f"    ℹ️  Role filter: using default signals (domain '{_profile_domain}' not in scoring_config)")
        except Exception as _rqe:
            WRONG_ROLE_SIGNALS = _FALLBACK_WRONG_ROLE_SIGNALS
            print(f"    ℹ️  Role filter: using default signals (config load failed: {_rqe})")
        # A job is "wrong role" only if title matches the exclusion list
        # AND Groq did NOT rate it as a strong domain match.
        # This prevents false positives when profile domain mis-detects (e.g.
        # short resume_override text) — Groq scoring is the ground truth.
        wrong_roles      = [j for j in jobs if (
            any(s in j.get("title", "").lower() for s in WRONG_ROLE_SIGNALS)
            and j.get("domain_match") != "strong"
        )]
        weak_domain_jobs = [j for j in jobs if j.get("domain_match") == "weak"]
        penalised        = [j for j in jobs if j.get("role_mismatch_reason")]

        if wrong_roles:
            print(f"    ❌ {len(wrong_roles)} wrong-role titles found:")
            for j in wrong_roles:
                print(f"       {j.get('title','')[:45]} @ "
                      f"{j.get('company','')[:20]} "
                      f"({j.get('score','?')}%, domain: {j.get('domain_match','?')})")
        else:
            print(f"    ✅ Zero excluded-role titles in results")

        if weak_domain_jobs:
            print(f"    ⚠️  {len(weak_domain_jobs)} weak-domain jobs passed 70% gate:")
            for j in weak_domain_jobs:
                print(f"       {j.get('score','?')}% | {j.get('title','')[:40]} "
                      f"— {j.get('score_reason','')[:50]}")
        else:
            print(f"    ✅ No weak-domain jobs in results")

        print(f"    Role penalty applied: {len(penalised)} jobs capped")

        # ── 5D: Description Quality ─────────────────────────────────────────
        print(f"\n  [5D] DESCRIPTION QUALITY")
        for quality in ["complete", "sparse", "no_requirements_listed",
                        "too_short", "missing"]:
            count = desc_quality.get(quality, 0)
            if count > 0:
                icon = "✅" if quality == "complete" else "⚠️"
                print(f"    {icon} {quality}: {count}")

        incomplete = [j for j in jobs if j.get("description_quality") in
                      ("no_requirements_listed", "too_short", "missing")]
        if incomplete:
            print(f"\n    Jobs with unreliable scores (no requirements in JD):")
            for j in incomplete:
                print(f"       {j.get('score','?')}% | {j.get('title','')[:40]} "
                      f"@ {j.get('company','')[:20]} "
                      f"— {j.get('description_quality_note','')[:60]}")

        # ── 5E: Scoring Method ──────────────────────────────────────────────
        print(f"\n  [5E] SCORING METHOD")
        for method, count in scored_by.most_common():
            pct  = 100 * count / max(total, 1)
            icon = "✅" if "groq" in str(method) else "⚠️"
            print(f"    {icon} {method}: {count} ({pct:.0f}%)")

        kw_pct = 100 * scored_by.get("keyword_only", 0) / max(total, 1)
        if kw_pct > 20:
            print(f"    ⚠️  High keyword-only rate — Groq quota may be low")

        # ── 5F: Location Breakdown ──────────────────────────────────────────
        print(f"\n  [5F] LOCATION BREAKDOWN")
        for loc_type, count in sorted(loc_types.items(), key=lambda x: -x[1]):
            icon = "🏢" if "On-site" in str(loc_type) else "🌐"
            print(f"    {icon} {loc_type}: {count}")

        remote_count = sum(v for k, v in loc_types.items()
                           if any(t in str(k) for t in
                                  ["Remote", "Hybrid", "Flexible", "Pan"]))
        print(f"    Remote/Flexible total: {remote_count} / {total} jobs")

        # ── 5G: Salary Analysis ─────────────────────────────────────────────
        print(f"\n  [5G] SALARY ANALYSIS")
        salary_stated = [j for j in jobs
                         if j.get("salary_label") and
                         j.get("salary_label") != "Not stated"]
        print(f"    Salary stated: {len(salary_stated)} / {total}")
        print(f"    Not stated:    {total - len(salary_stated)} "
              f"(normal for Indian market)")
        for fit_type, count in salary_fits.most_common():
            icon = ("✅" if fit_type == "in_target_range" else
                    "⚠️" if fit_type == "unknown" else "❌")
            print(f"    {icon} {fit_type}: {count}")
        if salary_stated:
            print(f"    Stated salaries:")
            for j in salary_stated:
                print(f"       {j.get('salary_label')} | "
                      f"{j.get('title','')[:35]} @ {j.get('company','')[:20]}")

        # ── 5H: Job Freshness ───────────────────────────────────────────────
        print(f"\n  [5H] JOB FRESHNESS")
        for label, count in sorted(freshness.items(), key=lambda x: -x[1]):
            age_icon = ("🔥" if any(t in str(label).lower()
                                    for t in ("today", "yesterday"))
                        else "✅" if "day" in str(label).lower() else "⚠️")
            print(f"    {age_icon} {label}: {count}")

        stale = [j for j in jobs
                 if any(f"{n} days" in j.get("freshness_label", "")
                        for n in range(8, 30))]
        if stale:
            print(f"    ⚠️  {len(stale)} jobs older than 7 days — "
                  f"stale date filter may need check")

        # ── 5I: Top 15 Detailed ─────────────────────────────────────────────
        print(f"\n  [5I] TOP 15 JOBS — DETAILED")
        top15 = sorted(jobs, key=lambda j: float(j.get("score", 0) or 0),
                       reverse=True)[:15]

        print(f"  {'#':<3} {'Score':<7} {'Domain':<10} {'Title':<40} "
              f"{'Company':<20} {'Type':<20} {'Freshness'}")
        print(f"  {'-'*120}")
        for i, j in enumerate(top15, 1):
            print(f"  {i:<3} {str(j.get('score','?')):<7} "
                  f"{j.get('domain_match','?')[:9]:<10} "
                  f"{j.get('title','')[:39]:<40} "
                  f"{j.get('company','')[:19]:<20} "
                  f"{j.get('location_type','On-site')[:19]:<20} "
                  f"{j.get('freshness_label','?')}")

            reason = j.get("score_reason", "")
            if reason:
                print(f"      ↳ {reason[:100]}")

            flags = []
            if j.get("domain_match") == "weak":
                flags.append("⚠️ Weak domain")
            if j.get("role_mismatch_reason"):
                flags.append(f"⚠️ {j['role_mismatch_reason'][:40]}")
            if j.get("description_quality") in ("no_requirements_listed",
                                                 "too_short", "missing"):
                flags.append(f"⚠️ Score unreliable: {j.get('description_quality')}")
            if j.get("salary_fit") == "too_low":
                flags.append("❌ Salary below threshold")
            if flags:
                print(f"      ⚑ {' | '.join(flags)}")

        # ── 5J: Applyable Jobs Summary ──────────────────────────────────────
        print(f"\n  [5J] APPLYABLE JOBS (≥70%, strong or moderate domain)")
        applyable = [j for j in jobs
                     if float(j.get("score", 0) or 0) >= 70
                     and j.get("domain_match") in ("strong", "moderate", "unknown")]

        print(f"  Count: {len(applyable)}")
        for i, j in enumerate(sorted(applyable,
                                      key=lambda x: float(x.get("score", 0) or 0),
                                      reverse=True), 1):
            link_status = j.get("link_status", "unchecked")
            apply_icon  = ("✅ APPLY" if link_status == "live" else
                           "⚠️ CHECK" if "login" in str(link_status) else
                           "→ APPLY")
            print(f"  {i}. {apply_icon} ({j.get('score')}%) "
                  f"{j.get('title','')[:40]} @ {j.get('company','')[:20]}")
            print(f"       {j.get('location_type','On-site')[:25]} | "
                  f"{j.get('salary_label','Salary unknown')[:20]} | "
                  f"{j.get('freshness_label','Date unknown')}")
            print(f"       {j.get('url','')[:80]}")

        # ── Store metrics for DB + final report ─────────────────────────────
        self.results["quality_metrics"] = {
            "total":             total,
            "score_mean":        sum(scores) / total if scores else 0,
            "above_70":          sum(1 for s in scores if s >= 70),
            "above_80":          sum(1 for s in scores if s >= 80),
            "wrong_roles":       len(wrong_roles),
            "weak_domain":       len(weak_domain_jobs),
            "keyword_only_pct":  kw_pct,
            "incomplete_desc":   len(incomplete),
            "applyable_count":   len(applyable),
            "remote_count":      remote_count,
            "domain_strong":     domain_matches.get("strong", 0),
            "domain_moderate":   domain_matches.get("moderate", 0),
            "domain_weak":       domain_matches.get("weak", 0),
        }
        print()

    # ── Check 6: link validity ─────────────────────────────────────────────

    def _check_6_link_validity(self) -> None:
        print("━━━ CHECK 6: Link Validity ━━━")
        jobs = self.results.get("test_jobs", [])

        if not jobs:
            print("  ⚠️  No jobs to check\n")
            return

        print(f"  Checking {len(jobs)} URLs in parallel (max_workers=8)…")
        from job_automation.link_checker import check_urls_parallel
        jobs = check_urls_parallel(jobs, max_workers=8)

        status_counts = Counter(j.get("link_status") for j in jobs)
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            pct  = 100 * count / len(jobs)
            icon = "✅" if status == "live" else (
                   "⚠️ " if "login" in status or status == "timeout" else "❌")
            print(f"  {icon} {status:<20} {count:>3} ({pct:.0f}%)")

        self.results["test_jobs"]     = jobs
        self.results["link_validity"] = dict(status_counts)
        print()

    # ── Check 7: persist to SQLite ─────────────────────────────────────────

    def _check_7_save_to_db(self) -> None:
        print("━━━ CHECK 7: Saving to Database ━━━")
        from job_automation.metrics_db import save_run, update_link_results

        try:
            run_data = {
                **self.results.get("test_metadata", {}),
                "quality_metrics": self.results.get("quality_metrics", {}),
            }
            run_id = save_run(
                run_data,
                self.results.get("test_jobs", []),
            )
            self._run_id = run_id

            # If link check ran, back-fill the result
            if not self.quick and self.results.get("link_validity"):
                update_link_results(run_id, self.results.get("test_jobs", []))
                print(f"  ✅ Saved as run #{run_id} in scrutinizer.db "
                      f"(with link results)")
            else:
                print(f"  ✅ Saved as run #{run_id} in scrutinizer.db")
        except Exception as e:
            import traceback
            print(f"  ❌ DB save failed: {e}")
            traceback.print_exc()
        print()

    # ── Final summary report ───────────────────────────────────────────────

    def _print_final_report(self) -> None:
        elapsed   = time.time() - self.start_time
        qm        = self.results.get("quality_metrics", {})
        profile   = self.results.get("candidate_profile", {})
        link_data = self.results.get("link_validity", {})
        run_id    = self._run_id

        # ── Build issues list ──────────────────────────────────────────────
        issues: list[str] = []
        if qm.get("wrong_roles", 0) > 0:
            issues.append(f"❌ {qm['wrong_roles']} wrong-role titles in results")
        if qm.get("weak_domain", 0) > 0:
            issues.append(f"⚠️  {qm['weak_domain']} weak-domain jobs above threshold")
        if qm.get("keyword_only_pct", 0) > 20:
            issues.append(f"⚠️  {qm['keyword_only_pct']:.0f}% keyword-only "
                          f"(Groq quota low)")
        if qm.get("score_mean", 0) < 65:
            issues.append(f"⚠️  Low mean score {qm['score_mean']:.0f}% — "
                          f"check scoring prompt")
        if qm.get("incomplete_desc", 0) > 5:
            issues.append(f"⚠️  {qm['incomplete_desc']} jobs with no JD requirements")

        total_checked = sum(link_data.values()) if link_data else 0
        dead_count    = link_data.get("dead", 0)
        if total_checked > 0 and dead_count / total_checked > 0.15:
            issues.append(f"⚠️  {100*dead_count//total_checked}% dead links")

        print(f"\n{'='*65}")
        print(f"  SCRUTINIZER REPORT  —  {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*65}")

        if issues:
            print("\n  ISSUES FOUND:")
            for issue in issues:
                print(f"    {issue}")
        else:
            print("\n  ✅ ALL QUALITY CHECKS PASSED")

        # ── Candidate profile used ─────────────────────────────────────────
        if profile:
            print(f"\n  CANDIDATE PROFILE USED:")
            print(f"    {profile.get('title', '?')} | "
                  f"{profile.get('level', '?')} | "
                  f"{profile.get('years_experience', '?')} yrs")

        # ── Summary ────────────────────────────────────────────────────────
        print(f"\n  SUMMARY:")
        print(f"    Jobs returned:      {qm.get('total', 0)}")
        print(f"    Applyable (≥70%):   {qm.get('applyable_count', 0)}")
        print(f"    Mean score:         {qm.get('score_mean', 0):.1f}%")
        print(f"    Domain — strong: {qm.get('domain_strong', 0)} | "
              f"moderate: {qm.get('domain_moderate', 0)} | "
              f"weak: {qm.get('domain_weak', 0)}")
        print(f"    Remote/Flexible:    {qm.get('remote_count', 0)} jobs")
        print(f"    Wrong roles:        {qm.get('wrong_roles', 0)}")

        if not self.quick and link_data:
            total = max(qm.get("total", 1), 1)
            print(f"    Links live:         {link_data.get('live', 0)} "
                  f"({100*link_data.get('live',0)//total}%)")
            print(f"    Links dead:         {dead_count} "
                  f"({100*dead_count//total}%)")

        print(f"    Runtime:            {elapsed/60:.1f} minutes")
        if run_id:
            print(f"    Results saved:      scrutinizer.db run #{run_id}")

        print(f"\n  View historical trends:")
        print(f"    python scrutinizer.py --report-only")
        print(f"{'='*65}\n")


# ══════════════════════════════════════════════════════════════════════════════

def print_historical_report() -> None:
    """Pretty-print trend table from the last 10 runs."""
    from job_automation.metrics_db import get_trend_report
    rows = get_trend_report(10)

    if not rows:
        print("\nNo runs recorded yet. Run: python scrutinizer.py --quick\n")
        return

    print(f"\n{'='*130}")
    print(f"  HISTORICAL TREND REPORT (last {len(rows)} runs)")
    print(f"{'='*130}")
    header = (
        f"{'Timestamp':<20} {'Keyword':<26} {'Jobs':>4}  "
        f"{'Mean%':>5}  {'>70':>3}  {'Apply':>5}  "
        f"{'Str':>3} {'Mod':>3} {'Wk':>3}  "
        f"{'Window':<12} {'Min(m)':>6}  {'KW%':>4}"
    )
    print(header)
    print("─" * 130)

    for row in rows:
        (ts, kw, total, mean, median, above60, above70, window,
         runtime, kw_only, errors,
         d_strong, d_mod, d_weak,
         applyable, remote, wrong_roles) = row

        kw_pct   = 100 * (kw_only or 0) / max(total or 1, 1)
        kw_flag  = " ⚠️" if kw_pct > 20 else ""
        wr_flag  = " ❌" if (wrong_roles or 0) > 0 else ""
        print(
            f"{ts[:19]:<20} {kw[:25]:<26} {total:>4}  "
            f"{mean:>5.1f}  {above70:>3}  {(applyable or 0):>5}  "
            f"{(d_strong or 0):>3} {(d_mod or 0):>3} {(d_weak or 0):>3}  "
            f"{window[:11]:<12} {(runtime or 0)/60:>6.1f}  "
            f"{kw_pct:>3.0f}%{kw_flag}{wr_flag}"
        )
    print(
        f"\n  Columns: Jobs=total returned | Apply=≥70% applyable | "
        f"Str/Mod/Wk=domain strong/moderate/weak | KW%=keyword-only scored"
    )
    print()


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Job Finder AI — Scrutinizer"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Skip link checking (faster run)",
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="Print historical trend table and exit",
    )
    parser.add_argument(
        "--scenario", default="standard",
        choices=list(SCENARIOS.keys()),
        help="Test scenario to run",
    )
    args = parser.parse_args()

    if args.report_only:
        print_historical_report()
    else:
        scrutinizer = JobFinderScrutinizer(quick=args.quick)
        scrutinizer.run_full_evaluation(scenario=args.scenario)
