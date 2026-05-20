# Platform Coverage Report

**Date:** 2026-05-06  
**Search Titles:** AI Implementation Manager, Product Manager  
**Location:** India  
**Jobs per title:** 10 (max_results_per_title=10)

---

## API Used

| Setting | Value |
|---|---|
| Primary API | **SerpAPI** (`google_jobs` engine) |
| Fallback API | Serper.dev (not triggered — SerpAPI succeeded) |
| Engine | `google_jobs` — queries Google's job search aggregator |
| Rate limit | ~100 searches/month (free tier) |

---

## How Google Jobs Aggregation Works

SerpAPI's `google_jobs` engine fetches jobs directly from **Google Jobs**, which is a meta-aggregator. Google Jobs indexes listings from multiple platforms automatically. The job results do not come labelled with a source platform in the API response — they all return as Google Jobs entries with encoded `htidocid` references.

All 20 URLs follow the pattern:
```
https://www.google.com/search?ibp=htl;jobs&q=<base64-encoded-job-id>
```

This means **the app is effectively searching all platforms that Google Jobs indexes**, which includes:

---

## Platforms Covered (via Google Jobs)

Google Jobs aggregates from the following platforms for India job searches:

| Platform | Indexed by Google Jobs | Notes |
|---|---|---|
| LinkedIn | ✅ Yes | Most professional roles appear here |
| Indeed India | ✅ Yes | High volume, especially mid-level |
| Naukri.com | ✅ Yes | India's largest job board — heavily indexed |
| Shine.com | ✅ Yes | Job 12 (Shine.com Senior Manager) confirms Shine listings appear |
| Glassdoor | ✅ Yes | Company + job data |
| Instahyre | ⚠️ Partial | Startup roles sometimes indexed |
| Hirist | ⚠️ Partial | Tech-specific, partial Google indexing |
| Cutshort | ⚠️ Partial | Tech startup roles, partial indexing |
| Company career pages | ✅ Yes | Adobe, Mastercard, Intuit, Uber, GE Healthcare, Experian, D.E. Shaw all post directly |

**Evidence from results:**
- Adobe, Mastercard, Intuit, Uber, GE Healthcare, Experian — direct company postings (indexed by Google)
- Shine.com — confirmed as a source platform (Job 12 is from shine.com)
- Spysr, Talentmatics, Sirius AI, IMerit, Delphi — likely from Naukri or LinkedIn

---

## Coverage Analysis

### What's well covered
- **Tier-1 companies** (Adobe, Mastercard, Intuit, Uber, GE Healthcare, Experian): Company career pages are indexed → good coverage
- **AI-specific companies** (Spysr, IMerit, Sirius AI, Delphi Consulting): Appear to be indexed via Naukri/LinkedIn
- **Naukri listings**: India's top job board is well-indexed by Google Jobs

### What may be missed
1. **LinkedIn-only postings**: Some LinkedIn jobs are gated and may not be fully indexed by Google. For comprehensive LinkedIn coverage, the app would need LinkedIn Jobs API or a scraper.
2. **Hirist.com / Cutshort**: Tech-focused Indian platforms with strong AI/startup listings — partially indexed at best.
3. **AngelList / Wellfound**: Startup equity roles rarely appear in Google Jobs.
4. **Iimjobs / Foundit (Monster India)**: Mid-to-senior management roles on these platforms may not be fully represented.
5. **Company ATS systems** (Workday, Greenhouse, Lever, Taleo): If a company doesn't surface their ATS postings to Google, they're missed.

---

## Job Search Query Performance

| Title Searched | Jobs Returned | Relevant | Notes |
|---|---|---|---|
| AI Implementation Manager | ~10 | 8–9 | Good specificity — most results are AI/PM roles |
| Product Manager | ~10 | 5–6 | Too broad — pulls pharma, fintech, unrelated domains |
| **Total** | **20** | **13–15** | — |

---

## Recommendations

### 1. Replace "Product Manager" with specific AI-focused titles
```
"AI Product Manager"
"GenAI Program Manager"  
"AI Implementation Manager"
"Technical Product Manager – AI"
```
This will reduce domain pollution (like the Eris pharma job) and improve result quality.

### 2. Add direct Naukri / LinkedIn search (optional enhancement)
To catch jobs that Google Jobs misses, consider adding:
- **Naukri API** (paid) for comprehensive India coverage
- **LinkedIn Jobs API** (requires approval) for full LinkedIn coverage
- **Hirist scraper** for AI/tech-specific Indian roles

### 3. Current setup is sufficient for initial job hunting
The SerpAPI `google_jobs` engine covers the most important platforms. The 20 jobs returned included roles from Adobe, Mastercard, Intuit, Uber, GE Healthcare — these are all enterprise-level postings that validate the search is reaching the right tier of companies.

### 4. Increase `max_results_per_title` for broader searches
Current setting: 10 per title (20 total).  
Recommend: 15–20 per title for richer results, especially with more specific titles.

---

## API Quota Status

- **SerpAPI free tier:** ~100 searches/month
- **Each job search call:** 1 search per title × number of titles
- **At 2 titles:** 2 credits used per full search
- **Remaining budget:** ~98 searches left this month (assuming this was the first run)
- **Groq API:** Free tier, using `llama-3.3-70b-versatile` with fallback chain — no quota issues observed
