"""
Test Script: Context Analyzer Domain Mismatch Detection

Tests the enhanced Context Analyzer on critical career switcher cases:
1. Architecture PM → Tech PM (should score LOW due to domain mismatch)
2. Tech PM → Tech PM (should score HIGH due to domain match)
3. InvoiceCloud case (Fintech PM, should catch domain + years gap)

Success Criteria:
- Architecture → Tech PM scores <40%
- Tech → Tech PM scores 70%+
- InvoiceCloud scores <40% (not ~80% from keywords alone)
"""

import os
import sys
from hybrid_scorer import HybridScorer

# Sample resumes
ARCHITECTURE_PM_RESUME = """
HARSH GARG
Project Manager

EXPERIENCE:
Project Manager - Architecture & Real Estate (2018-2025) - 7 years
• Led cross-functional teams for commercial real estate projects
• Managed stakeholder relationships across architecture, construction, and development
• Delivered 15+ projects on time and within budget
• Strong coordination and communication across multiple teams
• Expertise in construction project management and real estate development

Skills:
• Project management, stakeholder management
• Team coordination, budget management
• Agile methodologies (recently learned)
• Basic SQL and data analysis
• Communication and presentation skills

EDUCATION:
Bachelor's Degree - Architecture

CERTIFICATIONS:
- Google Gen AI Certification (2024)
- Product Management fundamentals
"""

TECH_PM_RESUME = """
JANE DOE
Product Manager

EXPERIENCE:
Product Manager - SaaS Tech Company (2019-2026) - 7 years
• Led product development for B2B SaaS platform serving 10,000+ users
• Managed roadmap and prioritization for core product features
• Worked closely with engineering teams on technical requirements
• Launched 3 major features that increased revenue by 40%
• Strong understanding of software development lifecycle

Skills:
• Product management in software/tech
• Agile/Scrum, user stories, backlog management
• SQL, analytics, data-driven decision making
• API understanding, technical documentation
• Cross-functional leadership in tech environment

EDUCATION:
Bachelor's Degree - Computer Science

CERTIFICATIONS:
- Certified Scrum Product Owner (CSPO)
- Product Management certification
"""

# Sample job descriptions
TECH_PM_JOB = """
Product Manager - B2B SaaS

We're looking for a Product Manager to join our SaaS team.

Required:
- 4+ years as Product Manager in Software/Tech industry
- Experience with Agile/Scrum in software development
- SQL and data analysis
- Stakeholder management in tech environment
- Understanding of software development lifecycle

Preferred:
- B2B SaaS background
- Technical degree or software development experience
- API/integration experience
"""

FINTECH_AI_PM_JOB = """
Product Owner, AI - InvoiceCloud

Required:
- 5+ years as Product Owner/Manager in Fintech
- Deep AI/ML product experience
- Financial services domain expertise
- Technical degree (CS/Engineering)
- Experience with payment processing systems

Must have:
- Hands-on AI product development
- Fintech industry background
- Technical API knowledge
- Cloud infrastructure experience
"""

def test_domain_mismatch_detection():
    """Test that Context Analyzer catches domain mismatch"""
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: Set GROQ_API_KEY environment variable")
        print("Get free key at: https://console.groq.com/keys")
        sys.exit(1)
    
    scorer = HybridScorer(groq_api_key=api_key)
    
    print("\n" + "="*80)
    print("CONTEXT ANALYZER VALIDATION TEST")
    print("="*80)
    print("\nTesting domain mismatch detection...")
    
    # Test 1: Architecture PM → Tech PM (should score LOW)
    print("\n" + "#"*80)
    print("TEST 1: Architecture PM → Tech PM (DOMAIN MISMATCH)")
    print("#"*80)
    
    result1 = scorer.score_job(
        job_description=TECH_PM_JOB,
        resume=ARCHITECTURE_PM_RESUME,
        job_title="Product Manager",
        company="Tech SaaS Company"
    )
    
    # Test 2: Tech PM → Tech PM (should score HIGH)
    print("\n" + "#"*80)
    print("TEST 2: Tech PM → Tech PM (DOMAIN MATCH)")
    print("#"*80)
    
    result2 = scorer.score_job(
        job_description=TECH_PM_JOB,
        resume=TECH_PM_RESUME,
        job_title="Product Manager",
        company="Tech SaaS Company"
    )
    
    # Test 3: Architecture PM → Fintech AI PM (should score VERY LOW)
    print("\n" + "#"*80)
    print("TEST 3: Architecture PM → Fintech AI PM (DOMAIN + SKILL MISMATCH)")
    print("#"*80)
    
    result3 = scorer.score_job(
        job_description=FINTECH_AI_PM_JOB,
        resume=ARCHITECTURE_PM_RESUME,
        job_title="Product Owner (AI)",
        company="InvoiceCloud"
    )
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    
    tests_passed = 0
    tests_total = 3
    
    # Test 1 validation
    print(f"\nTest 1: Architecture PM → Tech PM")
    print(f"  Final Score: {result1['final_score']}%")
    print(f"  Context Score: {result1['context_score']}%")
    print(f"  Expected: <40% (domain mismatch penalty)")
    if result1['final_score'] < 40:
        print(f"  ✅ PASS - System correctly detected domain mismatch!")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL - Score too high, domain mismatch not detected")
    
    # Test 2 validation
    print(f"\nTest 2: Tech PM → Tech PM")
    print(f"  Final Score: {result2['final_score']}%")
    print(f"  Context Score: {result2['context_score']}%")
    print(f"  Expected: 70%+ (domain match)")
    if result2['final_score'] >= 70:
        print(f"  ✅ PASS - System correctly identified domain match!")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL - Score too low for same-domain match")
    
    # Test 3 validation (InvoiceCloud equivalent)
    print(f"\nTest 3: Architecture PM → Fintech AI PM (InvoiceCloud case)")
    print(f"  Final Score: {result3['final_score']}%")
    print(f"  Context Score: {result3['context_score']}%")
    print(f"  Expected: <40% (domain + skill mismatch)")
    if result3['final_score'] < 40:
        print(f"  ✅ PASS - System correctly detected severe mismatch!")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL - Score too high, should be <40%")
    
    # Final verdict
    print("\n" + "="*80)
    print(f"FINAL RESULT: {tests_passed}/{tests_total} tests passed")
    print("="*80)
    
    if tests_passed == tests_total:
        print("\n🎉 SUCCESS! Context Analyzer working correctly!")
        print("   Domain mismatch detection is functional.")
        print("   Ready to test on real Jobscan validation dataset.")
    else:
        print("\n⚠️  NEEDS TUNING - Some tests failed.")
        print("   Review Context Analyzer prompt and weights.")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_domain_mismatch_detection()
    sys.exit(0 if success else 1)
