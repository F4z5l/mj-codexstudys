#!/bin/bash
# ─────────────────────────────────────────────
# start.sh  –  API + Bot dono ek saath chalao
# ─────────────────────────────────────────────

# .env load karo agar exist karta hai
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "[START] .env loaded"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Sachin Academy API v3 + Bot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Bot background mein chalao
echo "[START] Starting Telegram Bot..."
python bot.py &
BOT_PID=$!
echo "[START] Bot PID: $BOT_PID"

# API start karo
echo "[START] Starting FastAPI on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Agar API band ho to bot bhi band karo
kill $BOT_PID 2>/dev/null
