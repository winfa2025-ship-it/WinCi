#!/usr/bin/env bash
# One-click local desktop run for WinCi (engine + web). Not an Android installer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then cp .env.example .env; fi

echo "[WinCi] Starting engine on :8787 …"
cd "$ROOT/services/engine"
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8787 &
ENGINE_PID=$!
trap 'kill $ENGINE_PID 2>/dev/null || true' EXIT

cd "$ROOT/apps/web"
if [[ ! -d node_modules ]]; then npm install; fi
echo "[WinCi] Web UI → http://127.0.0.1:5173"
echo "[WinCi] PWA: Chrome 選單 → 安裝應用程式／加到主畫面"
npm run dev -- --host 127.0.0.1 --port 5173
