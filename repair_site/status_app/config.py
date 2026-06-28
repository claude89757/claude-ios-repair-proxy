from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    admin_username: str
    admin_password_hash: str
    invite_secret: str
    status_token_secret: str
    internal_api_secret: str
    database_path: str
    proxy_port_start: int = 10001
    proxy_port_end: int = 10999
    invite_default_ttl_seconds: int = 86400
    public_invite_ttl_seconds: int = 3600


def load_settings() -> Settings:
    return Settings(
        admin_username=os.getenv("ADMIN_USERNAME", "admin"),
        admin_password_hash=os.getenv("ADMIN_PASSWORD_HASH", ""),
        invite_secret=os.getenv("INVITE_SECRET", ""),
        status_token_secret=os.getenv("STATUS_TOKEN_SECRET", ""),
        internal_api_secret=os.getenv("INTERNAL_API_SECRET", ""),
        database_path=os.getenv(
            "INVITE_DATABASE_PATH",
            "/opt/claude-ios-repair/data/invites.sqlite3",
        ),
        proxy_port_start=int(os.getenv("PROXY_PORT_START", "10001")),
        proxy_port_end=int(os.getenv("PROXY_PORT_END", "10999")),
        invite_default_ttl_seconds=int(os.getenv("INVITE_DEFAULT_TTL_SECONDS", "86400")),
        public_invite_ttl_seconds=int(os.getenv("PUBLIC_INVITE_TTL_SECONDS", "3600")),
    )


def require_configured(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "ADMIN_PASSWORD_HASH": settings.admin_password_hash,
            "INVITE_SECRET": settings.invite_secret,
            "STATUS_TOKEN_SECRET": settings.status_token_secret,
            "INTERNAL_API_SECRET": settings.internal_api_secret,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError("Missing required settings: " + ", ".join(missing))


def sha256_password_hash(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return "sha256:" + digest


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def pbkdf2_password_hash(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int = 260_000,
) -> str:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${_b64encode(salt)}${_b64encode(digest)}"


def verify_admin_password(password: str, settings: Settings) -> bool:
    expected = settings.admin_password_hash
    if expected.startswith("sha256:"):
        actual = sha256_password_hash(password)
        return hmac.compare_digest(actual, expected)
    if expected.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_b64, digest_b64 = expected.split("$", 3)
            salt = _b64decode(salt_b64)
            expected_digest = _b64decode(digest_b64)
            actual_digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations),
            )
        except Exception:
            return False
        return hmac.compare_digest(actual_digest, expected_digest)
    return False


def _require_secret(secret: str) -> None:
    if not secret:
        raise ValueError("secret must not be empty")


def _urlsafe_digest(message: str, secret: str, length: int = 32) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")[:length]


def derive_proxy_password(proxy_username: str, *, version: int, secret: str) -> str:
    _require_secret(secret)
    return _urlsafe_digest(f"proxy:{version}:{proxy_username}", secret, length=28)


def _random_chars(alphabet: str, length: int, *, token_size: int) -> str:
    chars: list[str] = []
    while len(chars) < length:
        chars.extend(char for char in secrets.token_urlsafe(token_size) if char in alphabet)
    return "".join(chars[:length])


def new_invite_code() -> str:
    return "INV-" + _random_chars("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 12, token_size=12).upper()


def new_session_id() -> str:
    return "sess_" + secrets.token_urlsafe(18)


def new_proxy_username() -> str:
    return "repair_" + _random_chars("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 10, token_size=10).lower()


def sign_status_token(session_id: str, *, secret: str, ttl_seconds: int = 3600) -> str:
    _require_secret(secret)
    payload_data = {
        "purpose": "status",
        "session_id": session_id,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_json = json.dumps(payload_data, separators=(",", ":"), sort_keys=True)
    payload = _b64encode(payload_json.encode("utf-8"))
    signature = _urlsafe_digest(payload, secret, length=32)
    return payload + "." + signature


def verify_status_token(token: str, *, secret: str) -> str | None:
    if not secret:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    payload, signature = parts
    expected = _urlsafe_digest(payload, secret, length=32)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload_data = json.loads(_b64decode(payload).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload_data, dict):
        return None
    if payload_data.get("purpose") != "status":
        return None
    exp = payload_data.get("exp")
    if not isinstance(exp, int):
        return None
    if exp < int(time.time()):
        return None
    session_id = payload_data.get("session_id")
    if not isinstance(session_id, str):
        return None
    return session_id
