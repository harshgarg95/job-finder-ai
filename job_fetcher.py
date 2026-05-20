"""
Updated job_fetcher.py with:
- Better logging prefix
- Skip jobs that already have descriptions (from API)
"""

import requests
from bs4 import BeautifulSoup
import time


class JobFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 10
    
    def fetch_job_details(self, job_url):
        """
        Fetch full job description from URL
        
        Args:
            job_url: URL of the job posting
        
        Returns:
            dict with description and success status
        """
        try:
            response = requests.get(job_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code != 200:
                return {"description": "", "success": False}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try common selectors for job descriptions
            description = None
            selectors = [
                '.job-description',
                '#job-description',
                '[class*="description"]',
                'article',
                'main'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to all paragraphs
            if not description:
                paragraphs = soup.find_all('p')
                description = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Clean up
            description = ' '.join(description.split())
            
            return {
                "description": description,
                "success": True
            }
        
        except Exception as e:
            return {"description": "", "success": False}
    
    # Indian cities — if the location field is one of these, the role is On-site
    # unless the description EXPLICITLY says remote.
    _CITIES = {
        'mumbai', 'delhi', 'bangalore', 'bengaluru', 'hyderabad', 'pune',
        'chennai', 'kolkata', 'ahmedabad', 'gurgaon', 'gurugram', 'noida',
        'kochi', 'thiruvananthapuram', 'indore', 'jaipur', 'chandigarh',
        'lucknow', 'nagpur', 'surat', 'vadodara', 'coimbatore', 'bhopal',
    }

    _REMOTE_EXPLICIT = (
        'fully remote', 'remote position', 'remote role', 'remote opportunity',
        'remote work', 'work from home', 'work from anywhere', 'wfh',
        '100% remote', 'remote-first',
    )
    _HYBRID_KW = ('hybrid', 'flexible work', 'remote-friendly', 'partial remote')
    _ONSITE_KW = ('on-site', 'onsite', 'in-office', 'office-based',
                  'must relocate', 'relocation required')

    def _detect_job_type(self, job):
        """
        Accurate Remote/Hybrid/On-site detection.

        Rules (in priority order):
        1. Explicit on-site markers in title/description → On-site
        2. Location is a specific Indian city AND description has no explicit remote → On-site
        3. Location is 'remote', 'anywhere', or 'work from home' → Remote
        4. Hybrid keyword anywhere → Hybrid
        5. Explicit remote phrase in description or title → Remote
        6. Default → On-site
        """
        location = job.get('location', '').lower().strip()
        title    = job.get('title', '').lower()
        desc     = (job.get('description', '') + ' ' + job.get('description_snippet', '')).lower()

        # 1. Hard on-site markers in description/title
        if any(kw in desc or kw in title for kw in self._ONSITE_KW):
            return 'On-site'

        # 2. Location is a specific city → On-site unless description is explicit about remote
        loc_has_city = any(city in location for city in self._CITIES)
        if loc_has_city:
            if any(phrase in desc or phrase in title for phrase in self._REMOTE_EXPLICIT):
                return 'Remote'   # city-based company offering remote work
            if 'hybrid' in location or any(kw in desc for kw in self._HYBRID_KW):
                return 'Hybrid'
            return 'On-site'

        # 3. Location field itself says remote / anywhere
        if any(kw in location for kw in ('remote', 'anywhere', 'work from home', 'wfh')):
            return 'Remote'

        # 4. Hybrid keyword
        if any(kw in desc or kw in title or kw in location for kw in self._HYBRID_KW):
            return 'Hybrid'

        # 5. Explicit remote phrase in description/title
        if any(phrase in desc or phrase in title for phrase in self._REMOTE_EXPLICIT):
            return 'Remote'

        return 'On-site'

    def batch_fetch(self, jobs_list):
        """
        ✅ UPDATED: Skip jobs that already have descriptions from API
        Only fetch for jobs missing descriptions
        
        Args:
            jobs_list: List of job dicts with 'apply_link' field
        
        Returns:
            Same list with 'description' field added/updated
        """
        for job in jobs_list:
            # ✅ Skip if description already exists from SerpAPI/Serper
            if 'description' in job and job['description'] and len(job['description']) > 100:
                print(f"[JobFetcher] Using existing description for: {job['title']}")
                continue
            
            # Only fetch if no description or description is too short
            if 'apply_link' in job:
                print(f"[JobFetcher] Fetching description for: {job['title']}")
                result = self.fetch_job_details(job['apply_link'])
                
                if result['success']:
                    job['description'] = result['description']
                else:
                    print(f"[JobFetcher] Failed to fetch: {job['title']}")
                    # Use snippet as fallback
                    job['description'] = job.get('description_snippet', '')
                
                # Be nice to servers
                time.sleep(1)
        
        # Tag every job with its work arrangement
        for job in jobs_list:
            job['job_type'] = self._detect_job_type(job)

        return jobs_list


# Test the class
if __name__ == "__main__":
    fetcher = JobFetcher()
    
    # Test job
    test_jobs = [
        {
            "title": "Product Manager",
            "company": "Test Corp",
            "apply_link": "https://example.com/job/123",
            "description": ""  # Empty - should fetch
        }
    ]
    
    result = fetcher.batch_fetch(test_jobs)
    print(f"\nFetched {len(result)} jobs")
    print(f"First job description length: {len(result[0]['description'])} chars")
