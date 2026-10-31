# Hosted WinCi engine (personal)

Live URL (SiteMix Vultr / Caddy):

`https://sitemixhk.com/winci-api`

- Path prefix stripped by Caddy (`handle_path`) → FastAPI sees `/health`, `/auth`, `/api/...`
- systemd: `winci.service` (user `winci`, listen `127.0.0.1:8787`)
- Data: `/opt/winci/data/winci_users.db` · secrets: `/opt/winci/.env` (not in git)
- Redeploy engine: `bash deploy/deploy.sh` from the WinCi repo on the build box
- Android APK defaults `VITE_API_BASE` to this URL

Smoke:

```bash
curl -fsS https://sitemixhk.com/winci-api/health
curl -fsS -X POST https://sitemixhk.com/winci-api/auth/google -H 'content-type: application/json' -d '{"credential":"demo"}'
```
