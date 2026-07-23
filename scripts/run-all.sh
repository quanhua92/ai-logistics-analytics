#!/usr/bin/env bash
# Start the ai-logistics-analytics dev stack in the background (nohup).
#
#   FastAPI  →  http://localhost:8000   (log → .dev-logs/backend.log)
#   Next.js  →  http://localhost:3000   (log → .dev-logs/web.log)
#
# Usage:
#   ./scripts/run-all.sh          # start both
#   ./scripts/run-all.sh --stop   # kill both
#   API_PORT=9000 WEB_PORT=4000 ./scripts/run-all.sh
#
# Servers run detached — the script returns immediately.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PROJECT_DIR/server"
WEB_DIR="$PROJECT_DIR/web"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"
MODE="${1:-}"

API_LOG="$PROJECT_DIR/.dev-logs/backend.log"
WEB_LOG="$PROJECT_DIR/.dev-logs/web.log"
mkdir -p "$PROJECT_DIR/.dev-logs"

# ── Stop ─────────────────────────────────────────────────────────────────
# Scoped to OUR ports only (the process LISTENING on the port), never broad
# pkill -f that could touch unrelated uvicorn/next processes on this machine.
if [[ "$MODE" == "--stop" ]]; then
  echo "Stopping dev servers..."
  api_pids="$(lsof -ti ":$API_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$api_pids" ]]; then
    kill $api_pids 2>/dev/null || true
    echo "  ✓ backend stopped (port $API_PORT)"
  else
    echo "  · backend not running on port $API_PORT"
  fi
  web_pids="$(lsof -ti ":$WEB_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$web_pids" ]]; then
    kill $web_pids 2>/dev/null || true
    echo "  ✓ web stopped (port $WEB_PORT)"
  else
    echo "  · web not running on port $WEB_PORT"
  fi
  exit 0
fi

# ── Kill anything already on our ports ───────────────────────────────────
api_pids="$(lsof -ti ":$API_PORT" -sTCP:LISTEN 2>/dev/null || true)"
[[ -n "$api_pids" ]] && kill $api_pids 2>/dev/null || true
web_pids="$(lsof -ti ":$WEB_PORT" -sTCP:LISTEN 2>/dev/null || true)"
[[ -n "$web_pids" ]] && kill $web_pids 2>/dev/null || true
sleep 1

# ── Postgres ─────────────────────────────────────────────────────────────
echo "→ Postgres..."
if docker compose -f "$PROJECT_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up.*healthy"; then
  echo "  · already healthy"
else
  docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d 2>/dev/null \
    && echo "  ✓ started" \
    || echo "  ⚠ could not start (is colima/docker running?)"
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || echo '192.168.1.x')"

# ── Start FastAPI (nohup, background) ────────────────────────────────────
cd "$SERVER_DIR"
nohup uv run uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$API_PORT" \
  >"$API_LOG" 2>&1 &
API_PID=$!

for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$API_PORT/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "  ✓ backend  PID $API_PID  →  http://localhost:$API_PORT  (log: $API_LOG)"

# ── Start Next.js dev (nohup, background) ────────────────────────────────
cd "$WEB_DIR"
nohup pnpm dev --port "$WEB_PORT" >"$WEB_LOG" 2>&1 &
WEB_PID=$!

for i in $(seq 1 30); do
  if curl -sf "http://localhost:$WEB_PORT/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "  ✓ web      PID $WEB_PID  →  http://localhost:$WEB_PORT  (log: $WEB_LOG)"
echo "  ✓ LAN              →  http://$LAN_IP:$WEB_PORT"
echo ""
echo "  Stop: ./scripts/run-all.sh --stop"
echo "  Logs: tail -f $API_LOG  |  tail -f $WEB_LOG"
