"""
Validation Script - Test Hybrid System Against Jobscan Baseline

Tests the hybrid scorer on the 5 jobs that were validated with Jobscan
to measure accuracy.
"""

import os
import sys
from hybrid_scorer import HybridScorer

# Jobscan baseline scores (ground truth)
JOBSCAN_BASELINE = {
    "Joveo AI - Product Manager": 62,
    "Google - Product Manager, Google Cloud": 61,
    "JPMorgan - Product Manager": 54,
    "Microsoft - Product Manager II": 53,
    "InvoiceCloud - Product Owner (AI)": 33
}

# Sample job descriptions (shortened for testing)
# In production, these would be extracted from LinkedIn
TEST_JOBS = [
    {
        "company": "Joveo AI",
        "title": "Product Manager",
        "jobscan_score": 62,
        "job_description": """
        Product Manager - Joveo AI
        
        We're looking for a Product Manager to join our AI-powered recruitment platform.
        
        Minimum qualifications:
        - Bachelor's degree or equivalent practical experience
        - 3+ years of Product Management experience
        - Experience with agile development
        - Strong analytical skills
        
        Preferred qualifications:
        - Experience in HR tech or recruitment
        - Technical background
        - SQL/data analysis
        - API/integration experience
        """
    },
    {
        "company": "Google",
        "title": "Product Manager, Google Cloud",
        "jobscan_score": 61,
        "job_description": """
        Product Manager, Google Cloud Business Platform
        
        Minimum qualifications:
        - Bachelor's degree or equivalent
        - 5 years of product management experience
        - 2 years technical product experience
        
        Preferred qualifications:
        - MBA or technical degree
        - Experience with cloud platforms
        - Supply chain or procurement experience
        - Understanding of Quote-to-Cash processes
        """
    },
    {
        "company": "JPMorgan",
        "title": "Product Manager",
        "jobscan_score": 54,
        "job_description": """
        Product Manager - JPMorgan Chase
        
        Required:
        - 3+ years product management experience
        - Financial services experience preferred
        - Agile/Scrum methodology
        - Stakeholder management
        
        Preferred:
        - Banking or fintech background
        - Technical skills (SQL, APIs)
        - Market research experience
        """
    },
    {
        "company": "Microsoft",
        "title": "Product Manager II",
        "jobscan_score": 53,
        "job_description": """
        Product Manager II - Microsoft
        
        Qualifications:
        - Bachelor's Degree in relevant field
        - 4+ years product management experience
        - Experience shipping software products
        
        Preferred:
        - Master's degree
        - Technical background (CS/Engineering)
        - Experience with developer tools
        - Azure or cloud platform experience
        """
    },
    {
        "company": "InvoiceCloud",
        "title": "Product Owner (AI)",
        "jobscan_score": 33,
        "job_description": """
        Product Owner, AI - InvoiceCloud
        
        Required:
        - 5+ years as Product Owner/Manager
        - Deep AI/ML product experience
        - Fintech industry background
        - Technical degree (CS/Engineering)
        - Experience with payment processing
        
        Must have:
        - Hands-on AI product development
        - Financial services domain expertise
        - Technical API knowledge
        - Cloud infrastructure experience
        """
    }
]

# Sample resume (Architecture/Real Estate PM background)
RESUME = """
HARSH GARG
Product Manager

EXPERIENCE:

Project Manager - Architecture & Real Estate (2018-2025) - 7 years
• Led cross-functional teams for commercial real estate projects
• Managed stakeholder relationships across architecture, construction, and development
• Delivered 15+ projects on time and within budget
• Strong coordination and communication across multiple teams

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

def calculate_accuracy_metrics(hybrid_scores, jobscan_scores):
    """Calculate correlation and error metrics"""
    import math
    
    n = len(hybrid_scores)
    
    # Mean Absolute Error
    mae = sum(abs(h - j) for h, j in zip(hybrid_scores, jobscan_scores)) / n
    
    # Calculate correlation coefficient
    mean_hybrid = sum(hybrid_scores) / n
    mean_jobscan = sum(jobscan_scores) / n
    
    numerator = sum((h - mean_hybrid) * (j - mean_jobscan) 
                    for h, j in zip(hybrid_scores, jobscan_scores))
    
    denom_hybrid = math.sqrt(sum((h - mean_hybrid)**2 for h in hybrid_scores))
    denom_jobscan = math.sqrt(sum((j - mean_jobscan)**2 for j in jobscan_scores))
    
    correlation = numerator / (denom_hybrid * denom_jobscan) if denom_hybrid and denom_jobscan else 0
    
    return {
        "mae": round(mae, 2),
        "correlation": round(correlation, 3)
    }

def main():
    """Run validation test"""
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: Set GROQ_API_KEY environment variable")
        print("Get free key at: https://console.groq.com/keys")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("HYBRID SYSTEM VALIDATION TEST")
    print("="*80)
    print("\nTesting hybrid scorer against Jobscan baseline...")
    print(f"Jobs to test: {len(TEST_JOBS)}")
    print("\nJobscan Baseline Scores:")
    for job, score in JOBSCAN_BASELINE.items():
        print(f"  - {job}: {score}%")
    
    # Initialize scorer
    scorer = HybridScorer(groq_api_key=api_key)
    
    # Score all jobs
    results = scorer.score_multiple_jobs(TEST_JOBS, RESUME)
    
    # Compare to Jobscan
    print("\n" + "="*80)
    print("RESULTS COMPARISON")
    print("="*80)
    print(f"\n{'Job':<45} | Hybrid | Jobscan | Diff")
    print("-" * 80)
    
    hybrid_scores = []
    jobscan_scores = []
    
    for result in results:
        job_name = f"{result['company']} - {result['job_title']}"
        hybrid_score = result['final_score']
        jobscan_score = JOBSCAN_BASELINE.get(job_name, 0)
        diff = abs(hybrid_score - jobscan_score)
        
        hybrid_scores.append(hybrid_score)
        jobscan_scores.append(jobscan_score)
        
        print(f"{job_name:<45} | {hybrid_score:6.1f} | {jobscan_score:7} | {diff:+5.1f}")
    
    # Calculate metrics
    metrics = calculate_accuracy_metrics(hybrid_scores, jobscan_scores)
    
    print("\n" + "="*80)
    print("ACCURACY METRICS")
    print("="*80)
    print(f"Mean Absolute Error (MAE): {metrics['mae']}%")
    print(f"Correlation: {metrics['correlation']}")
    print("\nTargets:")
    print(f"  MAE < 10%: {'✅ PASS' if metrics['mae'] < 10 else '❌ FAIL'}")
    print(f"  Correlation > 0.85: {'✅ PASS' if metrics['correlation'] > 0.85 else '❌ FAIL'}")
    
    if metrics['mae'] < 10 and metrics['correlation'] > 0.85:
        print("\n🎉 SYSTEM IS ACCURATE! Ready for production use.")
    else:
        print("\n⚠️  System needs tuning. Adjust weights or prompt.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
