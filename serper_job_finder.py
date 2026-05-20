"""
Serper.dev + SerpAPI Job Finder
Fixed version addressing:
1. Serper 404 error (wrong endpoint)
2. SerpAPI skipping all jobs (wrong link parsing)
3. Using working API first (SerpAPI primary)
"""

import requests
import os
from dotenv import load_dotenv
from platform_filter import best_trusted_link, BLOCKED

load_dotenv()


class SerperJobFinder:
    def __init__(self):
        self.serper_key = os.getenv('SERPER_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        
        serper_status = "set" if self.serper_key else "missing"
        serpapi_status = "set" if self.serpapi_key else "missing"
        print(f"[SerperJobFinder] __init__: serper_key={serper_status}, serpapi_key={serpapi_status}")
    
    def search_query(self, query, max_results=10):
        """
        Search using a pre-formed query string (used by api.py for location/remote splits).
        Returns deduplicated list of job dicts.
        """
        print(f"[SerperJobFinder] Searching: {query}")
        try:
            jobs = self._search_serpapi(query)
            if not jobs:
                print("[SerperJobFinder] SerpAPI empty, trying Serper...")
                jobs = self._search_serper(query)
            jobs = jobs[:max_results]
            print(f"[SerperJobFinder] Got {len(jobs)} results")
            return jobs
        except Exception as e:
            print(f"[SerperJobFinder] Error: {e}")
            return []

    def search_jobs(self, job_titles, location="India", max_results=10):
        """
        Legacy method — builds queries internally and delegates to search_query().
        Kept for backward compatibility.
        """
        all_jobs = []
        for title in job_titles:
            all_jobs.extend(self.search_query(f"{title} jobs {location}", max_results))

        # Deduplicate by company + title
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job['company']}_{job['title']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        print(f"[SerperJobFinder] Total unique jobs: {len(unique_jobs)}")
        return unique_jobs
    
    def _search_serper(self, query):
        """Search using Serper.dev API"""
        if not self.serper_key:
            print("[SerperJobFinder] No Serper API key, skipping")
            return []
        
        # ✅ FIX 1: Use /jobs endpoint (not /search)
        url = "https://google.serper.dev/jobs"
        headers = {
            'X-API-KEY': self.serper_key,
            'Content-Type': 'application/json'
        }
        
        body = {
            "q": query,
            "num": 10,
            "location": "India",
            "tbs": "qdr:d"  # 24-hour filter
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Jobs are in 'jobs' key
                if 'jobs' in data:
                    jobs = data['jobs']
                    return self._parse_serper_jobs(jobs)
                else:
                    print(f"[SerperJobFinder] No 'jobs' key in Serper response: {list(data.keys())}")
                    return []
            else:
                print(f"[SerperJobFinder] Serper API error: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"[SerperJobFinder] Serper request failed: {str(e)}")
            return []
    
    def _search_serpapi(self, query):
        """Search using SerpAPI"""
        if not self.serpapi_key:
            print("[SerperJobFinder] No SerpAPI key, skipping")
            return []
        
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": "India",
            "chips": "date_posted:today",  # 24-hour filter
            "api_key": self.serpapi_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API error in response
                if 'error' in data:
                    print(f"[SerperJobFinder] SerpAPI error in response: {data['error']}")
                    return []
                
                # Jobs are in 'jobs_results'
                if 'jobs_results' in data:
                    jobs = data['jobs_results']
                    return self._parse_serpapi_jobs(jobs)
                else:
                    print(f"[SerperJobFinder] No jobs_results in SerpAPI response: {list(data.keys())}")
                    return []
            else:
                print(f"[SerperJobFinder] SerpAPI error: {response.status_code}")
                return []
        
        except requests.exceptions.Timeout:
            print(f"[SerperJobFinder] SerpAPI request timed out")
            return []
        except Exception as e:
            print(f"[SerperJobFinder] SerpAPI request failed: {str(e)}")
            return []
    
    def _parse_serper_jobs(self, jobs_data):
        """Parse jobs from Serper.dev response"""
        parsed_jobs = []
        
        for job in jobs_data:
            # Extract apply link
            apply_link = None
            
            if 'related_links' in job and len(job['related_links']) > 0:
                apply_link = job['related_links'][0].get('link', '')
            elif 'link' in job:
                apply_link = job['link']
            
            if not apply_link:
                print(f"[SerperJobFinder] No link for job: {job.get('title')}")
                continue
            
            # Extract extensions (posted date, job type)
            posted_date = "Unknown"
            job_type = "Unknown"
            
            if 'extensions' in job:
                for ext in job['extensions']:
                    if 'ago' in ext or 'days' in ext or 'hours' in ext:
                        posted_date = ext
                    elif ext in ['Full-time', 'Part-time', 'Contract', 'Internship']:
                        job_type = ext
            
            parsed_job = {
                "title": job.get('title', 'Unknown Title'),
                "company": job.get('company', 'Unknown Company'),
                "location": job.get('location', 'Unknown Location'),
                "description_snippet": job.get('description', '')[:200],
                "apply_link": apply_link,
                "posted_date": posted_date,
                "job_type": job_type,
                "source": "serper",
                "description": job.get('description', '')
            }
            
            parsed_jobs.append(parsed_job)
        
        return parsed_jobs
    
    def _best_apply_link(self, job):
        """
        Extract the best direct apply URL from a SerpAPI job result.

        Priority:
          1. apply_options — company career pages / LinkedIn / Naukri (actual postings)
          2. related_links — secondary platform links
          3. share_link / source_link — Google's own direct link if present
          4. Google wrapper URL built from job_id — last resort (expires, but better than nothing)
        """
        # 1. apply_options contains real platform links (LinkedIn, Naukri, company sites)
        options = job.get('apply_options', [])
        if options:
            trusted = best_trusted_link(options)
            if trusted:
                return trusted
            # No trusted link found — fall back to first non-blocked option
            for opt in options:
                link = opt.get('link', '')
                if not any(b in link.lower() for b in BLOCKED):
                    return link
            return options[0].get('link', '')

        # 2. related_links (used by Serper responses too)
        for rl in job.get('related_links', []):
            if rl.get('link'):
                return rl['link']

        # 3. share_link or source_link (direct Google-provided link, shorter-lived than job_id wrapper)
        if job.get('share_link'):
            return job['share_link']
        if job.get('source_link'):
            return job['source_link']

        # 4. Google wrapper URL — still opens the job, just not a direct platform link
        if job.get('job_id'):
            return f"https://www.google.com/search?ibp=htl;jobs&q={job['job_id']}"

        return None

    def _parse_serpapi_jobs(self, jobs_data):
        """Parse jobs from SerpAPI response, using real platform URLs."""
        parsed_jobs = []

        for job in jobs_data:
            apply_link = self._best_apply_link(job)

            if not apply_link:
                print(f"[SerperJobFinder] ⚠️  No link found for: {job.get('title')}")
                title_query = job.get('title', '').replace(' ', '+')
                apply_link = f"https://www.google.com/search?q={title_query}+jobs"
            
            # Extract job details
            posted_date = "Unknown"
            job_type = "Unknown"
            
            if 'detected_extensions' in job:
                exts = job['detected_extensions']
                posted_date = exts.get('posted_at', 'Unknown')
                job_type = exts.get('schedule_type', 'Unknown')
            
            # Extract description
            description = job.get('description', '')
            
            # If no description, try job_highlights
            if not description and 'job_highlights' in job:
                highlights = job.get('job_highlights', [])
                description_parts = []
                for highlight in highlights:
                    if 'items' in highlight:
                        description_parts.extend(highlight['items'])
                description = ' '.join(description_parts)
            
            parsed_job = {
                "title": job.get('title', 'Unknown Title'),
                "company": job.get('company_name', 'Unknown Company'),
                "location": job.get('location', 'Unknown Location'),
                "description_snippet": description[:200] if description else '',
                "apply_link": apply_link,
                "posted_date": posted_date,
                "job_type": job_type,
                "source": "serpapi",
                "description": description  # Full description
            }
            
            parsed_jobs.append(parsed_job)
            print(f"[SerperJobFinder] ✅ Parsed job: {parsed_job['title']} at {parsed_job['company']}")
        
        return parsed_jobs


# Test the class
if __name__ == "__main__":
    finder = SerperJobFinder()
    jobs = finder.search_jobs(
        job_titles=["Product Manager"],
        location="India",
        max_results=5
    )
    
    print(f"\n{'='*60}")
    print(f"FOUND {len(jobs)} JOBS:")
    print(f"{'='*60}")
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Posted: {job['posted_date']}")
        print(f"   Link: {job['apply_link']}")
        print(f"   Description: {job['description'][:100]}...")
