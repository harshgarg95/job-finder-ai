# Setup Guide for New Users
## AI Job Matcher - Get Started in 5 Minutes

**Welcome!** This guide helps you set up the AI Job Matcher with your own FREE API keys.

---

## 📋 **PREREQUISITES**

Before running the app, you need 3 free API keys:

| API | Purpose | Free Tier | Sign Up Link |
|-----|---------|-----------|--------------|
| **Serper.dev** | Job search | 2,500 searches/month | https://serper.dev |
| **Groq** | AI job scoring | 1,000 requests/day | https://console.groq.com |
| **SerpAPI** (Optional backup) | Fallback job search | 250 searches/month | https://serpapi.com |

**Total Cost: $0/month** ✅

---

## 🚀 **STEP-BY-STEP SETUP**

### **Step 1: Clone the Repository** (2 minutes)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/job-finder-ai.git
cd job-finder-ai

# Install dependencies
pip install -r requirements.txt --break-system-packages
```

---

### **Step 2: Get Your API Keys** (5 minutes)

#### **A. Serper.dev (Primary Job Search)**
1. Go to https://serper.dev
2. Click "Get Started Free"
3. Sign up with Google/GitHub
4. Go to Dashboard → Copy your API key
5. **Save it somewhere** (you'll need it in Step 3)

**Free tier:** 2,500 searches/month (no credit card required!)

---

#### **B. Groq (AI Scoring)**
1. Go to https://console.groq.com
2. Sign up with email
3. Go to API Keys section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)
6. **Save it somewhere**

**Free tier:** 1,000 requests/day (30,000/month!)

---

#### **C. SerpAPI (Optional Backup)**
1. Go to https://serpapi.com
2. Click "Get Started"
3. Sign up with email
4. Go to Dashboard → Copy your API key
5. **Save it somewhere**

**Free tier:** 250 searches/month (used only if Serper fails)

---

### **Step 3: Configure Environment Variables** (1 minute)

Create a `.env` file in the project root:

```bash
# In the job-finder-ai directory
touch .env
```

Add your API keys to `.env`:

```bash
# REQUIRED: Primary job search
SERPER_API_KEY=your_serper_key_here

# REQUIRED: AI job scoring
GROQ_API_KEY=your_groq_key_here

# OPTIONAL: Backup job search
SERPAPI_KEY=your_serpapi_key_here
```

**IMPORTANT:** 
- Replace `your_serper_key_here` with your actual Serper API key
- Replace `your_groq_key_here` with your actual Groq API key
- The `.env` file is already in `.gitignore` (won't be committed to GitHub)

---

### **Step 4: Run the App** (1 minute)

```bash
# Start the server
PORT=8000 python api.py
```

Open your browser: **http://localhost:8000**

---

## ✅ **VERIFY IT WORKS**

**Test the setup:**
1. Upload your resume
2. Click "Suggest Job Titles" → Should return 5-10 titles
3. Select 2-3 titles
4. Click "Find & Score Jobs Automatically"
5. Should find 20-30 jobs and score them

**If it works:** ✅ You're ready to go!

**If it fails:** See troubleshooting below ⬇️

---

## 🐛 **TROUBLESHOOTING**

### **Error: "No API key found"**
**Fix:** Check `.env` file exists and has correct format (no spaces around `=`)

### **Error: "Invalid API key"**
**Fix:** Copy-paste keys again from dashboards (no extra spaces)

### **Error: "No jobs found"**
**Fix:** 
- Check Serper API key is valid
- Try different job titles
- Check your usage limits on Serper dashboard

### **Error: "Scoring failed"**
**Fix:**
- Check Groq API key is valid
- Check Groq usage limits (1000/day)
- Try again in a few minutes

---

## 📊 **MONITOR YOUR USAGE**

**Track your API usage to stay within free tiers:**

**Serper.dev Dashboard:** https://serper.dev/dashboard
- Shows: X / 2,500 searches used
- Resets: Monthly

**Groq Dashboard:** https://console.groq.com
- Shows: X / 1,000 requests used (daily)
- Resets: Every 24 hours

**SerpAPI Dashboard:** https://serpapi.com/manage-api-key
- Shows: X / 250 searches used
- Resets: Monthly

---

## 🎯 **DAILY USAGE ESTIMATES**

**Light user (1 search/day):**
- 3 job titles × 10 jobs each = 3 searches
- Monthly: 90 searches (3.6% of free tier) ✅

**Power user (5 searches/day):**
- 15 searches/day
- Monthly: 450 searches (18% of free tier) ✅

**You can support ~25 daily active users before hitting limits!**

---

## 🔒 **SECURITY BEST PRACTICES**

1. ✅ **Never commit `.env` file** (already in .gitignore)
2. ✅ **Don't share API keys** in screenshots or public repos
3. ✅ **Rotate keys** if accidentally exposed
4. ✅ **Use separate keys** for dev vs production

---

## 📞 **NEED HELP?**

**Common issues:**
- API key format wrong → Check for spaces/typos
- Rate limits hit → Check dashboards for usage
- Dependencies missing → Run `pip install -r requirements.txt --break-system-packages`

**Still stuck?** Open an issue on GitHub with:
- Error message
- Steps you followed
- Which API is failing

---

## 🎉 **YOU'RE ALL SET!**

You now have a **FREE, AI-powered job matcher** that:
- ✅ Searches 2,500+ jobs per month automatically
- ✅ Scores jobs with domain-aware AI analysis
- ✅ Finds matches across LinkedIn, Indeed, Naukri
- ✅ Costs $0 to run

**Happy job hunting!** 🚀

---

END OF SETUP GUIDE
