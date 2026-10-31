from __future__ import annotations
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.db import UserStore
from auth.jwt_util import decode_access_token
from config import get_settings

_bearer = HTTPBearer(auto_error=False)
_store: Optional[UserStore] = None


def get_store() -> UserStore:
    global _store
    if _store is None:
        settings = get_settings()
        _store = UserStore(getattr(settings, "WINCI_AUTH_DB", None) or None)
    return _store


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    if not creds or not creds.credentials:
        return None
    settings = get_settings()
    payload = decode_access_token(creds.credentials, settings.JWT_SECRET)
    if not payload or "sub" not in payload:
        return None
    try:
        uid = int(payload["sub"])
    except (TypeError, ValueError):
        return None
    user = get_store().get_by_id(uid)
    return UserStore.public(user) if user else None


def get_current_user(user: Optional[dict] = Depends(get_optional_user)) -> dict:
    if not user:
        raise HTTPException(401, "unauthorized")
    return user
