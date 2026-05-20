"""
TitleSuggester - Suggests job titles based on resume

This is a simple implementation that uses Groq to suggest titles.
If you already have title_suggester.py, compare and merge.
"""

import os
from groq import Groq


class TitleSuggester:
    def __init__(self):
        """Initialize with Groq API"""
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        print("[TitleSuggester] Initialized with Groq API")
    
    def suggest_titles(self, resume):
        """
        Suggest job titles based on resume
        
        Args:
            resume: Resume text
        
        Returns:
            list: List of 5-8 suggested job titles
        """
        
        prompt = f"""Based on this resume, suggest 5-8 relevant job titles the person should search for.

Resume:
{resume[:2000]}

Return ONLY a JSON array of job titles. No explanation. Format:
["Title 1", "Title 2", "Title 3", ...]

Example:
["Product Manager", "Senior Product Manager", "Technical Product Manager"]

Your response (JSON array only):"""
        
        try:
            # Try with Groq
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a career advisor. Return ONLY valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            print(f"[TitleSuggester] Raw response: {result}")
            
            # Parse JSON
            import json
            import re
            
            # Remove markdown code blocks if present
            result = re.sub(r'```json\s*|\s*```', '', result)
            
            # Parse JSON
            titles = json.loads(result)
            
            # Validate it's a list
            if not isinstance(titles, list):
                raise ValueError("Response is not a list")
            
            # Ensure all items are strings
            titles = [str(t) for t in titles if t]
            
            print(f"[TitleSuggester] Parsed {len(titles)} titles: {titles}")
            
            # ✅ RETURN LIST (not dict, not string)
            return titles[:8]  # Max 8 titles
        
        except Exception as e:
            print(f"[TitleSuggester] Error: {str(e)}")
            print("[TitleSuggester] Falling back to defaults")
            
            # ✅ FALLBACK: Return default titles as LIST
            return [
                "Product Manager",
                "Senior Product Manager",
                "Technical Product Manager",
                "AI Product Manager",
                "Product Lead",
                "Associate Product Manager",
                "Principal Product Manager",
                "Group Product Manager"
            ]


# Test the suggester
if __name__ == "__main__":
    import sys
    
    print("="*80)
    print("TESTING TitleSuggester")
    print("="*80)
    
    test_resume = """
    Product Manager with 8 years experience in architecture and real estate.
    Recently transitioned to tech with 1 year at a startup.
    Skills: Agile, roadmapping, stakeholder management, SQL, Python basics.
    """
    
    suggester = TitleSuggester()
    titles = suggester.suggest_titles(test_resume)
    
    print(f"\n{'='*80}")
    print(f"RESULT:")
    print(f"{'='*80}")
    print(f"Type: {type(titles)}")
    print(f"Count: {len(titles)}")
    print(f"Titles: {titles}")
    
    # Verify it's JSON-serializable
    import json
    print(f"\nJSON serializable: {json.dumps({'titles': titles})}")
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE - titles is a proper list")
    print(f"{'='*80}")
