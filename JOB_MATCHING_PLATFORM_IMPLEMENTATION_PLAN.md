# 🎯 JOB MATCHING PLATFORM - IMPLEMENTATION PLAN
**Project Goal:** Free/low-cost AI-powered job matching system for career switchers and job seekers

**Last Updated:** April 24, 2026  
**Status:** Planning Phase → Build Phase

---

## 📐 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                     WEB APP (Browser-Based)                      │
│  User Interface: React/HTML → Free hosting: GitHub Pages/Vercel │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT LAYER                              │
│  • Resume upload (PDF/text)                                      │
│  • API Key input (Groq/OpenAI/Claude - optional)                │
│  • Search preferences (job title, location)                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 1: JOB DATA COLLECTION                        │
│  LinkedIn Scraper (start here, add Indeed/Google later)         │
│  • Default: Last 24 hours jobs only                              │
│  • Boolean search support                                        │
│  • Deduplication against CSV history                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 2: INTELLIGENT FILTERING                      │
│                                                                   │
│  Component A: Rule-Based Filter (20% weight)                    │
│  └─ Block: IT companies, developer roles, obvious mismatches    │
│                                                                   │
│  Component B: Keyword Matcher (30% weight)                      │
│  └─ Skills present: PM, Agile, SQL, etc.                        │
│                                                                   │
│  Component C: CONTEXT ANALYZER (50% weight) ← KEY INNOVATION!   │
│  └─ LLM analyzes:                                                │
│     • Industry/Domain match (Architecture PM vs Tech PM)        │
│     • Years in RELEVANT domain (not total years)                │
│     • Required vs Preferred skills separation                    │
│     • Seniority level (Junior/Mid/Senior)                       │
│     • Transferability score                                      │
│                                                                   │
│  API Fallback System:                                            │
│  1st: User's API (if provided)                                   │
│  2nd: Groq (recommended default - free)                          │
│  3rd: Claude API (if user added key)                             │
│  4th: Ollama local (fallback if all fail)                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                  SCORING & RANKING                               │
│  Final Score = (Rules × 0.2) + (Keywords × 0.3) + (Context × 0.5)│
│                                                                   │
│  Thresholds:                                                     │
│  • 70-100% = APPLY (strong match)                                │
│  • 50-69%  = REVIEW (read carefully)                             │
│  • 0-49%   = SKIP (weak match)                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT & STORAGE                               │
│  • CSV file: jobs_history.csv (persistent tracking)             │
│  • Columns: date, title, company, platform, score, status, url  │
│  • Auto-dedup: never process same job twice                     │
│  • Export: filtered list of Apply/Review jobs                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│              CHROME EXTENSION (Phase 2)                          │
│  Quick score any LinkedIn job page:                              │
│  • User on job page → click extension → instant score           │
│  • Like Jobscan/JobTracker                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 COMPONENT BREAKDOWN

### **Component C: CONTEXT ANALYZER** ⭐ The Game Changer

**Problem It Solves:**
```
Resume: "8 years Project Management in Architecture/Real Estate"
Job: "4+ years Product Management in Software/Tech"

❌ Keyword Matcher: "Project Management" found → 80% match!
✅ Context Analyzer: "PM exists BUT wrong domain → 30% match"
```

**LLM Prompt Structure:**
```
Analyze this job vs resume with DOMAIN CONTEXT:

JOB DESCRIPTION:
[full text]

RESUME:
[full text]

CRITICAL: Distinguish between TOTAL experience and RELEVANT experience.

1. DOMAIN/INDUSTRY MATCH:
   - Job industry: Tech/Software/SaaS/Finance/Healthcare/etc.
   - Resume background: Architecture/Real Estate/Consulting/etc.
   - Are they SAME domain? (Yes/No)
   - Transferability: High/Medium/Low
   
2. RELEVANT YEARS CALCULATION:
   - Total PM years: X
   - Years in TARGET domain: Y (THIS is what matters!)
   - Required years in job: Z
   - Gap: Z - Y (not Z - X!)
   
3. REQUIRED SKILLS (in target domain):
   - Job asks: "Agile in software development"
   - Resume has: "Agile in construction projects"
   - Match? NO (different application context)

Return JSON:
{
  "domain_analysis": {
    "job_domain": "Tech/SaaS",
    "resume_domain": "Architecture/Real Estate",
    "same_domain": false,
    "transferability": "Low",
    "score": 0-100
  },
  "relevant_experience": {
    "total_pm_years": 8,
    "relevant_pm_years": 0,
    "required_years": 4,
    "gap": -4,
    "score": 0-100
  },
  "contextual_skills": {
    "required_in_domain": ["Agile in software", "SQL"],
    "candidate_has_in_domain": [],
    "missing": ["Agile in software", "SQL"],
    "score": 0-100
  },
  "overall_score": 0-100,
  "reasoning": "..."
}
```

**Weight:** 50% of final score (highest component)

---

## 💰 COST ANALYSIS

### **Free Tier (Default Path):**

| Component | Cost | Limits |
|-----------|------|--------|
| **Groq API** | $0/month | 1,000 jobs/day |
| **GitHub Pages** (hosting) | $0/month | Unlimited static hosting |
| **CSV Storage** | $0 | Local file |
| **LinkedIn Scraping** | $0 | Manual search URLs (no Apify) |
| **TOTAL** | **$0/month** | Perfect for individual users |

### **Free Tier + Quality (Recommended):**

| Addition | Cost | Value |
|----------|------|-------|
| Groq API (default) | $0/month | Good quality |
| *User adds own Claude API* | User pays (~$1-3/month) | Best quality for career switchers |
| TOTAL | **$0-3/month** | User choice |

### **Heavy User (100+ jobs/day):**

| Scenario | Cost |
|----------|------|
| Groq free tier | $0 (up to 1,000 jobs/day) |
| Claude API if Groq exhausted | ~$0.01/job × 100 = $1/day |
| TOTAL | **$0-30/month** (worst case) |

**Strategy:** Start 100% free (Groq), let users upgrade to their own Claude API if they want premium accuracy.

---

## ✅ QUALITY VALIDATION APPROACH

### **Phase 1: LinkedIn Only (Validation)**

**Test Dataset:** 5 Jobscan-validated jobs

**Metrics to Track:**
```
| Job | Jobscan % | Our Score | Difference | Pass/Fail |
|-----|-----------|-----------|------------|-----------|
| Joveo | 62% | ? | ? | <10% = Pass |
| Google | 61% | ? | ? | <10% = Pass |
| JPMorgan | 54% | ? | ? | <10% = Pass |
| Microsoft | 53% | ? | ? | <10% = Pass |
| InvoiceCloud | 33% | ? | ? | <10% = Pass |

Targets:
✅ MAE < 10% (Mean Absolute Error)
✅ Correlation > 0.85
✅ Correctly identifies domain mismatch (InvoiceCloud case)
```

**Current Status (Keyword-only test):**
- MAE: 8.66% ✅ PASS
- Correlation: 0.949 ✅ PASS
- InvoiceCloud score: 20% (Jobscan: 33%) ✅ Correctly identified as worst

**Next:** Add Context Analyzer and retest

### **Phase 2: Add Indeed (Cross-Platform Validation)**

**Process:**
1. Search same query on LinkedIn + Indeed
2. Find overlapping jobs (same company + title)
3. Score both sources
4. Compare scores for identical jobs

**Expected:** Same job should get same score regardless of platform

**Validation:**
- Score variance < 5% for identical jobs
- Platform-specific jobs scored independently
- Overall accuracy maintained (MAE < 10%)

---

## 📅 IMPLEMENTATION TIMELINE

### **Week 1: Core System (MVP)**
**Goal:** Build and validate Context Analyzer

**Tasks:**
- [ ] Enhance `groq_analyzer.py` with domain analysis logic
- [ ] Add relevant experience calculation (not just total years)
- [ ] Test on Architecture→Tech PM case
- [ ] Adjust scoring weights (Rule 20%, Keyword 30%, Context 50%)
- [ ] Validate on 5 Jobscan jobs
- [ ] Target: MAE < 10%, InvoiceCloud < 40%

**Success Criteria:**
- Context Analyzer catches domain mismatch
- InvoiceCloud scores <40% (currently ~80% with keywords alone)
- All 5 jobs within ±10% of Jobscan scores

---

### **Week 2: Web App Interface**
**Goal:** Build user-facing web application

**Tasks:**
- [ ] Design simple HTML/React UI
- [ ] Resume upload component (PDF/text parsing)
- [ ] API key input field (optional, stored in localStorage)
- [ ] Job search input (keywords, location)
- [ ] Results display table (score, recommendation, details)
- [ ] CSV export functionality
- [ ] Deploy to Vercel/GitHub Pages

**Tech Stack:**
- Frontend: React or vanilla HTML/JavaScript
- Backend: Python Flask API (for scoring logic)
- Hosting: Vercel (supports both frontend + Python backend)
- Storage: Browser localStorage + CSV download

**Success Criteria:**
- User can upload resume
- User can input API key (Groq/Claude/OpenAI)
- User can search jobs
- Results display with scores and recommendations
- CSV export works

---

### **Week 3: LinkedIn Integration**
**Goal:** Automate job data collection from LinkedIn

**Tasks:**
- [ ] Manual URL input (user pastes LinkedIn search URL)
- [ ] LinkedIn page scraper (extract job listings)
- [ ] Last 24 hours filter implementation
- [ ] Deduplication logic (check against CSV history)
- [ ] Boolean search support
- [ ] Error handling for blocked requests

**Approach:**
- Start with manual URL paste (no Apify cost)
- User searches LinkedIn → copies URL → pastes into app
- App extracts jobs from that search page
- Scores and displays results

**Success Criteria:**
- Extracts jobs from LinkedIn search URLs
- Filters to last 24 hours only
- No duplicate jobs processed
- Handles pagination (optional)

---

### **Week 4: Polish + Deploy**
**Goal:** Production-ready release

**Tasks:**
- [ ] Error handling for API failures
- [ ] API fallback system (Groq → Claude → Ollama)
- [ ] Loading states and progress indicators
- [ ] Documentation (README, user guide)
- [ ] Open source release (GitHub)
- [ ] Landing page with demo

**Success Criteria:**
- Graceful error handling
- Clear user instructions
- Open source on GitHub
- Public demo available

---

### **Week 5+: Extensions (Future)**

**Phase 2A: Chrome Extension**
- Quick score any LinkedIn job page
- Click extension → instant score
- Save to history automatically

**Phase 2B: Multi-Platform**
- Add Indeed integration
- Add Google Jobs integration
- Cross-platform validation

**Phase 2C: Advanced Features**
- User accounts (optional)
- Cloud storage (Supabase/Firebase)
- Email alerts for new matches
- Dashboard analytics

---

## 🔨 BUILD SEQUENCE (Step-by-Step)

### **Step 1: Fix Context Analyzer** ⭐ CRITICAL
**Priority:** HIGHEST  
**Time Estimate:** 2-3 hours

**What to build:**
```python
# Enhance groq_analyzer.py

class GroqAnalyzer:
    def analyze_job_match(self, job_description, resume):
        """
        NEW: Add domain context analysis
        """
        
        prompt = f"""
        Analyze this job vs resume with DOMAIN CONTEXT:
        
        JOB: {job_description}
        RESUME: {resume}
        
        CRITICAL ANALYSIS:
        
        1. DOMAIN MATCH:
           - What industry is this job in? (Tech/Finance/Healthcare/etc.)
           - What industry is candidate from? (Architecture/Real Estate/etc.)
           - Are they the SAME? (Yes/No)
           - Transferability score: 0-100
        
        2. RELEVANT EXPERIENCE (NOT total experience):
           - Total years in PM: X
           - Years in TARGET domain: Y
           - Required years: Z
           - Gap: Z - Y (THIS is what matters!)
        
        3. CONTEXTUAL SKILLS:
           - "Agile in software" ≠ "Agile in construction"
           - Skills must match DOMAIN context
        
        Return JSON with domain_analysis, relevant_experience, contextual_skills
        """
        
        # Call Groq API
        # Parse JSON response
        # Return structured analysis
```

**Test Cases:**
```python
# Test 1: Architecture PM → Tech PM (should score LOW)
job = "Tech PM, 4+ years software experience"
resume = "Architecture PM, 8 years construction"
# Expected: <40% (domain mismatch penalty)

# Test 2: Tech PM → Tech PM (should score HIGH)
job = "Tech PM, 4+ years software"
resume = "Tech PM, 5 years SaaS"
# Expected: 80%+ (domain match!)
```

**Success Criteria:**
- InvoiceCloud scores <40% (not ~80%)
- Architecture→Tech PM cases score <50%
- Same-domain cases score 70%+

---

### **Step 2: Adjust Scoring Weights**
**Priority:** HIGH  
**Time Estimate:** 30 minutes

**Change in `hybrid_scorer.py`:**
```python
# OLD weights
self.keyword_weight = 0.6
self.llm_weight = 0.4

# NEW weights (context-heavy for career switchers)
self.rule_weight = 0.2      # Rule-based filter
self.keyword_weight = 0.3   # Keyword matching
self.context_weight = 0.5   # Context analyzer (LLM)

# NEW calculation
final_score = (
    (rule_score * self.rule_weight) +
    (keyword_score * self.keyword_weight) +
    (context_score * self.context_weight)
)
```

**Rationale:** Context understanding is MORE important than keyword matching for career switchers.

---

### **Step 3: API Fallback System**
**Priority:** MEDIUM  
**Time Estimate:** 1-2 hours

**What to build:**
```python
class APIManager:
    """Manages multiple LLM API providers with fallback"""
    
    def __init__(self, user_api_key=None, user_provider=None):
        """
        user_api_key: User's custom API key (optional)
        user_provider: "groq", "claude", "openai", etc.
        """
        
        # Build priority list
        self.priority = []
        
        # 1st: User's API (if provided)
        if user_api_key and user_provider:
            self.priority.append((user_provider, user_api_key))
        
        # 2nd: Groq (recommended default - free)
        if os.getenv("GROQ_API_KEY"):
            self.priority.append(("groq", os.getenv("GROQ_API_KEY")))
        
        # 3rd: Claude API (if available)
        if os.getenv("CLAUDE_API_KEY"):
            self.priority.append(("claude", os.getenv("CLAUDE_API_KEY")))
        
        # 4th: Ollama local (always available as fallback)
        self.priority.append(("ollama", "local"))
    
    def get_analysis(self, job_description, resume):
        """Try each API in priority order until one works"""
        
        last_error = None
        
        for provider, api_key in self.priority:
            try:
                if provider == "groq":
                    return self._call_groq(api_key, job_description, resume)
                elif provider == "claude":
                    return self._call_claude(api_key, job_description, resume)
                elif provider == "openai":
                    return self._call_openai(api_key, job_description, resume)
                elif provider == "ollama":
                    return self._call_ollama(job_description, resume)
                    
            except Exception as e:
                last_error = e
                print(f"{provider} failed: {e}, trying next...")
                continue
        
        raise Exception(f"All APIs failed. Last error: {last_error}")
```

**UI Component:**
```html
<!-- In web app -->
<div class="api-settings">
  <label>API Provider (optional - defaults to free Groq):</label>
  <select id="api-provider">
    <option value="">Auto (Groq free tier)</option>
    <option value="groq">Groq (recommended - free)</option>
    <option value="claude">Claude API (paid - best quality)</option>
    <option value="openai">OpenAI (paid)</option>
  </select>
  
  <input type="text" id="api-key" placeholder="Your API key (optional)">
  <small>Leave blank to use free Groq. Add your own API for better quality.</small>
</div>
```

---

### **Step 4: Build Web Interface**
**Priority:** MEDIUM  
**Time Estimate:** 4-6 hours

**Tech Stack Decision:**
- **Option A:** Pure HTML/JS (no build step, simpler)
- **Option B:** React (better UX, more modern)

**Recommendation:** Start with Option A (HTML/JS), migrate to React later if needed.

**File Structure:**
```
job-matcher-web/
├── index.html          # Main page
├── styles.css          # Styling
├── app.js              # Frontend logic
├── api/
│   └── score.py        # Python Flask API (scoring endpoint)
├── requirements.txt    # Python dependencies
└── vercel.json         # Deployment config
```

**Key Features:**
```javascript
// app.js

class JobMatcher {
    constructor() {
        this.resume = null;
        this.apiKey = localStorage.getItem('apiKey') || null;
        this.history = this.loadHistory();
    }
    
    uploadResume(file) {
        // Parse PDF/text
        // Store in memory
    }
    
    async scoreJobs(jobUrls) {
        // Call Python API
        // Display results
        // Save to CSV
    }
    
    loadHistory() {
        // Load from localStorage
        // Deduplicate jobs
    }
    
    exportCSV() {
        // Download jobs_history.csv
    }
}
```

**Python API Endpoint:**
```python
# api/score.py

from flask import Flask, request, jsonify
from hybrid_scorer import HybridScorer

app = Flask(__name__)

@app.route('/api/score', methods=['POST'])
def score_jobs():
    data = request.json
    
    resume = data['resume']
    jobs = data['jobs']  # List of job descriptions
    api_key = data.get('apiKey')  # Optional
    
    scorer = HybridScorer(user_api_key=api_key)
    results = scorer.score_multiple_jobs(jobs, resume)
    
    return jsonify(results)
```

---

### **Step 5: LinkedIn Integration**
**Priority:** LOW (Week 3)  
**Time Estimate:** 3-4 hours

**Approach:** Manual URL input (no Apify cost)

**Process:**
1. User searches LinkedIn manually
2. User copies search URL
3. User pastes URL into app
4. App extracts jobs from that page

**Implementation:**
```python
def extract_jobs_from_linkedin_url(url):
    """
    Extract job listings from LinkedIn search URL
    
    Returns: List of job objects with:
    - title
    - company
    - location
    - description
    - url
    - date_posted
    """
    
    # Use requests + BeautifulSoup
    # OR use browser automation (Playwright/Selenium)
    # Parse job cards from search results page
    # Extract job details
    # Filter to last 24 hours
    # Return list of jobs
```

**Deduplication:**
```python
def is_duplicate(job, history_csv):
    """
    Check if job already exists in CSV
    
    Match by: job_url (exact match)
    """
    
    df = pd.read_csv(history_csv)
    return job['url'] in df['job_url'].values
```

---

### **Step 6: Deployment**
**Priority:** LOW (Week 4)  
**Time Estimate:** 2-3 hours

**Platform:** Vercel (supports Python + React)

**Steps:**
1. Push code to GitHub
2. Connect Vercel to GitHub repo
3. Configure build settings
4. Deploy

**vercel.json:**
```json
{
  "builds": [
    { "src": "api/*.py", "use": "@vercel/python" },
    { "src": "index.html", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/$1.py" },
    { "src": "/(.*)", "dest": "/$1" }
  ]
}
```

**Environment Variables:**
- Set `GROQ_API_KEY` in Vercel dashboard (for default free tier)
- Users add their own keys via UI

---

## 📊 SUCCESS CRITERIA

### **Week 1 (MVP Core):**
- [ ] Context Analyzer implemented
- [ ] Domain mismatch detection working
- [ ] InvoiceCloud scores <40% (not ~80%)
- [ ] MAE < 10% on Jobscan validation
- [ ] Correlation > 0.85

### **Week 2 (Web App):**
- [ ] Web app deployed and accessible
- [ ] Resume upload working
- [ ] API key input working
- [ ] Results display working
- [ ] CSV export working

### **Week 3 (LinkedIn):**
- [ ] LinkedIn URL extraction working
- [ ] Last 24 hours filter working
- [ ] Deduplication working
- [ ] End-to-end flow: search → extract → score → export

### **Week 4 (Production):**
- [ ] Error handling complete
- [ ] API fallback system working
- [ ] Documentation complete
- [ ] Open source on GitHub
- [ ] Public demo available

---

## 🎯 TARGET USERS

### **Primary:**
1. **Career Switchers** (like Architecture → Tech PM)
   - Need: Domain context understanding
   - Pain: Keyword tools give false positives
   - Solution: Context Analyzer (50% weight)

2. **Job Seekers (General)**
   - Need: Filter noise, focus on quality matches
   - Pain: Too many irrelevant jobs
   - Solution: Intelligent filtering + scoring

3. **Students/Fresh Graduates**
   - Need: Identify entry-level matches
   - Pain: Experience requirements unclear
   - Solution: Seniority level analysis

### **Distribution:**
- Open source GitHub project
- Free tier (100% functional with Groq)
- Optional paid upgrade (user's own Claude API for better accuracy)

---

## 💡 KEY INNOVATIONS

### **1. Context-Aware Scoring (Not Just Keywords)**
**Problem:** Traditional tools miss domain context  
**Solution:** 50% weight on LLM domain analysis

### **2. Relevant Experience (Not Total Experience)**
**Problem:** "8 years PM" doesn't mean "8 years tech PM"  
**Solution:** LLM calculates years in TARGET domain only

### **3. Free-First with Quality**
**Problem:** Free tools are low quality, good tools are expensive  
**Solution:** Free Groq tier (good quality) + optional Claude API (best quality)

### **4. API Flexibility**
**Problem:** Locked into one LLM provider  
**Solution:** User can bring their own API (Groq/Claude/OpenAI) with fallback system

---

## 📝 NEXT ACTIONS

**Immediate (Now):**
1. Build Context Analyzer enhancement
2. Test on Architecture→Tech PM case
3. Validate on 5 Jobscan jobs

**Short-term (This Week):**
1. Adjust scoring weights
2. Build API fallback system
3. Start web interface

**Medium-term (Next 2-3 Weeks):**
1. Complete web app
2. Add LinkedIn integration
3. Deploy to production

**Long-term (Month 2+):**
1. Chrome extension
2. Multi-platform (Indeed, Google Jobs)
3. Advanced features (user accounts, email alerts)

---

## 🔗 REFERENCES

### **Technical:**
- Groq API Docs: https://console.groq.com/docs
- Claude API Docs: https://docs.anthropic.com
- Vercel Deployment: https://vercel.com/docs

### **Validation:**
- Jobscan (baseline): https://jobscan.co
- 5 validated jobs in /mnt/project/Match_Report__Jobscan*.pdf

### **Code Repository:**
- Current code: /home/claude/job_matcher/
- Project files: /mnt/project/

---

## ✅ DECISION LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-24 | Context Analyzer gets 50% weight | Career switchers need domain understanding > keyword matching |
| 2026-04-24 | Groq as default free tier | 1,000 jobs/day free, good quality, no credit card needed |
| 2026-04-24 | CSV storage (not cloud) | Start simple, add cloud later when users onboard |
| 2026-04-24 | Web app (not CLI) | More user-friendly, easier to share |
| 2026-04-24 | LinkedIn first, then Indeed | Validate accuracy on one platform before expanding |
| 2026-04-24 | User brings own API key | Flexibility + cost control for users |

---

**END OF IMPLEMENTATION PLAN**

*This document will be updated as we progress through the build phases.*
