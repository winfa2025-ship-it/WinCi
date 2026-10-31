"""SQLite users table for personal-use auth."""
from __future__ import annotations
import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Optional

DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "winci_users.db"


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return salt, dk.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, h = _hash_password(password, salt)
    return secrets.compare_digest(h, password_hash)


class UserStore:
    def __init__(self, db_path: Optional[str] = None):
        path = Path(db_path or os.environ.get("WINCI_AUTH_DB", str(DEFAULT_DB)))
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.path))
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_salt TEXT,
                    password_hash TEXT,
                    display_name TEXT,
                    provider TEXT NOT NULL DEFAULT 'email',
                    google_sub TEXT UNIQUE,
                    created_at REAL NOT NULL
                )
                """
            )
            c.commit()

    def get_by_email(self, email: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)).fetchone()
            return dict(row) if row else None

    def get_by_id(self, user_id: int) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def get_by_google_sub(self, sub: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM users WHERE google_sub = ?", (sub,)).fetchone()
            return dict(row) if row else None

    def create_email(self, email: str, password: str, display_name: str = "") -> dict:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("invalid email")
        if len(password) < 6:
            raise ValueError("password min 6 chars")
        if self.get_by_email(email):
            raise ValueError("email already registered")
        salt, pw_hash = _hash_password(password)
        now = time.time()
        with self._conn() as c:
            cur = c.execute(
                """
                INSERT INTO users (email, password_salt, password_hash, display_name, provider, created_at)
                VALUES (?, ?, ?, ?, 'email', ?)
                """,
                (email, salt, pw_hash, display_name or email.split("@")[0], now),
            )
            c.commit()
            uid = cur.lastrowid
        return self.get_by_id(uid)  # type: ignore

    def create_or_get_google(self, sub: str, email: str, display_name: str = "") -> dict:
        existing = self.get_by_google_sub(sub)
        if existing:
            return existing
        by_email = self.get_by_email(email)
        if by_email:
            with self._conn() as c:
                c.execute(
                    "UPDATE users SET google_sub = ?, provider = CASE WHEN provider='email' THEN 'email+google' ELSE provider END, display_name = COALESCE(NULLIF(?, ''), display_name) WHERE id = ?",
                    (sub, display_name, by_email["id"]),
                )
                c.commit()
            return self.get_by_id(by_email["id"])  # type: ignore
        email = email.strip().lower()
        now = time.time()
        with self._conn() as c:
            cur = c.execute(
                """
                INSERT INTO users (email, display_name, provider, google_sub, created_at)
                VALUES (?, ?, 'google', ?, ?)
                """,
                (email, display_name or email.split("@")[0], sub, now),
            )
            c.commit()
            uid = cur.lastrowid
        return self.get_by_id(uid)  # type: ignore

    @staticmethod
    def public(user: dict) -> dict:
        return {
            "id": user["id"],
            "email": user["email"],
            "displayName": user.get("display_name") or "",
            "provider": user.get("provider") or "email",
        }
