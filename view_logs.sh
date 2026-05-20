#!/bin/bash
# view_logs.sh - View Flask logs in real-time with colours

cd "$(dirname "$0")/logs" 2>/dev/null || { echo "logs/ not found"; exit 1; }

echo "=== FLASK LOGS (Ctrl+C to stop) ==="
echo ""

tail -f flask_app.log job_searches.log platform_filter.log 2>/dev/null | \
    sed 's/\[INFO\]/\x1b[32m[INFO]\x1b[0m/g' | \
    sed 's/\[WARNING\]/\x1b[33m[WARNING]\x1b[0m/g' | \
    sed 's/\[ERROR\]/\x1b[31m[ERROR]\x1b[0m/g'
