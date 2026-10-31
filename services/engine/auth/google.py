"""Google Identity ID-token verify — real when client id set, else demo stub."""
from __future__ import annotations
import base64
import json
from typing import Optional

import httpx

# Runtime override (Settings / POST /auth/google/client-id); takes precedence when non-empty.
_runtime_client_id: str = ""


def get_effective_client_id(env_client_id: str) -> str:
    rid = (_runtime_client_id or "").strip()
    if rid:
        return rid
    return (env_client_id or "").strip()


def set_runtime_client_id(client_id: str) -> str:
    global _runtime_client_id
    _runtime_client_id = (client_id or "").strip()
    return _runtime_client_id


async def verify_google_credential(
    credential: str,
    client_id: str,
) -> dict:
    """
    Returns {sub, email, name, picture, demo: bool}.
    Without client_id: accepts 'demo' / 'demo:<email>' for local personal use.
    With client_id: verifies via Google tokeninfo endpoint.
    """
    cred = (credential or "").strip()
    effective = (client_id or "").strip()
    if not effective:
        # Demo / stub path — works without OAuth keys
        if cred.lower() in ("demo", "demo-login", ""):
            return {
                "sub": "demo-google-sub",
                "email": "demo@winci.local",
                "name": "Demo Google User",
                "picture": "",
                "demo": True,
            }
        if cred.lower().startswith("demo:"):
            email = cred.split(":", 1)[1].strip() or "demo@winci.local"
            return {
                "sub": f"demo-{email}",
                "email": email,
                "name": email.split("@")[0],
                "picture": "",
                "demo": True,
            }
        # Try decode JWT payload without verify (demo only) for pasted tokens
        try:
            parts = cred.split(".")
            if len(parts) == 3:
                pad = "=" * (-len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
                email = payload.get("email") or "demo@winci.local"
                return {
                    "sub": str(payload.get("sub") or f"demo-{email}"),
                    "email": email,
                    "name": payload.get("name") or email.split("@")[0],
                    "picture": payload.get("picture") or "",
                    "demo": True,
                }
        except Exception:
            pass
        raise ValueError(
            "未設定 GOOGLE_CLIENT_ID：可用 credential 'demo'，或喺 Settings／.env 設定 Web Client ID"
        )

    # Real verification via Google tokeninfo
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": cred},
        )
    if r.status_code != 200:
        raise ValueError("invalid Google credential（token 無效或過期）")
    data = r.json()
    aud = data.get("aud")
    if aud != effective:
        raise ValueError(
            f"Google token audience mismatch（token aud ≠ Client ID）。請確認 App 同引擎用同一個 Web Client ID。"
        )
    if data.get("email_verified") in ("false", False):
        raise ValueError("Google email not verified")
    email = data.get("email")
    sub = data.get("sub")
    if not email or not sub:
        raise ValueError("Google token missing email/sub")
    return {
        "sub": sub,
        "email": email,
        "name": data.get("name") or email.split("@")[0],
        "picture": data.get("picture") or "",
        "demo": False,
    }
