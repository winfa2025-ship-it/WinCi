"""Google Identity ID-token verify — real when GOOGLE_CLIENT_ID set, else demo stub."""
from __future__ import annotations
import base64
import json
from typing import Optional

import httpx


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
    if not client_id:
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
        raise ValueError("demo mode: use credential 'demo' or set GOOGLE_CLIENT_ID")

    # Real verification via Google tokeninfo
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": cred},
        )
    if r.status_code != 200:
        raise ValueError("invalid Google credential")
    data = r.json()
    aud = data.get("aud")
    if aud != client_id:
        raise ValueError("Google token audience mismatch")
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
