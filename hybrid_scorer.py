"""
Updated hybrid_scorer.py with AUTOMATIC career switch detection

KEY CHANGE: No more manual toggle!
The scorer now AUTOMATICALLY adjusts weights based on domain analysis:
- Same domain → 50/50 balance
- Different domain + High transferability → 60/40 (favor keywords slightly)
- Different domain + Medium transferability → 70/30 (clear career switch)
- Different domain + Low transferability → 80/20 (major pivot)
"""

from keyword_matcher import KeywordMatcher
from groq_analyzer import GroqAnalyzer

# ── Profile detection ──────────────────────────────────────────────────────

def detect_profile_type(resume_text: str) -> dict:
    """
    Detect career level and domain from resume text.
    Returns dict with 'level' (senior/mid/junior) and 'domain'.
    Called once per search session and cached on HybridScorer.
    """
    resume_lower = resume_text.lower()

    SENIOR_SIGNALS = ['vp ', 'vice president', 'director', 'head of',
                      'senior manager', 'principal', 'chief', 'cto', 'coo']
    MID_SIGNALS    = ['manager', 'lead', 'senior', 'consultant', 'advisor',
                      'architect', 'specialist', 'analyst']
    # JUNIOR_SIGNALS only used as fallback (absence of senior/mid)

    if any(s in resume_lower for s in SENIOR_SIGNALS):
        level = 'senior'
    elif any(s in resume_lower for s in MID_SIGNALS):
        level = 'mid'
    else:
        level = 'junior'

    # Tech-management titles take priority — a manager who codes is still a manager
    TECH_MGMT_STRONG = [
        'implementation manager', 'program manager', 'project manager',
        'delivery manager', 'product manager', 'transformation manager',
        'engagement manager', 'ai manager', 'scrum master', 'consulting',
        'it manager', 'tech manager', 'technology manager',
    ]
    DEVELOPER  = ['software engineer', 'developer', 'coding', 'backend',
                  'frontend', 'full stack', 'devops', 'swe', 'sde']
    DATA_ML    = ['data scientist', 'machine learning', 'deep learning', 'nlp',
                  'computer vision', 'analytics', 'data engineer']
    FINANCE    = ['investment', 'banking', 'portfolio', 'equities',
                  'underwriting', 'credit', 'treasury']
    SALES      = ['sales manager', 'account executive', 'business development',
                  'revenue', 'quota', 'pipeline']

    if any(s in resume_lower for s in TECH_MGMT_STRONG):
        domain = 'tech_management'   # manager who codes → still tech_management
    elif any(s in resume_lower for s in DEVELOPER):
        domain = 'developer'
    elif any(s in resume_lower for s in DATA_ML):
        domain = 'data_ml'
    elif any(s in resume_lower for s in FINANCE):
        domain = 'finance'
    elif any(s in resume_lower for s in SALES):
        domain = 'sales'
    else:
        domain = 'tech_management'   # AI/Implementation/PM/consulting roles

    return {'level': level, 'domain': domain}


# ── Role mismatch filter ───────────────────────────────────────────────────

_IC_LEAD_PATTERNS = [
    'technical lead', 'tech lead',
    r'lead\s+(engineer|developer|architect|analyst|sde|swe|qa)',
]
_MGMT_LEAD_PATTERNS = [
    'delivery lead', 'program lead', 'implementation lead',
    'engagement lead', 'transformation lead', 'project lead',
    'team lead', 'practice lead', 'portfolio lead',
]


def is_technical_lead_role(title_lower: str) -> bool:
    """
    True when title is an IC technical lead (penalise for manager resumes).
    False when it is a management/delivery lead (keep).
    """
    import re
    if any(p in title_lower for p in _MGMT_LEAD_PATTERNS):
        return False
    return any(re.search(p, title_lower) for p in _IC_LEAD_PATTERNS)


def role_mismatch_penalty(
    job_title: str,
    resume_text: str,
    raw_score: float,
    profile: dict | None = None,
) -> tuple[float, str]:
    """
    Cap score at 35 when the job function conflicts with the detected
    career profile.  profile is pre-computed and passed in to avoid
    re-detecting on every job.
    """
    if profile is None:
        profile = detect_profile_type(resume_text)

    job_lower = job_title.lower()

    if profile['domain'] == 'developer':
        # Developer resume → penalise non-tech management roles
        WRONG_ROLES: list[str] = [
            'area sales manager', 'underwriting', 'loan officer',
        ]
    elif profile['domain'] == 'tech_management':
        # Manager/consultant/PM resume → penalise IC, junior, and unrelated roles
        WRONG_ROLES = [
            'developer', 'software engineer', ' l1', ' l2', ' l3',
            'programmer', 'designer', 'ops engineer', 'sre ',
            'data scientist', 'ml engineer', 'fresher', 'trainee',
            'specialist i ', 'specialist ii ',
            # abbreviated / shorthand IC dev titles
            'software dev', 'sw engineer', 'software development engineer',
            'sde ', 'sde-', 'software dev engineer',
            # IC engineering roles that aren't software-named but are still IC
            'backend engineer', 'frontend engineer', 'full stack engineer',
            'forward deployed',
            'underwriting', 'loan ', 'real estate',
            'area sales', 'territory sales',
            'business development', 'sales executive', 'account executive',
        ]
    elif profile['domain'] == 'finance':
        # Finance resume → penalise pure IC tech and unrelated sales
        WRONG_ROLES = [
            'software engineer', 'programmer', 'devops',
            'area sales', 'civil engineer',
        ]
    elif profile['domain'] == 'data_ml':
        # Data/ML resume → penalise pure sales and finance ops
        WRONG_ROLES = [
            'area sales', 'loan officer', 'underwriting',
            'territory sales',
        ]
    else:
        WRONG_ROLES = []   # Unknown domain — don't penalise anything

    _JUNIOR_CODES = [
        ' l1', ' l2', ' l3', 'fresher', 'trainee', 'intern',
        'graduate trainee', 'entry level', 'associate engineer',
        'junior developer',
    ]
    is_junior_role    = any(kw in job_lower for kw in _JUNIOR_CODES)
    is_wrong_function = (
        any(kw in job_lower for kw in WRONG_ROLES)
        or (profile['domain'] == 'tech_management' and is_technical_lead_role(job_lower))
    )
    is_senior_resume  = profile['level'] in ('senior', 'mid')

    if (is_wrong_function or (is_senior_resume and is_junior_role)) and raw_score > 35:
        reason = (
            f"Role mismatch: '{job_title}' conflicts with detected profile "
            f"({profile['level']} {profile['domain']})"
        )
        return 35.0, reason

    return raw_score, ""


class HybridScorer:
    def __init__(self):
        """
        Initialize hybrid scorer with AUTOMATIC career switch detection
        
        NO MORE MANUAL TOGGLE - the system detects career switching automatically
        based on domain analysis and transferability assessment.
        """
        self.keyword_matcher = KeywordMatcher()
        self.groq_analyzer   = GroqAnalyzer()
        self._profile_cache: dict = {}   # resume_hash → profile dict (cached per session)

        print(f"[HybridScorer] Initialized with automatic career switch detection")

    def _get_profile(self, resume_text: str) -> dict:
        """Return cached detect_profile_type result for this resume."""
        key = hash(resume_text[:500])
        if key not in self._profile_cache:
            self._profile_cache[key] = detect_profile_type(resume_text)
            print(f"[HybridScorer] Detected profile: {self._profile_cache[key]}")
        return self._profile_cache[key]
    
    def _calculate_weights(self, domain_match, transferability):
        """
        ✅ NEW: Automatically calculate weights based on domain analysis
        
        Logic:
        - Same domain → Balance keywords and context equally (50/50)
        - Different domain → Weight keywords more based on transferability:
          * High: 60/40 (some overlap, moderate boost)
          * Medium: 70/30 (clear career switch, significant boost)
          * Low: 80/20 (major pivot, maximum boost)
        
        Args:
            domain_match: Boolean - do job and candidate domains match?
            transferability: String - "High", "Medium", or "Low"
        
        Returns:
            tuple: (keyword_weight, context_weight)
        """
        if domain_match:
            # Same domain - balance equally
            keyword_weight = 0.5
            context_weight = 0.5
            reason = "Same domain - balanced weighting"
        else:
            # Different domains - adjust based on transferability
            if transferability == "High":
                keyword_weight = 0.6
                context_weight = 0.4
                reason = "Career switch detected (High transferability) - moderate keyword boost"
            elif transferability == "Medium":
                keyword_weight = 0.7
                context_weight = 0.3
                reason = "Career switch detected (Medium transferability) - significant keyword boost"
            else:  # Low or Unknown
                keyword_weight = 0.8
                context_weight = 0.2
                reason = "Major career pivot detected (Low transferability) - maximum keyword boost"
        
        print(f"[HybridScorer] Weight calculation: {reason}")
        print(f"[HybridScorer] Weights: {keyword_weight:.0%} keywords, {context_weight:.0%} context")
        
        return keyword_weight, context_weight
    
    def score_job(self, resume, job):
        """
        Score a job using hybrid approach with AUTOMATIC career switch detection
        
        Args:
            resume: Resume text
            job: Job dict with title, company, description
        
        Returns:
            dict with final_score, keyword_score, context_score, recommendation, 
            model_used, domain_match, transferability, weights_used
        """
        
        print(f"\n{'='*80}")
        print(f"Analyzing: {job['company']} - {job['title']}")
        print(f"{'='*80}")
        
        # Step 1: Rule-based filter (hard requirements)
        print(f"[1/3] Running rule-based filter...")
        rule_score = 100.0  # Placeholder - you can add your rule logic here
        print(f"   Rule Score: {rule_score}%")
        
        # Step 2: Keyword matching
        print(f"[2/3] Running keyword analysis...")
        keyword_result = self.keyword_matcher.match(resume, job['description'])
        keyword_score = keyword_result['match_percentage']
        matched_skills = len(keyword_result['matched_skills'])
        total_skills = len(keyword_result['job_skills'])
        print(f"   Keyword Score: {keyword_score}%")
        print(f"   Matched Skills: {matched_skills}/{total_skills}")
        
        # Step 3: Context analysis (domain matching)
        print(f"[3/3] Running context analysis (domain matching)...")
        context_result = self.groq_analyzer.analyze_job_match(resume, job['description'])
        context_score = context_result.get('context_score', 50)
        model_used = context_result.get('model_used', 'unknown')
        
        # Extract domain analysis
        domain_match = context_result.get('domain_match', False)
        transferability = context_result.get('transferability', 'Unknown')
        
        print(f"   Context Score: {context_score}%")
        print(f"   Job Domain: {context_result.get('job_domain', 'Unknown')}")
        print(f"   Candidate Domain: {context_result.get('candidate_domain', 'Unknown')}")
        print(f"   Same Domain: {domain_match}")
        print(f"   Transferability: {transferability}")
        
        # ✅ NEW: Automatically calculate weights based on domain analysis
        keyword_weight, context_weight = self._calculate_weights(domain_match, transferability)
        
        # Calculate final score with automatic weights
        raw_score = (keyword_score * keyword_weight) + (context_score * context_weight)
        raw_score = round(raw_score, 1)

        # Apply role-mismatch penalty using cached profile (one detect per session)
        profile = self._get_profile(resume)
        final_score, mismatch_reason = role_mismatch_penalty(
            job.get('title', ''), resume, raw_score, profile=profile
        )

        # Determine recommendation
        if final_score >= 70:
            recommendation = "APPLY"
        elif final_score >= 50:
            recommendation = "Review"
        else:
            recommendation = "Skip"

        scored_by = context_result.get('scored_by', 'groq_ai')

        print(f"{'='*80}")
        print(f"FINAL SCORE: {final_score}% ({recommendation})"
              + (f" [PENALISED: {mismatch_reason}]" if mismatch_reason else ""))
        print(f"   = (Keyword {keyword_score}% × {keyword_weight}) + "
              f"(Context {context_score}% × {context_weight})")

        if not domain_match:
            print(f"   Career switch detected — Transferability: {transferability} "
                  f"→ Keyword weight: {keyword_weight:.0%}")
        print(f"{'='*80}")

        result = {
            "final_score": final_score,
            "keyword_score": keyword_score,
            "context_score": context_score,
            "recommendation": recommendation,
            "model_used": model_used,
            "scored_by": scored_by,
            "matched_skills": matched_skills,
            "total_skills": total_skills,
            "domain_match": domain_match,
            "transferability": transferability,
            "weights_used": {
                "keyword_weight": keyword_weight,
                "context_weight": context_weight,
            },
        }
        if mismatch_reason:
            result["role_mismatch_reason"] = mismatch_reason
        return result


# Test the automatic detection
if __name__ == "__main__":
    import sys
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "SAME DOMAIN (Tech PM → Tech PM)",
            "resume": """
            Product Manager with 5 years experience in SaaS tech companies.
            Skills: Agile, roadmapping, SQL, Python, cloud platforms.
            Experience: Led product teams at Google and Microsoft.
            """,
            "job": {
                "title": "Senior Product Manager - AI Platform",
                "company": "Adobe",
                "description": """
                We're looking for a Senior PM with 5+ years in tech/software.
                Requirements: Product strategy, Agile, SQL, stakeholder management.
                """
            },
            "expected_weights": (0.5, 0.5),
            "expected_behavior": "Should use 50/50 weights (same domain)"
        },
        {
            "name": "CAREER SWITCH (Architecture PM → Tech PM)",
            "resume": """
            Product Manager with 8 years in architecture and real estate.
            Recent: 1 year as PM at tech startup.
            Skills: Agile, roadmapping, stakeholder management, SQL.
            """,
            "job": {
                "title": "Senior Product Manager - AI Platform",
                "company": "Google",
                "description": """
                We're looking for a Senior PM with 5+ years in tech/software.
                Requirements: AI/ML experience, Python, cloud platforms, Agile.
                """
            },
            "expected_weights": (0.7, 0.3),
            "expected_behavior": "Should detect career switch, use 70/30 weights"
        }
    ]
    
    print("=" * 80)
    print("TESTING AUTOMATIC CAREER SWITCH DETECTION")
    print("=" * 80)
    
    scorer = HybridScorer()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST SCENARIO {i}: {scenario['name']}")
        print(f"{'='*80}")
        print(f"Expected: {scenario['expected_behavior']}")
        print(f"{'='*80}\n")
        
        result = scorer.score_job(scenario['resume'], scenario['job'])
        
        print(f"\n{'='*80}")
        print(f"RESULT ANALYSIS:")
        print(f"{'='*80}")
        print(f"Final Score: {result['final_score']}%")
        print(f"Domain Match: {result['domain_match']}")
        print(f"Transferability: {result['transferability']}")
        print(f"Weights Used: Keyword {result['weights_used']['keyword_weight']:.0%}, Context {result['weights_used']['context_weight']:.0%}")
        print(f"Expected Weights: Keyword {scenario['expected_weights'][0]:.0%}, Context {scenario['expected_weights'][1]:.0%}")
        
        # Verify weights match expectations
        actual_kw = result['weights_used']['keyword_weight']
        expected_kw = scenario['expected_weights'][0]
        
        if abs(actual_kw - expected_kw) < 0.01:
            print(f"✅ PASS: Weights match expected behavior")
        else:
            print(f"❌ FAIL: Weights don't match (got {actual_kw:.0%}, expected {expected_kw:.0%})")
        
        print(f"{'='*80}")
    
    print("\n\n" + "="*80)
    print("AUTOMATIC CAREER SWITCH DETECTION TEST COMPLETE")
    print("="*80)
