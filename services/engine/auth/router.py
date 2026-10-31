"""Auth HTTP routes: register / login / google / me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.db import UserStore
from auth.deps import get_current_user, get_store
from auth.google import verify_google_credential
from auth.jwt_util import create_access_token
from config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    display_name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class GoogleIn(BaseModel):
    credential: str = "demo"  # Google ID token, or "demo" when no client id


def _token_for(user: dict) -> dict:
    settings = get_settings()
    token = create_access_token(
        {"sub": str(user["id"]), "email": user["email"]},
        settings.JWT_SECRET,
    )
    return {"accessToken": token, "tokenType": "bearer", "user": UserStore.public(user)}


@router.post("/register")
def register(body: RegisterIn, store: UserStore = Depends(get_store)):
    try:
        user = store.create_email(body.email, body.password, body.display_name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _token_for(user)


@router.post("/login")
def login(body: LoginIn, store: UserStore = Depends(get_store)):
    from auth.db import verify_password

    user = store.get_by_email(body.email)
    if not user or not user.get("password_hash"):
        raise HTTPException(401, "invalid email or password")
    if not verify_password(body.password, user["password_salt"], user["password_hash"]):
        raise HTTPException(401, "invalid email or password")
    return _token_for(user)


@router.post("/google")
async def google_login(body: GoogleIn, store: UserStore = Depends(get_store)):
    settings = get_settings()
    try:
        info = await verify_google_credential(body.credential, settings.GOOGLE_CLIENT_ID)
    except ValueError as e:
        raise HTTPException(400, str(e))
    user = store.create_or_get_google(info["sub"], info["email"], info.get("name") or "")
    out = _token_for(user)
    out["demo"] = bool(info.get("demo"))
    out["googleConfigured"] = bool(settings.GOOGLE_CLIENT_ID)
    return out


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    settings = get_settings()
    return {
        **user,
        "googleConfigured": bool(settings.GOOGLE_CLIENT_ID),
    }


@router.get("/google/status")
def google_status():
    settings = get_settings()
    return {
        "configured": bool(settings.GOOGLE_CLIENT_ID),
        "clientIdPresent": bool(settings.GOOGLE_CLIENT_ID),
        "demoAvailable": True,
        "note": "Set GOOGLE_CLIENT_ID for real Google Identity; without it use Demo Google login.",
    }
