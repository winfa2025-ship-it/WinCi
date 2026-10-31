#!/usr/bin/env bash
# Deploy WinCi engine to the SiteMix Vultr box (same host as sitemixhk.com).
# Usage:  bash deploy/deploy.sh
# Keeps /opt/winci/.env and /opt/winci/data/ on the server.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${SITEMIX_HOST:-root@45.76.119.43}"
KEY="${SITEMIX_KEY:-$HOME/.ssh/sitemix_vultr}"
SSH=(ssh -i "$KEY" -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new)
RSYNC_SSH="ssh -i $KEY -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new"

echo "==> Ensure user + dirs on $HOST"
"${SSH[@]}" "$HOST" 'set -e
  id -u winci >/dev/null 2>&1 || useradd --system --home /opt/winci --shell /usr/sbin/nologin winci
  mkdir -p /opt/winci/app /opt/winci/data
  if [ ! -f /opt/winci/.env ]; then
    JWT=$(openssl rand -hex 32)
    cat > /opt/winci/.env <<ENVEOF
MODE=paper
JWT_SECRET=${JWT}
ENGINE_HOST=127.0.0.1
ENGINE_PORT=8787
WINCI_AUTH_DB=/opt/winci/data/winci_users.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://localhost,capacitor://localhost,http://localhost,https://sitemixhk.com,http://sitemixhk.com
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false
BINANCE_WHITELIST_IPS=
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
GOOGLE_CLIENT_ID=
MIN_NOTIONAL_USD=1
MAX_POSITION_USD=500
DAILY_LOSS_LIMIT_USD=50
PAPER_STARTING_USDT=10000
ENVEOF
    chmod 600 /opt/winci/.env
    echo "created /opt/winci/.env"
  else
    echo "keeping existing /opt/winci/.env"
  fi
  chown -R winci:winci /opt/winci
'

echo "==> Sync engine code"
rsync -az --delete -e "$RSYNC_SSH" \
  --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' --exclude '.env' --exclude 'data/' \
  "$ROOT/services/engine/" "$HOST:/opt/winci/app/"

echo "==> Install venv + systemd unit"
"${SSH[@]}" "$HOST" 'set -e
  chown -R winci:winci /opt/winci
  if [ ! -d /opt/winci/venv ]; then
    sudo -u winci -H python3 -m venv /opt/winci/venv
  fi
  sudo -u winci -H /opt/winci/venv/bin/pip install -q --upgrade pip
  sudo -u winci -H /opt/winci/venv/bin/pip install -q -r /opt/winci/app/requirements.txt
'

# Copy unit from local deploy folder
scp -i "$KEY" -o ConnectTimeout=20 "$ROOT/deploy/winci.service" "$HOST:/etc/systemd/system/winci.service"

echo "==> Patch Caddyfile for /winci-api (idempotent)"
"${SSH[@]}" "$HOST" 'python3 - <<'"'"'PY'"'"'
from pathlib import Path
path = Path("/etc/caddy/Caddyfile")
text = path.read_text()
marker = "handle_path /winci-api/*"
if marker in text:
    print("Caddyfile already has /winci-api")
else:
    old = """sitemixhk.com {
	encode zstd gzip
	reverse_proxy 127.0.0.1:8080
}"""
    new = """sitemixhk.com {
	encode zstd gzip
	handle_path /winci-api/* {
		reverse_proxy 127.0.0.1:8787
	}
	handle {
		reverse_proxy 127.0.0.1:8080
	}
}"""
    if old not in text:
        raise SystemExit("unexpected Caddyfile; aborting to protect SiteMix")
    path.write_text(text.replace(old, new, 1))
    print("patched sitemixhk.com block")
PY
  caddy validate --config /etc/caddy/Caddyfile
  systemctl daemon-reload
  systemctl enable winci
  systemctl restart winci
  sleep 2
  systemctl is-active winci
  systemctl reload caddy
  sleep 1
  curl -fsS http://127.0.0.1:8787/health
  echo
  curl -fsS -o /dev/null -w "local sitemix /api/config -> %{http_code}\n" http://127.0.0.1:8080/api/config
'

echo "==> Public smoke"
curl -fsS "https://sitemixhk.com/winci-api/health" || true
echo
echo "==> Done. Engine URL: https://sitemixhk.com/winci-api"
