# Invite Admin Dynamic Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the shared `default` repair status with invite-based user flows and an administrator invite management page.

**Architecture:** Keep a single public repair proxy on `9443`; generate one proxy username/password per invite; authenticate proxy requests in the mitmproxy addon; map authenticated proxy usernames to internal `session_id` values; expose user status only after invite claim. Store invites in SQLite and keep sanitized live events in memory.

**Tech Stack:** Python standard library SQLite, FastAPI, static HTML/CSS/JavaScript, mitmproxy addon hooks `http_connect` and `requestheaders`, pytest, Docker/systemd deployment.

---

## Repository Notes

`/Users/claude89757/Desktop/cc` is not currently a git repository. Replace commit steps with checkpoint commands. Do not expose values from `sg_proxy.txt` in code, docs, tests, or terminal summaries.

Production currently has:

```text
443   Nginx public website
8080  existing direct HTTP proxy
8443  existing WARP HTTPS proxy
9443  Claude iOS repair proxy
9000  local FastAPI backend
```

Do not change public ports for this feature.

## File Structure

- `repair_site/status_app/config.py`  
  Environment-backed settings, admin password hash verification, proxy password derivation, token signing.
- `repair_site/status_app/invites.py`  
  SQLite invite repository and invite domain helpers.
- `repair_site/status_app/main.py`  
  Admin APIs, public invite claim APIs, token-scoped status/SSE APIs, internal proxy auth API.
- `repair_site/mitm/claude_repair_addon.py`  
  Remove shared session behavior; add multi-user proxy auth and session attribution.
- `repair_site/web/index.html`  
  Replace repair session input with invite claim UI and proxy config output.
- `repair_site/web/app.js`  
  Claim invite, show config, subscribe to token-scoped status/SSE.
- `repair_site/web/styles.css`  
  Add invite/admin UI styles.
- `repair_site/web/admin.html`  
  Admin login and invite management UI.
- `repair_site/web/admin.js`  
  Admin login, invite list, create, disable, and reset password actions.
- `repair_site/deploy/claude-repair-status.service`  
  Add environment file for admin and invite secrets.
- `repair_site/deploy/claude-repair-mitm.service`  
  Remove `--proxyauth`, add internal secret env.
- `tests/test_config.py`  
  Settings, password derivation, token signing tests.
- `tests/test_invites.py`  
  SQLite invite repository tests.
- `tests/test_invite_api.py`  
  Public invite claim and token-scoped status tests.
- `tests/test_admin_api.py`  
  Admin login and invite management tests.
- `tests/test_mitm_addon.py`  
  Proxy auth attribution and rewrite tests.
- `tests/test_static_site.py`  
  Public/admin static UI and leakage tests.

## Task 1: Config, Secrets, and Token Helpers

**Files:**
- Create: `repair_site/status_app/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from repair_site.status_app.config import (
    Settings,
    derive_proxy_password,
    sign_status_token,
    verify_status_token,
    verify_admin_password,
)


def test_derive_proxy_password_is_repeatable_and_secret_dependent():
    first = derive_proxy_password("repair_abcd", version=1, secret="secret-a")
    second = derive_proxy_password("repair_abcd", version=1, secret="secret-a")
    third = derive_proxy_password("repair_abcd", version=1, secret="secret-b")

    assert first == second
    assert first != third
    assert len(first) >= 24


def test_status_token_round_trip_and_tamper_rejection():
    token = sign_status_token("session-123", secret="status-secret")

    assert verify_status_token(token, secret="status-secret") == "session-123"
    assert verify_status_token(token + "x", secret="status-secret") is None


def test_admin_password_hash_verification():
    settings = Settings(
        admin_username="admin",
        admin_password_hash="sha256:2bb80d537b1da3e38bd30361aa855686bde0ba3634aa083dcad23cf913e250d",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )

    assert verify_admin_password("secret", settings) is True
    assert verify_admin_password("wrong", settings) is False
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_config.py -q
```

Expected: fail because `repair_site.status_app.config` does not exist.

- [ ] **Step 3: Implement config helpers**

Create `repair_site/status_app/config.py`:

```python
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    admin_username: str
    admin_password_hash: str
    invite_secret: str
    status_token_secret: str
    internal_api_secret: str
    database_path: str


def load_settings() -> Settings:
    return Settings(
        admin_username=os.getenv("ADMIN_USERNAME", "admin"),
        admin_password_hash=os.getenv("ADMIN_PASSWORD_HASH", ""),
        invite_secret=os.getenv("INVITE_SECRET", ""),
        status_token_secret=os.getenv("STATUS_TOKEN_SECRET", ""),
        internal_api_secret=os.getenv("INTERNAL_API_SECRET", ""),
        database_path=os.getenv("INVITE_DATABASE_PATH", "/opt/claude-ios-repair/data/invites.sqlite3"),
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


def verify_admin_password(password: str, settings: Settings) -> bool:
    expected = settings.admin_password_hash
    if not expected.startswith("sha256:"):
        return False
    actual = sha256_password_hash(password)
    return hmac.compare_digest(actual, expected)


def _urlsafe_digest(message: str, secret: str, length: int = 32) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")[:length]


def derive_proxy_password(proxy_username: str, *, version: int, secret: str) -> str:
    return _urlsafe_digest(f"proxy:{version}:{proxy_username}", secret, length=28)


def new_invite_code() -> str:
    return "INV-" + secrets.token_urlsafe(9).replace("_", "").replace("-", "")[:12].upper()


def new_session_id() -> str:
    return "sess_" + secrets.token_urlsafe(18)


def new_proxy_username() -> str:
    return "repair_" + secrets.token_urlsafe(8).replace("_", "").replace("-", "").lower()[:10]


def sign_status_token(session_id: str, *, secret: str) -> str:
    payload = base64.urlsafe_b64encode(session_id.encode("utf-8")).decode("ascii").rstrip("=")
    signature = _urlsafe_digest(payload, secret, length=32)
    return payload + "." + signature


def verify_status_token(token: str, *, secret: str) -> str | None:
    try:
        payload, signature = token.split(".", 1)
    except ValueError:
        return None
    expected = _urlsafe_digest(payload, secret, length=32)
    if not hmac.compare_digest(signature, expected):
        return None
    padded = payload + "=" * (-len(payload) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except Exception:
        return None
```

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_config.py -q
```

Expected: pass.

## Task 2: SQLite Invite Repository

**Files:**
- Create: `repair_site/status_app/invites.py`
- Create: `tests/test_invites.py`

- [ ] **Step 1: Write failing repository tests**

Create `tests/test_invites.py`:

```python
from repair_site.status_app.config import Settings, derive_proxy_password
from repair_site.status_app.invites import InviteStore


def settings() -> Settings:
    return Settings(
        admin_username="admin",
        admin_password_hash="sha256:unused",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )


def test_create_invite_generates_unique_credentials():
    store = InviteStore(settings())
    invite = store.create_invite(note="first user")

    assert invite["invite_code"].startswith("INV-")
    assert invite["session_id"].startswith("sess_")
    assert invite["proxy_username"].startswith("repair_")
    assert invite["proxy_password"] == derive_proxy_password(
        invite["proxy_username"], version=invite["proxy_password_version"], secret="invite-secret"
    )
    assert invite["status"] == "active"


def test_claim_invite_rejects_disabled_invite():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    store.disable_invite(invite["id"])

    assert store.claim_invite(invite["invite_code"]) is None


def test_verify_proxy_auth_maps_to_session_id():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    verified = store.verify_proxy_auth(invite["proxy_username"], invite["proxy_password"])

    assert verified["session_id"] == invite["session_id"]
    assert store.verify_proxy_auth(invite["proxy_username"], "wrong") is None
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_invites.py -q
```

Expected: fail because `repair_site.status_app.invites` does not exist.

- [ ] **Step 3: Implement invite store**

Create `repair_site/status_app/invites.py` with:

```python
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repair_site.status_app.config import (
    Settings,
    derive_proxy_password,
    new_invite_code,
    new_proxy_username,
    new_session_id,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InviteStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if settings.database_path != ":memory:":
            Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(settings.database_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_code TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL UNIQUE,
                proxy_username TEXT NOT NULL UNIQUE,
                proxy_password_version INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                last_used_at TEXT,
                disabled_at TEXT,
                note TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def _row_to_invite(self, row: sqlite3.Row | None, *, include_password: bool) -> dict[str, Any] | None:
        if row is None:
            return None
        invite = dict(row)
        if include_password:
            invite["proxy_password"] = derive_proxy_password(
                invite["proxy_username"],
                version=int(invite["proxy_password_version"]),
                secret=self.settings.invite_secret,
            )
        return invite

    def create_invite(self, *, note: str, expires_at: str | None = None) -> dict[str, Any]:
        for _ in range(10):
            invite_code = new_invite_code()
            session_id = new_session_id()
            proxy_username = new_proxy_username()
            created_at = now_iso()
            try:
                cursor = self.conn.execute(
                    """
                    INSERT INTO invites (
                        invite_code, session_id, proxy_username, proxy_password_version,
                        status, created_at, expires_at, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (invite_code, session_id, proxy_username, 1, "active", created_at, expires_at, note),
                )
                self.conn.commit()
                return self.get_invite_by_id(int(cursor.lastrowid), include_password=True)
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("could not create unique invite")

    def list_invites(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM invites ORDER BY id DESC").fetchall()
        return [self._row_to_invite(row, include_password=True) for row in rows]

    def get_invite_by_id(self, invite_id: int, *, include_password: bool = False) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM invites WHERE id = ?", (invite_id,)).fetchone()
        return self._row_to_invite(row, include_password=include_password)

    def claim_invite(self, invite_code: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM invites
            WHERE invite_code = ? AND status = 'active' AND disabled_at IS NULL
            """,
            (invite_code.strip(),),
        ).fetchone()
        invite = self._row_to_invite(row, include_password=True)
        if invite is None:
            return None
        if invite["expires_at"] and invite["expires_at"] < now_iso():
            return None
        self.conn.execute("UPDATE invites SET last_used_at = ? WHERE id = ?", (now_iso(), invite["id"]))
        self.conn.commit()
        return self.get_invite_by_id(invite["id"], include_password=True)

    def disable_invite(self, invite_id: int) -> dict[str, Any] | None:
        self.conn.execute(
            "UPDATE invites SET status = 'disabled', disabled_at = ? WHERE id = ?",
            (now_iso(), invite_id),
        )
        self.conn.commit()
        return self.get_invite_by_id(invite_id, include_password=True)

    def reset_proxy_password(self, invite_id: int) -> dict[str, Any] | None:
        invite = self.get_invite_by_id(invite_id)
        if invite is None:
            return None
        self.conn.execute(
            "UPDATE invites SET proxy_password_version = proxy_password_version + 1 WHERE id = ?",
            (invite_id,),
        )
        self.conn.commit()
        return self.get_invite_by_id(invite_id, include_password=True)

    def verify_proxy_auth(self, proxy_username: str, proxy_password: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM invites
            WHERE proxy_username = ? AND status = 'active' AND disabled_at IS NULL
            """,
            (proxy_username,),
        ).fetchone()
        invite = self._row_to_invite(row, include_password=True)
        if invite is None:
            return None
        if invite["expires_at"] and invite["expires_at"] < now_iso():
            return None
        if invite["proxy_password"] != proxy_password:
            return None
        return invite
```

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_config.py tests/test_invites.py -q
```

Expected: pass.

## Task 3: Public Invite APIs and Token-Scoped Status

**Files:**
- Modify: `repair_site/status_app/main.py`
- Create: `tests/test_invite_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_invite_api.py`:

```python
from fastapi.testclient import TestClient

from repair_site.status_app.config import Settings
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.main import app, set_invite_store_for_tests, store


def setup_function():
    store.sessions.clear()
    store.subscribers.clear()
    settings = Settings(
        admin_username="admin",
        admin_password_hash="sha256:unused",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )
    set_invite_store_for_tests(InviteStore(settings), settings)


def test_claim_invite_returns_proxy_config_without_session_id():
    client = TestClient(app)
    invite = app.state.invite_store.create_invite(note="user")

    response = client.post("/api/invites/claim", json={"invite_code": invite["invite_code"]})

    assert response.status_code == 200
    body = response.json()
    assert body["proxy_host"] == "sg2.claude89757.cc"
    assert body["proxy_port"] == 9443
    assert body["proxy_username"] == invite["proxy_username"]
    assert body["proxy_password"] == invite["proxy_password"]
    assert "session_id" not in body
    assert body["status_token"]


def test_token_scoped_status_uses_internal_session():
    client = TestClient(app)
    invite = app.state.invite_store.create_invite(note="user")
    token = client.post("/api/invites/claim", json={"invite_code": invite["invite_code"]}).json()["status_token"]

    client.post(
        "/api/internal/events",
        headers={"x-internal-secret": "internal-secret"},
        json={"type": "claude_request", "session_id": invite["session_id"], "host": "claude.ai", "path": "/api/account"},
    )
    response = client.get("/api/invites/me/status", headers={"x-status-token": token})

    assert response.status_code == 200
    assert response.json()["events"][0]["path"] == "/api/account"


def test_invalid_token_is_rejected():
    client = TestClient(app)

    response = client.get("/api/invites/me/status", headers={"x-status-token": "bad"})

    assert response.status_code == 401


def test_events_endpoint_accepts_query_token_for_eventsource():
    client = TestClient(app)
    invite = app.state.invite_store.create_invite(note="user")
    token = client.post("/api/invites/claim", json={"invite_code": invite["invite_code"]}).json()["status_token"]

    with client.stream("GET", f"/api/invites/me/events?token={token}&once=true") as response:
        body = next(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: snapshot" in body
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_invite_api.py -q
```

Expected: fail because new APIs do not exist.

- [ ] **Step 3: Implement API wiring**

Modify `repair_site/status_app/main.py`:

- load `Settings`
- create `InviteStore`
- add `set_invite_store_for_tests`
- add `POST /api/invites/claim`
- add `GET /api/invites/me/status`
- add `GET /api/invites/me/events`
- require `x-internal-secret` on `/api/internal/events`

Implementation details:

```python
from repair_site.status_app.config import (
    Settings,
    load_settings,
    sign_status_token,
    verify_status_token,
)
from repair_site.status_app.invites import InviteStore

settings = load_settings()
invite_store = InviteStore(settings)
app.state.invite_store = invite_store
app.state.settings = settings


def set_invite_store_for_tests(new_store: InviteStore, new_settings: Settings) -> None:
    app.state.invite_store = new_store
    app.state.settings = new_settings


def current_settings() -> Settings:
    return app.state.settings


def current_invite_store() -> InviteStore:
    return app.state.invite_store


def session_from_status_token(token: str | None) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="status token required")
    session_id = verify_status_token(token, secret=current_settings().status_token_secret)
    if not session_id:
        raise HTTPException(status_code=401, detail="invalid status token")
    return session_id
```

`POST /api/invites/claim` returns:

```python
{
    "proxy_host": "sg2.claude89757.cc",
    "proxy_port": 9443,
    "proxy_username": invite["proxy_username"],
    "proxy_password": invite["proxy_password"],
    "certificate_url": "/certs/mitmproxy-ca-cert.cer",
    "status_token": sign_status_token(invite["session_id"], secret=current_settings().status_token_secret),
}
```

`GET /api/invites/me/status` reads `x-status-token` and returns `store.snapshot(session_id)`.

`GET /api/invites/me/events` reads query parameter `token` and streams events for the resolved session. This query token is required because browser `EventSource` cannot send custom request headers. Support `once=true` in tests to return only the initial snapshot.

For `/api/internal/events`, require:

```python
if request.headers.get("x-internal-secret") != current_settings().internal_api_secret:
    raise HTTPException(status_code=401, detail="invalid internal secret")
```

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_invite_api.py tests/test_status_api.py -q
```

Expected: pass. If existing status tests post internal events, update them to pass `x-internal-secret`.

## Task 4: Admin APIs

**Files:**
- Modify: `repair_site/status_app/main.py`
- Create: `tests/test_admin_api.py`

- [ ] **Step 1: Write failing admin tests**

Create `tests/test_admin_api.py`:

```python
from fastapi.testclient import TestClient

from repair_site.status_app.config import Settings
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.main import app, set_invite_store_for_tests


def setup_function():
    settings = Settings(
        admin_username="admin",
        admin_password_hash="sha256:2bb80d537b1da3e38bd30361aa855686bde0ba3634aa083dcad23cf913e250d",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )
    set_invite_store_for_tests(InviteStore(settings), settings)


def test_admin_login_and_create_invite():
    client = TestClient(app)

    login = client.post("/api/admin/login", json={"username": "admin", "password": "secret"})
    created = client.post("/api/admin/invites", json={"note": "first"})

    assert login.status_code == 204
    assert created.status_code == 200
    assert created.json()["invite_code"].startswith("INV-")
    assert created.json()["proxy_username"].startswith("repair_")
    assert created.json()["proxy_password"]


def test_admin_invites_require_login():
    client = TestClient(app)

    response = client.get("/api/admin/invites")

    assert response.status_code == 401


def test_admin_can_disable_invite():
    client = TestClient(app)
    client.post("/api/admin/login", json={"username": "admin", "password": "secret"})
    invite = client.post("/api/admin/invites", json={"note": "first"}).json()

    disabled = client.post(f"/api/admin/invites/{invite['id']}/disable")

    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_admin_api.py -q
```

Expected: fail because admin APIs do not exist.

- [ ] **Step 3: Implement admin APIs**

Add helpers to `main.py`:

```python
from repair_site.status_app.config import verify_admin_password


def sign_admin_cookie(username: str) -> str:
    return sign_status_token("admin:" + username, secret=current_settings().status_token_secret)


def require_admin(request: Request) -> None:
    token = request.cookies.get("admin_session")
    session = verify_status_token(token or "", secret=current_settings().status_token_secret)
    if session != "admin:" + current_settings().admin_username:
        raise HTTPException(status_code=401, detail="admin login required")
```

Implement:

- `POST /api/admin/login`: validates username/password, sets `admin_session` cookie, returns 204.
- `POST /api/admin/logout`: clears cookie, returns 204.
- `GET /api/admin/invites`: requires admin, returns `current_invite_store().list_invites()`.
- `POST /api/admin/invites`: requires admin, creates invite from `note` and optional `expires_at`.
- `POST /api/admin/invites/{invite_id}/disable`: requires admin, disables invite.
- `POST /api/admin/invites/{invite_id}/reset-password`: requires admin, increments password version.

Cookie settings:

```python
response.set_cookie(
    "admin_session",
    token,
    httponly=True,
    secure=True,
    samesite="lax",
    path="/",
)
```

In tests, FastAPI TestClient runs over HTTP but still stores secure cookies; if needed, initialize `TestClient(app, base_url="https://testserver")`.

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_admin_api.py tests/test_invite_api.py -q
```

Expected: pass.

## Task 5: MITM Multi-User Proxy Authentication

**Files:**
- Modify: `repair_site/mitm/claude_repair_addon.py`
- Modify: `tests/test_mitm_addon.py`

- [ ] **Step 1: Add failing MITM auth tests**

Extend `tests/test_mitm_addon.py` with:

```python
import base64


def basic_auth(username, password):
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def test_connect_auth_maps_proxy_user_to_session(monkeypatch):
    posts = []

    def fake_post(url, json, timeout, headers=None):
        if url.endswith("/proxy-auth/verify"):
            class Response:
                status_code = 200
                def json(self):
                    return {"session_id": "sess-user-1"}
            return Response()
        posts.append((url, json, headers))
        class Response:
            status_code = 204
        return Response()

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(status_url="http://127.0.0.1:9000/api/internal/events", internal_secret="internal-secret")
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth("repair_user", "password")

    addon.http_connect(flow)
    addon.response(flow)

    assert flow.response.status_code == 401
    assert posts[0][1]["session_id"] == "sess-user-1"


def test_missing_proxy_auth_gets_407(monkeypatch):
    addon = ClaudeRepairAddon(status_url="http://127.0.0.1:9000/api/internal/events", internal_secret="internal-secret")
    flow = Flow()

    addon.http_connect(flow)

    assert flow.response.status_code == 407
```

The fake `Flow` class needs:

```python
self.metadata = {}
self.client_conn = ClientConn()
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_mitm_addon.py -q
```

Expected: fail because auth methods do not exist.

- [ ] **Step 3: Implement auth hooks**

Modify `ClaudeRepairAddon`:

- Add `internal_secret`
- Add `self.authenticated = weakref.WeakKeyDictionary()`
- Add `http_connect(self, flow)`
- Add `requestheaders(self, flow)`
- Add Basic auth parser
- Add backend verifier
- Remove reliance on `REPAIR_SESSION_ID` for normal traffic

Implementation requirements:

```python
def http_connect(self, flow: Any) -> None:
    session_id = self._authenticate_flow(flow)
    if session_id:
        self.authenticated[flow.client_conn] = session_id
        flow.metadata["session_id"] = session_id


def requestheaders(self, flow: Any) -> None:
    if flow.client_conn in self.authenticated:
        flow.metadata["session_id"] = self.authenticated[flow.client_conn]
        return
    session_id = self._authenticate_flow(flow)
    if session_id:
        flow.metadata["session_id"] = session_id
```

If auth fails:

```python
flow.response = http.Response.make(
    407,
    b"Proxy authentication required",
    {"Proxy-Authenticate": 'Basic realm="claude-repair"'},
)
```

When emitting events:

```python
session_id = flow.metadata.get("session_id")
if not session_id:
    return
```

Do not emit unknown traffic into `default`.

Use the internal backend:

```python
httpx.post(
    self.auth_url,
    json={"proxy_username": username, "proxy_password": password},
    headers={"x-internal-secret": self.internal_secret},
    timeout=2.0,
)
```

When posting events, include `headers={"x-internal-secret": self.internal_secret}`.

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_mitm_addon.py -q
```

Expected: pass.

## Task 6: Public Invite UI

**Files:**
- Modify: `repair_site/web/index.html`
- Modify: `repair_site/web/app.js`
- Modify: `repair_site/web/styles.css`
- Modify: `tests/test_static_site.py`

- [ ] **Step 1: Update static UI tests**

Modify `tests/test_static_site.py`:

```python
def test_site_uses_invite_flow_not_session_id():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert "邀请码" in html
    assert "Repair session ID" not in html
    assert "/api/invites/claim" in js
    assert "/api/invites/me/status" in js
    assert "default" not in html
```

Keep existing leakage tests.

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: fail because current UI still uses repair session ID.

- [ ] **Step 3: Update public page**

In `index.html`:

- Replace both `Repair session ID` forms with invite code forms.
- Add a hidden proxy config panel with IDs:
  - `proxy-config`
  - `proxy-host`
  - `proxy-port`
  - `proxy-username`
  - `proxy-password`
- Keep existing status dashboard elements.

User-facing copy:

```text
输入管理员提供的邀请码，验证后页面会显示你的临时代理配置和实时状态。
```

- [ ] **Step 4: Update public JS**

In `app.js`:

- Replace `connect(sessionId)` with `claimInvite(inviteCode)`.
- Store `statusToken` in memory only.
- Fetch `/api/invites/me/status` with `x-status-token`.
- Connect `EventSource` to `/api/invites/me/events?token=...` or use `/api/invites/me/events` if implemented with query token because browser EventSource cannot set custom headers.

Because EventSource cannot set custom headers, implement SSE token as a query parameter:

```javascript
source = new EventSource(`/api/invites/me/events?token=${encodeURIComponent(statusToken)}`);
```

The non-SSE status endpoint can still use `x-status-token`.

- [ ] **Step 5: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: pass.

## Task 7: Admin Static UI

**Files:**
- Create: `repair_site/web/admin.html`
- Create: `repair_site/web/admin.js`
- Modify: `repair_site/web/styles.css`
- Modify: `tests/test_static_site.py`

- [ ] **Step 1: Add admin static tests**

Extend `tests/test_static_site.py`:

```python
def test_admin_page_exists_and_uses_admin_api():
    html = (WEB / "admin.html").read_text()
    js = (WEB / "admin.js").read_text()

    assert "管理员登录" in html
    assert "创建邀请码" in html
    assert "/api/admin/login" in js
    assert "/api/admin/invites" in js
    assert "sshPassword" not in html + js
```

- [ ] **Step 2: Run RED**

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: fail because admin files do not exist.

- [ ] **Step 3: Implement admin UI**

Create `admin.html` with:

- login form
- invite creation form
- invite table
- no embedded admin password
- link back to `/`

Create `admin.js` with:

- `POST /api/admin/login`
- `GET /api/admin/invites`
- `POST /api/admin/invites`
- `POST /api/admin/invites/{id}/disable`
- `POST /api/admin/invites/{id}/reset-password`

- [ ] **Step 4: Run GREEN**

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: pass.

## Task 8: Deployment Configuration

**Files:**
- Modify: `repair_site/deploy/claude-repair-status.service`
- Modify: `repair_site/deploy/claude-repair-mitm.service`
- Modify: `repair_site/deploy/Dockerfile`

- [ ] **Step 1: Update status service env**

Add:

```ini
EnvironmentFile=-/etc/claude-repair/app.env
ExecStartPre=/usr/bin/mkdir -p /opt/claude-ios-repair/data
```

Keep Docker command, but mount data:

```ini
-v /opt/claude-ios-repair/data:/opt/claude-ios-repair/data
```

- [ ] **Step 2: Update MITM service env**

Remove:

```text
--proxyauth ...
```

Add:

```ini
EnvironmentFile=-/etc/claude-repair/app.env
```

Pass `INTERNAL_API_SECRET` to Docker.

- [ ] **Step 3: Verify local tests**

```bash
. .venv/bin/activate
pytest -q
```

Expected: pass.

## Task 9: Server Migration

**Files:**
- Use local files.
- Remote:
  - `/opt/claude-ios-repair`
  - `/etc/claude-repair/app.env`
  - systemd services

- [ ] **Step 1: Generate production secrets locally without printing them**

Use Python `secrets.token_urlsafe(32)` for:

- `INVITE_SECRET`
- `STATUS_TOKEN_SECRET`
- `INTERNAL_API_SECRET`

Use `sha256_password_hash` for the admin password chosen by the operator.

- [ ] **Step 2: Sync files**

```bash
rsync -az --delete --exclude '.venv' --exclude '.pytest_cache' --exclude '__pycache__' repair_site requirements.txt tests root@sg2.claude89757.cc:/opt/claude-ios-repair/
```

- [ ] **Step 3: Build Docker image on server**

```bash
ssh root@sg2.claude89757.cc 'cd /opt/claude-ios-repair && docker build -f repair_site/deploy/Dockerfile -t claude-ios-repair:latest .'
```

- [ ] **Step 4: Write `/etc/claude-repair/app.env`**

The file must contain:

```text
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=sha256:<digest>
INVITE_SECRET=<secret>
STATUS_TOKEN_SECRET=<secret>
INTERNAL_API_SECRET=<secret>
INVITE_DATABASE_PATH=/opt/claude-ios-repair/data/invites.sqlite3
```

Set permissions:

```bash
chmod 600 /etc/claude-repair/app.env
```

- [ ] **Step 5: Restart services**

```bash
systemctl daemon-reload
systemctl restart claude-repair-status.service
systemctl restart claude-repair-mitm.service
systemctl restart nginx
```

- [ ] **Step 6: Smoke test**

```bash
curl -i https://sg2.claude89757.cc/api/health
curl -i https://sg2.claude89757.cc/admin
curl -i https://sg2.claude89757.cc/
ss -ltnp | egrep ":(443|8080|8443|9000|9443) "
```

Expected:

- website and admin page return 200
- Nginx owns 443
- status backend owns 9000 localhost
- mitmdump owns 9443
- gost owns 8080
- gost-warp owns 8443

## Task 10: End-to-End Invite Validation

**Files:** no new files.

- [ ] **Step 1: Log into `/admin`**

Use the configured admin username/password.

Expected: invite management table loads.

- [ ] **Step 2: Create one invite**

Expected: admin table shows invite code, proxy username, proxy password, active status.

- [ ] **Step 3: Claim invite on public page**

Open `https://sg2.claude89757.cc`, enter invite code.

Expected: page shows only that invite's proxy config and live status.

- [ ] **Step 4: Test 9443 with generated credentials**

```bash
curl -k -i -x "http://<proxy_username>:<proxy_password>@sg2.claude89757.cc:9443" "https://claude.ai/api/account?"
```

Expected:

- HTTP response includes `401`
- body contains `session_expired`
- response includes cookie deletion headers
- public page status updates for that invite

- [ ] **Step 5: Create second invite and verify isolation**

Create another invite, claim it in another browser session, run one repair request with second credentials.

Expected: first invite status does not receive second invite's event.

- [ ] **Step 6: Disable invite and verify auth rejection**

Disable first invite in `/admin`.

Run curl with first invite credentials.

Expected: proxy returns `407 Proxy Authentication Required`.

## Final Verification Checklist

Run locally:

```bash
. .venv/bin/activate
pytest -q
rg -n "claude:claude|SSH 密码|服务器 IP|sessionKey=sk-|routingHint=sk-|Authorization: Bearer|proxyPassword|sshPassword" repair_site requirements.txt tests || true
```

Run remotely:

```bash
curl -i https://sg2.claude89757.cc/api/health
curl -i https://sg2.claude89757.cc/admin
curl -i https://sg2.claude89757.cc/certs/mitmproxy-ca-cert.cer
systemctl is-active nginx claude-repair-status.service claude-repair-mitm.service
```

Expected:

- all tests pass
- scans do not expose credentials
- public website and admin page are reachable
- invite-created proxy credentials work on 9443
- disabled invite credentials are rejected
- `default` is not shown in the UI and is not used for normal invite traffic
