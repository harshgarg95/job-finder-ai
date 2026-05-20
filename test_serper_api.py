#!/usr/bin/env python3
"""
Quick Test Script for Serper API
Run this to diagnose "No jobs found" error
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("SERPER API DIAGNOSTIC TEST")
print("=" * 60)

# Check if API key exists
serper_key = os.getenv('SERPER_API_KEY')
serpapi_key = os.getenv('SERPAPI_KEY')

print("\n1. CHECKING ENVIRONMENT VARIABLES:")
print("-" * 60)
if serper_key:
    print(f"✅ SERPER_API_KEY found (first 10 chars): {serper_key[:10]}...")
else:
    print("❌ SERPER_API_KEY not found in .env file!")
    print("   Fix: Add SERPER_API_KEY=your_key_here to .env")

if serpapi_key:
    print(f"✅ SERPAPI_KEY found (first 10 chars): {serpapi_key[:10]}...")
else:
    print("⚠️  SERPAPI_KEY not found (optional backup)")

# Test Serper API
if serper_key:
    print("\n2. TESTING SERPER API (PRIMARY):")
    print("-" * 60)
    
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': serper_key,
        'Content-Type': 'application/json'
    }
    
    # Test with Google Jobs
    body = {
        "q": "Product Manager jobs India",
        "type": "jobs",
        "num": 5
    }
    
    print(f"📡 Calling: {url}")
    print(f"📦 Request body: {json.dumps(body, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        
        print(f"\n📬 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Response keys: {list(data.keys())}")
            
            if 'jobs' in data:
                jobs = data['jobs']
                print(f"\n✅ SUCCESS! Found {len(jobs)} jobs")
                
                if len(jobs) > 0:
                    print(f"\n📋 First job:")
                    job = jobs[0]
                    print(f"   Title: {job.get('title', 'N/A')}")
                    print(f"   Company: {job.get('company', 'N/A')}")
                    print(f"   Location: {job.get('location', 'N/A')}")
                    
                    # Check for apply link
                    if 'related_links' in job and len(job['related_links']) > 0:
                        link = job['related_links'][0].get('link', 'N/A')
                        print(f"   Apply Link: {link}")
                    elif 'link' in job:
                        print(f"   Link: {job.get('link', 'N/A')}")
                    
                    print(f"\n🎯 SERPER API IS WORKING CORRECTLY!")
            else:
                print(f"\n❌ ERROR: No 'jobs' key in response")
                print(f"   Available keys: {list(data.keys())}")
                print(f"\n   This means 'type': 'jobs' parameter may not be working")
                print(f"   Full response:")
                print(json.dumps(data, indent=2)[:500])
        
        elif response.status_code == 401:
            print(f"\n❌ ERROR: Invalid API key (401 Unauthorized)")
            print(f"   Fix: Check your Serper API key at https://serper.dev/dashboard")
        
        elif response.status_code == 429:
            print(f"\n❌ ERROR: Rate limit exceeded (429 Too Many Requests)")
            print(f"   You've used all 2,500 free searches this month")
            print(f"   Fix: Wait for monthly reset or use SerpAPI backup")
        
        else:
            print(f"\n❌ ERROR: Unexpected status code")
            print(f"   Response: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timed out")
        print(f"   Check your internet connection")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Connection failed")
        print(f"   Check your internet connection")
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

# Test SerpAPI if available
if serpapi_key:
    print("\n3. TESTING SERPAPI (BACKUP):")
    print("-" * 60)
    
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": "Product Manager jobs India",
        "api_key": serpapi_key
    }
    
    print(f"📡 Calling: {url}")
    print(f"📦 Params: engine=google_jobs, q=Product Manager jobs India")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n📬 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Response keys: {list(data.keys())}")
            
            if 'jobs_results' in data:
                jobs = data['jobs_results']
                print(f"\n✅ SUCCESS! Found {len(jobs)} jobs")
                
                if len(jobs) > 0:
                    print(f"\n📋 First job:")
                    job = jobs[0]
                    print(f"   Title: {job.get('title', 'N/A')}")
                    print(f"   Company: {job.get('company_name', 'N/A')}")
                    print(f"   Location: {job.get('location', 'N/A')}")
                    print(f"   Apply Link: {job.get('apply_link', 'N/A')}")
                    
                    print(f"\n🎯 SERPAPI IS WORKING CORRECTLY!")
            else:
                print(f"\n❌ ERROR: No 'jobs_results' key in response")
                print(f"   Available keys: {list(data.keys())}")
        
        elif response.status_code == 401:
            print(f"\n❌ ERROR: Invalid API key (401 Unauthorized)")
        
        elif response.status_code == 429:
            print(f"\n❌ ERROR: Rate limit exceeded")
            print(f"   You've used all 250 free searches this month")
        
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY & NEXT STEPS:")
print("=" * 60)

if serper_key:
    print("\n✅ If Serper test passed:")
    print("   → The issue is in your serper_job_finder.py code")
    print("   → Check the CRITICAL_FIXES_JOB_SEARCH.md document")
    print("   → Make sure 'type': 'jobs' is in the request body")
else:
    print("\n❌ Serper API key missing:")
    print("   → Add SERPER_API_KEY to your .env file")
    print("   → Get key from https://serper.dev/dashboard")

print("\n📖 For detailed debugging:")
print("   → See DEBUGGING_NO_JOBS_FOUND.md")
print("\n" + "=" * 60)
