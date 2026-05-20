"""
Keyword Matching Component - 60% weight in hybrid system
Extracts skills from job description and counts matches in resume
"""

import re
from typing import Dict, List, Set

class KeywordMatcher:
    """Matches job requirements against resume using keyword extraction"""
    
    # Common PM skills to look for
    PM_SKILLS = [
        "product management", "product manager", "agile", "scrum", "jira",
        "sql", "analytics", "data analysis", "stakeholder management",
        "roadmap", "user stories", "requirements gathering", "wireframes",
        "a/b testing", "metrics", "kpis", "okrs", "sprint planning",
        "backlog", "prioritization", "market research", "competitive analysis",
        "user research", "mvp", "product strategy", "go-to-market",
        "cross-functional", "api", "technical documentation"
    ]
    
    TECHNICAL_SKILLS = [
        "python", "java", "javascript", "react", "node.js", "aws", "azure",
        "docker", "kubernetes", "git", "ci/cd", "rest api", "graphql",
        "sql", "nosql", "mongodb", "postgresql", "redis", "elasticsearch"
    ]
    
    SOFT_SKILLS = [
        "leadership", "communication", "collaboration", "problem-solving",
        "analytical", "strategic", "organizational", "time management",
        "presentation", "negotiation", "influence", "decision-making"
    ]
    
    def __init__(self):
        self.all_skills = set(
            self.PM_SKILLS + self.TECHNICAL_SKILLS + self.SOFT_SKILLS
        )
    
    def extract_skills_from_text(self, text: str) -> Set[str]:
        """Extract skills mentioned in text"""
        text_lower = text.lower()
        found_skills = set()
        
        for skill in self.all_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        return found_skills
    
    def calculate_match_score(self, job_description: str, resume: str) -> Dict:
        """
        Calculate keyword match score between job and resume
        
        Returns:
            {
                "score": 0-100,
                "required_skills": [...],
                "matched_skills": [...],
                "missing_skills": [...],
                "match_percentage": 0-100
            }
        """
        # Extract skills from job description
        job_skills = self.extract_skills_from_text(job_description)
        
        # Extract skills from resume
        resume_skills = self.extract_skills_from_text(resume)
        
        # Calculate matches
        matched_skills = job_skills.intersection(resume_skills)
        missing_skills = job_skills - resume_skills
        
        # Calculate percentage
        if len(job_skills) == 0:
            match_percentage = 0
        else:
            match_percentage = (len(matched_skills) / len(job_skills)) * 100
        
        return {
            "score": round(match_percentage, 1),
            "required_skills": sorted(list(job_skills)),
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "total_job_skills": len(job_skills),
            "total_matched": len(matched_skills)
        }

    def match(self, resume: str, job_description: str) -> Dict:
        """Wrapper for HybridScorer compatibility — note arg order is (resume, job_description)"""
        result = self.calculate_match_score(job_description, resume)
        return {
            'match_percentage': result['score'],
            'matched_skills': result['matched_skills'],
            'job_skills': result['required_skills'],
            'missing_skills': result['missing_skills']
        }

if __name__ == "__main__":
    # Test
    matcher = KeywordMatcher()
    
    job_desc = "Looking for Product Manager with 5+ years experience in Agile, SQL, and stakeholder management"
    resume = "Product Manager with experience in Agile development and SQL analytics"
    
    result = matcher.calculate_match_score(job_desc, resume)
    print(f"Match Score: {result['score']}%")
    print(f"Matched: {result['matched_skills']}")
    print(f"Missing: {result['missing_skills']}")
