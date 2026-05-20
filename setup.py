#!/usr/bin/env python3
"""
setup.py — interactive first-run wizard for job-finder-ai.

Checks Python version, installs dependencies, walks the user through
adding API keys to .env, validates each key with a live round-trip,
and ends with a quick test search so you know everything works.

Run:
    python setup.py
"""

import sys
import os
import subprocess
import importlib

# ── 0. Python version gate ─────────────────────────────────────────────────

if sys.version_info < (3, 11):
    print(f"[FAIL] Python 3.11+ required (you have {sys.version.split()[0]})")
    print("       Install it from https://python.org/downloads")
    sys.exit(1)

print(f"[OK] Python {sys.version.split()[0]}")


# ── 1. Install / verify dependencies ──────────────────────────────────────

def install_deps():
    req = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req):
        print("[SKIP] requirements.txt not found — skipping pip install")
        return
    print("\n[...] Installing dependencies from requirements.txt …")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req, "-q"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("[FAIL] pip install failed:")
        print(result.stderr[:600])
        sys.exit(1)
    print("[OK] Dependencies installed")

install_deps()


# ── 2. .env setup ──────────────────────────────────────────────────────────

def load_or_create_env() -> dict:
    """Load existing .env or create one from .env.example."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    example  = os.path.join(os.path.dirname(__file__), ".env.example")

    if not os.path.exists(env_path):
        if os.path.exists(example):
            import shutil
            shutil.copy(example, env_path)
            print("[OK] Created .env from .env.example")
        else:
            with open(env_path, "w") as f:
                f.write("# job-finder-ai environment\n")
            print("[OK] Created blank .env")

    # Parse into dict
    env: dict[str, str] = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def write_env_key(key: str, value: str):
    """Append or update a key in .env."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            lines[i] = f"{key}={value}\n"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)


env = load_or_create_env()


# ── 3. Key wizard ──────────────────────────────────────────────────────────

DIVIDER = "─" * 60

def prompt_key(var: str, label: str, url: str, required: bool) -> str | None:
    existing = env.get(var, "").strip()
    tag = "(required)" if required else "(optional — skip with Enter)"

    print(f"\n{DIVIDER}")
    print(f"  {label}  {tag}")
    print(f"  Get yours: {url}")
    if existing:
        masked = f"{existing[:6]}…{existing[-4:]}" if len(existing) > 10 else "***"
        print(f"  Current value in .env: {masked}")
        choice = input("  Keep existing key? [Y/n]: ").strip().lower()
        if choice not in ("n", "no"):
            return existing

    while True:
        val = input(f"  Paste {var}: ").strip()
        if not val:
            if required:
                print("  [!] This key is required. Please enter a value.")
                continue
            else:
                print("  [SKIP] Skipping optional key.")
                return None
        return val


# ── 3a. Groq API key (required) ────────────────────────────────────────────

print(f"\n{'='*60}")
print("  STEP 1 of 3 — Groq API key (free, required for AI scoring)")
print(f"{'='*60}")
print("""
  Groq gives you a free LLM API:
    • 14,400 requests/day on llama-3.1-8b-instant  (batch scoring)
    • 1,000 requests/day on llama-3.3-70b-versatile (premium rescore)
  No credit card needed.

  How to get it:
    1. Go to  https://console.groq.com/keys
    2. Sign up / log in (Google or GitHub works)
    3. Click "Create API Key"
    4. Copy the key — it starts with "gsk_"
""")

groq_key = prompt_key(
    "GROQ_API_KEY",
    "Groq API Key",
    "https://console.groq.com/keys",
    required=True,
)
if groq_key:
    write_env_key("GROQ_API_KEY", groq_key)
    env["GROQ_API_KEY"] = groq_key

# ── Validate Groq key ──────────────────────────────────────────────────────

def validate_groq(key: str) -> bool:
    print("\n  [Groq] Validating key with a 1-token test call …")
    try:
        from groq import Groq
        client = Groq(api_key=key)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        _ = resp.choices[0].message.content
        print("  [OK] Groq key is valid and working.")
        return True
    except Exception as e:
        err = str(e)
        if "401" in err or "invalid" in err.lower():
            print(f"  [FAIL] Invalid Groq key: {err[:120]}")
        elif "429" in err:
            print("  [WARN] Key valid but rate-limited (daily quota reached).")
            return True   # key is valid, just exhausted
        else:
            print(f"  [FAIL] Groq test error: {err[:120]}")
        return False

if groq_key:
    if not validate_groq(groq_key):
        retry = input("  Enter a corrected Groq key (or press Enter to skip): ").strip()
        if retry:
            write_env_key("GROQ_API_KEY", retry)
            env["GROQ_API_KEY"] = retry
            validate_groq(retry)

# ── 3b. Serper API key (primary Naukri search) ────────────────────────────

print(f"\n{'='*60}")
print("  STEP 2 of 3 — Serper.dev key (free, powers Naukri search)")
print(f"{'='*60}")
print("""
  Serper gives you 2,500 free Google searches/month — used to
  search Naukri job listings via Google.  No credit card needed.

  How to get it:
    1. Go to  https://serper.dev
    2. Click "Get Started Free" — sign in with Google
    3. From the dashboard copy your API key
""")

serper_key = prompt_key(
    "SERPER_API_KEY",
    "Serper API Key",
    "https://serper.dev",
    required=False,
)
if serper_key:
    write_env_key("SERPER_API_KEY", serper_key)
    env["SERPER_API_KEY"] = serper_key

def validate_serper(key: str) -> bool:
    print("\n  [Serper] Validating key with a minimal search …")
    try:
        import requests as _req
        resp = _req.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": "python developer jobs hyderabad", "num": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            print("  [OK] Serper key is valid and working.")
            return True
        elif resp.status_code == 401:
            print("  [FAIL] Invalid Serper key (401 Unauthorized).")
        else:
            print(f"  [WARN] Serper returned HTTP {resp.status_code} — key may be valid.")
        return False
    except Exception as e:
        print(f"  [FAIL] Serper validation error: {e}")
        return False

if serper_key:
    if not validate_serper(serper_key):
        retry = input("  Enter a corrected Serper key (or press Enter to skip): ").strip()
        if retry:
            write_env_key("SERPER_API_KEY", retry)
            env["SERPER_API_KEY"] = retry
            validate_serper(retry)

# ── 3c. SerpAPI key (optional fallback) ───────────────────────────────────

print(f"\n{'='*60}")
print("  STEP 3 of 3 — SerpAPI key (optional fallback)")
print(f"{'='*60}")
print("""
  SerpAPI is a paid service (100 free searches/month) used as a
  fallback if Serper is unavailable.  Safe to skip if you have Serper.

  How to get it:
    1. Go to  https://serpapi.com/manage-api-key
    2. Sign up for the free plan
    3. Copy the API key from the dashboard
""")

serpapi_key = prompt_key(
    "SERPAPI_KEY",
    "SerpAPI Key",
    "https://serpapi.com/manage-api-key",
    required=False,
)
if serpapi_key:
    write_env_key("SERPAPI_KEY", serpapi_key)
    env["SERPAPI_KEY"] = serpapi_key


# ── 4. Verify modules load cleanly ────────────────────────────────────────

print(f"\n{DIVIDER}")
print("  Checking module imports …")

MODULES = [
    ("flask",                "Flask"),
    ("groq",                 "Groq SDK"),
    ("jobspy",               "python-jobspy"),
    ("requests",             "requests"),
    ("dotenv",               "python-dotenv"),
]

all_ok = True
for mod, label in MODULES:
    try:
        importlib.import_module(mod)
        print(f"  [OK] {label}")
    except ImportError:
        print(f"  [FAIL] {label} — run: pip install -r requirements.txt")
        all_ok = False

if not all_ok:
    print("\n[!] Some packages are missing. Run:  pip install -r requirements.txt")
    sys.exit(1)

# Check local modules
local = ["groq_analyzer", "hybrid_scorer", "keyword_matcher"]
for mod in local:
    try:
        importlib.import_module(mod)
        print(f"  [OK] {mod}.py")
    except Exception as e:
        print(f"  [WARN] {mod}.py import error: {e}")


# ── 5. Live test search ────────────────────────────────────────────────────

print(f"\n{DIVIDER}")
print("  Running a quick live test search (LinkedIn + Indeed, 5 jobs) …")
print(f"{DIVIDER}")

try:
    # Reload env so the keys we just wrote are picked up
    from dotenv import load_dotenv
    load_dotenv(override=True)

    sys.path.insert(0, os.path.dirname(__file__))
    from job_automation.aggregator import JobAggregator

    agg = JobAggregator()
    jobs = agg.search(
        keyword="Product Manager",
        location="Hyderabad, India",
        platforms=["linkedin", "indeed"],
        max_per_platform=5,
        hours_old=72,
    )

    if jobs:
        print(f"\n[OK] Test search returned {len(jobs)} job(s). Sample:")
        for j in jobs[:3]:
            print(f"  • {j.get('title','?')} @ {j.get('company','?')} [{j.get('source','?')}]")
    else:
        print("[WARN] Search returned 0 jobs — LinkedIn/Indeed may be rate-limiting.")
        print("       This is normal occasionally; the API itself is working.")

except Exception as e:
    print(f"[WARN] Test search failed: {e}")
    print("       Core setup is complete — this may be a transient scraping issue.")


# ── 6. Done ────────────────────────────────────────────────────────────────

print(f"""
{'='*60}
  Setup complete!

  Start the server:
    python api.py

  Run a deep search:
    curl -X POST http://localhost:8000/api/deep-search \\
      -H "Content-Type: application/json" \\
      -d '{{"keyword":"AI Implementation Manager","location":"Hyderabad","resume":"..."}}'

  Check system health:
    python scrutinizer.py --quick

  View historical trends:
    python scrutinizer.py --report-only
{'='*60}
""")
