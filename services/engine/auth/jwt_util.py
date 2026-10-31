"""Minimal HS256 JWT helpers (PyJWT)."""
from __future__ import annotations
import time
from typing import Any, Optional

import jwt

ALGORITHM = "HS256"
DEFAULT_TTL_SEC = 60 * 60 * 24 * 14  # 14 days


def create_access_token(payload: dict, secret: str, ttl_sec: int = DEFAULT_TTL_SEC) -> str:
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + ttl_sec}
    return jwt.encode(body, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, secret: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
