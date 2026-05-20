# Flask Process Location Report

## Process Information

| Field | Details |
|-------|---------|
| Parent PID | 29970 |
| Child PID | 82356 (active worker) |
| Running since | 1:05 AM (parent), ~21h 37m uptime |
| Working directory | `/Users/harshgarg/Desktop/job-finder-ai` |
| Command | `python api.py` |
| Port | 8000 (`*:irdmi`) |
| Python binary | `/opt/anaconda3/bin/python3.13` (parent) / `/opt/anaconda3/bin/python` (child) |

## Terminal Location

- **Running in:** Background (no controlling terminal — `PPID=1` for parent)
- **Session ID:** N/A — launched as a background daemon (not in screen or tmux)
- **Screen sessions:** None
- **Tmux:** Not installed
- **Output going to:** An unlinked (deleted) temp file from a prior Claude Code session:
  `/private/tmp/claude-501/.../tasks/bk620rroo.output`
  (inode 25050529 — file was deleted from disk but still open by PID 82356)

> **This means Flask output is currently being swallowed into an inaccessible deleted file.**

## Log Files Found

- No `.log` files in `/Users/harshgarg/Desktop/job-finder-ai/`
- Flask has **no file-based logging** configured

## Recent Activity

| File | Details |
|------|---------|
| `/Users/harshgarg/Downloads/job_matches_2026-05-06.csv` | Exported today (2026-05-06), 11 rows |
| `jobs_to_verify.csv` | 17 jobs pending manual review |

### Top Matches from Today's Export (job_matches_2026-05-06.csv)

| Score | Title | Company | Type |
|-------|-------|---------|------|
| 78.3 | Specialist Master-Data Architect | Nameless | Hybrid |
| 73.5 | AI Consulting Governance & Strategy Specialist | TELUS Digital AI | Remote |
| 70.0 | Principal AI Architect – AI Platform | Triadique Technologies | On-site |
| 70.0 | Architect, AI Cloud Platform | Oxmiq Labs | On-site |
| 70.0 | Senior Customer Success Partner | Turing | Remote |
| 64.2 | Senior Product Data Manager | Celigo | Hybrid |
| 60.0 | Product Manager, Trip Quality Data | Zoom | Remote |
| 58.6 | AI/ML Architect (GenAI / Databricks / Snowflake) | Spatial Alphabet | Remote |

### Jobs to Verify (jobs_to_verify.csv) — High Context Score (90) Picks

| Score | Title | Company | Rec |
|-------|-------|---------|-----|
| 61.6 | Agentic AI Project Manager | Spysr Services | Review |
| 56.5 | Principal Product Manager | Adobe | Review |
| 55.0 | Project Leader, Data & AI Solutions | Straive | Review |
| 53.4 | Project Manager – AI Initiatives | Talentmatics | Review |
| 53.4 | Program Manager - AI Consulting Services | Sirius AI | Review |

## How to Access Live Logs

Flask output is currently lost to a deleted temp file. To restore logging, restart with a log file:

```bash
cd ~/Desktop/job-finder-ai

# Kill old processes
kill 29970

# Restart with logging
python api.py > flask_output.log 2>&1 &

# Tail live output
tail -f flask_output.log
```

Or add logging directly in `api.py`:
```python
import logging
logging.basicConfig(
    filename='flask.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
```
