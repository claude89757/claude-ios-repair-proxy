# Claude iOS Repair Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a public HTTPS repair guide at `https://sg2.claude89757.cc` with a certificate download, live repair status dashboard, and a narrow mitmproxy-based Claude iOS session cleanup proxy.

**Architecture:** Nginx serves the static website on `443` and reverse proxies `/api/status/*` to a local FastAPI status service. A mitmproxy addon runs on `9443`, rewrites only `https://claude.ai/api/account`, and emits sanitized in-memory events to the status service. Existing WARP proxy behavior stays on `8443`.

**Tech Stack:** Static HTML/CSS/JavaScript, Python 3, FastAPI, uvicorn, mitmproxy addon API, pytest, Nginx, systemd.

---

## Repository Notes

`/Users/claude89757/Desktop/cc` is not currently a git repository. Replace commit steps with the verification checkpoint shown in each task. If this directory is initialized as git later, commit at each checkpoint.

## File Structure

- `repair_site/status_app/models.py`  
  Dataclasses and sanitizer helpers for repair sessions and events.
- `repair_site/status_app/store.py`  
  In-memory session store, TTL expiry, and subscriber fan-out for Server-Sent Events.
- `repair_site/status_app/main.py`  
  FastAPI app exposing health, event ingest, snapshot, and SSE endpoints.
- `repair_site/mitm/claude_repair_addon.py`  
  mitmproxy addon that performs the narrow `/api/account` rewrite and emits sanitized events.
- `repair_site/web/index.html`  
  Single-page guide and live status shell.
- `repair_site/web/styles.css`  
  Responsive visual design.
- `repair_site/web/app.js`  
  Status dashboard client using JSON plus SSE.
- `repair_site/deploy/nginx.conf`  
  Nginx server block for `sg2.claude89757.cc`.
- `repair_site/deploy/claude-repair-status.service`  
  systemd service for FastAPI status backend.
- `repair_site/deploy/claude-repair-mitm.service`  
  systemd service for mitmproxy repair proxy.
- `repair_site/scripts/run_local.sh`  
  Local development runner.
- `requirements.txt`  
  Python dependencies.
- `tests/test_models.py`  
  Unit tests for sanitization and state models.
- `tests/test_store.py`  
  Unit tests for TTL, event storage, and subscribers.
- `tests/test_status_api.py`  
  API tests for health, ingest, snapshot, and SSE response shape.
- `tests/test_mitm_addon.py`  
  Tests for `/api/account` rewrite behavior using fake mitmproxy flows.
- `tests/test_static_site.py`  
  Static file tests for content, links, and credential leakage prevention.

## Task 1: Python Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `repair_site/status_app/__init__.py`
- Create: `repair_site/mitm/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create dependency manifest**

Create `requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
mitmproxy==11.0.2
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Create package markers**

Create empty files:

```text
repair_site/status_app/__init__.py
repair_site/mitm/__init__.py
```

- [ ] **Step 3: Add pytest path setup**

Create `tests/conftest.py`:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 4: Verify dependencies install**

Run:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Expected: install completes without dependency resolution errors.

- [ ] **Step 5: Checkpoint**

Run:

```bash
find repair_site tests -maxdepth 3 -type f | sort
```

Expected: package marker and test config files are listed.

## Task 2: Sanitized Status Models

**Files:**
- Create: `repair_site/status_app/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing sanitizer tests**

Create `tests/test_models.py`:

```python
from repair_site.status_app.models import (
    sanitize_client_ip,
    summarize_headers,
    sanitize_claude_event,
)


def test_sanitize_client_ip_masks_ipv4_last_octet():
    assert sanitize_client_ip("203.0.113.42") == "203.0.113.x"


def test_summarize_headers_never_exposes_raw_cookie_or_device_id():
    headers = {
        "cookie": "sessionKey=secret; routingHint=secret2",
        "user-agent": "Claude/26723259874 CFNetwork/3860.600.12 Darwin/25.5.0",
        "anthropic-client-version": "1.260528.0",
        "anthropic-client-build": "26723259874",
        "anthropic-client-os-version": "26.5.1",
        "anthropic-device-id": "b93c2bd9-9c8c-4524-8d7d-f7882895a5d8",
    }

    summary = summarize_headers(headers)

    assert summary["session_key_present"] is True
    assert summary["routing_hint_present"] is True
    assert summary["claude_app_version"] == "1.260528.0"
    assert summary["claude_app_build"] == "26723259874"
    assert summary["ios_version"] == "26.5.1"
    assert summary["device_id_hash"].startswith("sha256:")
    assert "b93c2bd9" not in str(summary)
    assert "secret" not in str(summary)


def test_sanitize_claude_event_keeps_only_safe_metadata():
    event = sanitize_claude_event(
        session_id="repair-abc",
        client_ip="203.0.113.42",
        method="GET",
        host="claude.ai",
        path="/api/account?",
        request_headers={"cookie": "sessionKey=secret; routingHint=secret2"},
        response_status=401,
        rewrite_applied=True,
        error_code="session_expired",
        cookie_deletion_headers_sent=True,
    )

    assert event["session_id"] == "repair-abc"
    assert event["client_ip"] == "203.0.113.x"
    assert event["path"] == "/api/account"
    assert event["session_key_present"] is True
    assert event["routing_hint_present"] is True
    assert event["rewrite_applied"] is True
    assert "secret" not in str(event)
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
. .venv/bin/activate
pytest tests/test_models.py -q
```

Expected: FAIL because `repair_site.status_app.models` does not exist.

- [ ] **Step 3: Implement models**

Create `repair_site/status_app/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_client_ip(ip: str | None) -> str:
    if not ip:
        return "unknown"
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:3]) + ":x"
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3] + ["x"])
    return "unknown"


def _header(headers: dict[str, str], name: str) -> str:
    lower = {key.lower(): value for key, value in headers.items()}
    return lower.get(name.lower(), "")


def _safe_path(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        parsed = urlsplit(path)
        return parsed.path or "/"
    return path.split("?", 1)[0] or "/"


def summarize_headers(headers: dict[str, str]) -> dict[str, Any]:
    cookie = _header(headers, "cookie")
    user_agent = _header(headers, "user-agent")
    device_id = _header(headers, "anthropic-device-id")
    device_hash = ""
    if device_id:
        device_hash = "sha256:" + sha256(device_id.encode("utf-8")).hexdigest()[:16]

    return {
        "session_key_present": "sessionKey=" in cookie,
        "routing_hint_present": "routingHint=" in cookie,
        "user_agent_summary": "Claude iOS / CFNetwork / Darwin"
        if "Claude/" in user_agent and "CFNetwork" in user_agent
        else "unknown",
        "claude_app_version": _header(headers, "anthropic-client-version") or None,
        "claude_app_build": _header(headers, "anthropic-client-build") or None,
        "ios_version": _header(headers, "anthropic-client-os-version") or None,
        "device_id_hash": device_hash or None,
    }


def sanitize_claude_event(
    *,
    session_id: str,
    client_ip: str | None,
    method: str,
    host: str,
    path: str,
    request_headers: dict[str, str],
    response_status: int | None,
    rewrite_applied: bool,
    error_code: str | None,
    cookie_deletion_headers_sent: bool,
) -> dict[str, Any]:
    header_summary = summarize_headers(request_headers)
    return {
        "type": "claude_request",
        "session_id": session_id,
        "timestamp": now_iso(),
        "client_ip": sanitize_client_ip(client_ip),
        "method": method,
        "host": host,
        "path": _safe_path(path),
        "response_status": response_status,
        "rewrite_applied": rewrite_applied,
        "error_code": error_code,
        "cookie_deletion_headers_sent": cookie_deletion_headers_sent,
        **header_summary,
    }


@dataclass
class RepairSession:
    session_id: str
    created_at: str = field(default_factory=now_iso)
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    connection_status: str = "not connected"
    certificate_status: str = "unknown"
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_event(self, event: dict[str, Any], max_events: int = 50) -> None:
        timestamp = event.get("timestamp") or now_iso()
        if self.first_seen_at is None:
            self.first_seen_at = timestamp
        self.last_seen_at = timestamp
        self.connection_status = "connected"
        if event.get("host") == "claude.ai":
            self.certificate_status = "trusted"
        self.events.append(event)
        self.events = self.events[-max_events:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "connection_status": self.connection_status,
            "certificate_status": self.certificate_status,
            "events": self.events,
        }
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
. .venv/bin/activate
pytest tests/test_models.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
rg -n "sessionKey=secret|routingHint=secret|b93c2bd9" repair_site tests
```

Expected: only test fixtures in `tests/test_models.py` contain these dummy values; implementation does not.

## Task 3: In-Memory Status Store

**Files:**
- Create: `repair_site/status_app/store.py`
- Test: `tests/test_store.py`

- [ ] **Step 1: Write failing store tests**

Create `tests/test_store.py`:

```python
import asyncio

import pytest

from repair_site.status_app.store import StatusStore


def test_ingest_event_creates_session_and_snapshot():
    store = StatusStore(ttl_seconds=3600)
    event = {
        "type": "claude_request",
        "session_id": "repair-abc",
        "timestamp": "2026-06-25T00:00:00+00:00",
        "host": "claude.ai",
    }

    store.ingest(event)
    snapshot = store.snapshot("repair-abc")

    assert snapshot["connection_status"] == "connected"
    assert snapshot["certificate_status"] == "trusted"
    assert snapshot["events"] == [event]


def test_unknown_snapshot_is_empty_session():
    store = StatusStore(ttl_seconds=3600)

    snapshot = store.snapshot("missing")

    assert snapshot["session_id"] == "missing"
    assert snapshot["connection_status"] == "not connected"
    assert snapshot["events"] == []


@pytest.mark.asyncio
async def test_subscriber_receives_ingested_event():
    store = StatusStore(ttl_seconds=3600)
    queue = store.subscribe("repair-abc")
    event = {"type": "proxy_connected", "session_id": "repair-abc"}

    store.ingest(event)

    received = await asyncio.wait_for(queue.get(), timeout=1)
    assert received == event
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
. .venv/bin/activate
pytest tests/test_store.py -q
```

Expected: FAIL because `repair_site.status_app.store` does not exist.

- [ ] **Step 3: Implement store**

Create `repair_site/status_app/store.py`:

```python
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from repair_site.status_app.models import RepairSession, now_iso


class StatusStore:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self.sessions: dict[str, RepairSession] = {}
        self.subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    def _expired(self, session: RepairSession) -> bool:
        timestamp = session.last_seen_at or session.created_at
        try:
            seen = datetime.fromisoformat(timestamp)
        except ValueError:
            return False
        return datetime.now(timezone.utc) - seen > self.ttl

    def cleanup(self) -> None:
        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if self._expired(session)
        ]
        for session_id in expired_ids:
            self.sessions.pop(session_id, None)
            self.subscribers.pop(session_id, None)

    def ingest(self, event: dict[str, Any]) -> None:
        self.cleanup()
        session_id = str(event.get("session_id") or "default")
        event.setdefault("timestamp", now_iso())
        session = self.sessions.setdefault(session_id, RepairSession(session_id=session_id))
        session.add_event(event)
        for queue in list(self.subscribers.get(session_id, [])):
            queue.put_nowait(event)

    def snapshot(self, session_id: str) -> dict[str, Any]:
        self.cleanup()
        session = self.sessions.get(session_id)
        if session is None:
            return RepairSession(session_id=session_id).snapshot()
        return session.snapshot()

    def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.subscribers.setdefault(session_id, []).append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        queues = self.subscribers.get(session_id, [])
        if queue in queues:
            queues.remove(queue)
        if not queues:
            self.subscribers.pop(session_id, None)
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
. .venv/bin/activate
pytest tests/test_store.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
. .venv/bin/activate
pytest tests/test_models.py tests/test_store.py -q
```

Expected: PASS.

## Task 4: Status API and SSE

**Files:**
- Create: `repair_site/status_app/main.py`
- Test: `tests/test_status_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_status_api.py`:

```python
from fastapi.testclient import TestClient

from repair_site.status_app.main import app, store


def setup_function():
    store.sessions.clear()
    store.subscribers.clear()


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ingest_and_snapshot_round_trip():
    client = TestClient(app)
    event = {
        "type": "claude_request",
        "session_id": "repair-abc",
        "timestamp": "2026-06-25T00:00:00+00:00",
        "host": "claude.ai",
        "path": "/api/account",
        "rewrite_applied": True,
    }

    ingest = client.post("/api/internal/events", json=event)
    snapshot = client.get("/api/status/repair-abc")

    assert ingest.status_code == 204
    assert snapshot.status_code == 200
    assert snapshot.json()["events"][0]["rewrite_applied"] is True


def test_events_endpoint_returns_sse_content_type():
    client = TestClient(app)

    with client.stream("GET", "/api/status/repair-abc/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
. .venv/bin/activate
pytest tests/test_status_api.py -q
```

Expected: FAIL because `repair_site.status_app.main` does not exist.

- [ ] **Step 3: Implement FastAPI app**

Create `repair_site/status_app/main.py`:

```python
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from repair_site.status_app.store import StatusStore

app = FastAPI(title="Claude iOS Repair Status")
store = StatusStore(ttl_seconds=3600)


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/internal/events", status_code=204)
async def ingest_event(request: Request) -> JSONResponse:
    event: dict[str, Any] = await request.json()
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    store.ingest(event)
    return JSONResponse(status_code=204, content=None)


@app.get("/api/status/{session_id}")
def status_snapshot(session_id: str) -> dict[str, Any]:
    return store.snapshot(session_id)


@app.get("/api/status/{session_id}/events")
async def status_events(session_id: str) -> StreamingResponse:
    queue = store.subscribe(session_id)

    async def stream():
        try:
            yield "event: snapshot\\n"
            yield "data: " + json.dumps(store.snapshot(session_id), ensure_ascii=False) + "\\n\\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    yield "event: update\\n"
                    yield "data: " + json.dumps(event, ensure_ascii=False) + "\\n\\n"
                except asyncio.TimeoutError:
                    yield "event: ping\\n"
                    yield "data: {}\\n\\n"
        finally:
            store.unsubscribe(session_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream")
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
. .venv/bin/activate
pytest tests/test_status_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
. .venv/bin/activate
pytest tests/test_models.py tests/test_store.py tests/test_status_api.py -q
```

Expected: PASS.

## Task 5: mitmproxy Repair Addon

**Files:**
- Create: `repair_site/mitm/claude_repair_addon.py`
- Test: `tests/test_mitm_addon.py`

- [ ] **Step 1: Write failing addon tests**

Create `tests/test_mitm_addon.py`:

```python
from repair_site.mitm.claude_repair_addon import ClaudeRepairAddon


class Headers(dict):
    def add(self, name, value):
        self.setdefault(name, [])
        if isinstance(self[name], list):
            self[name].append(value)
        else:
            self[name] = [self[name], value]


class Request:
    def __init__(self, host="claude.ai", path="/api/account?"):
        self.host = host
        self.path = path
        self.method = "GET"
        self.headers = {
            "cookie": "sessionKey=secret; routingHint=secret2",
            "anthropic-client-version": "1.260528.0",
        }


class Response:
    def __init__(self):
        self.status_code = 403
        self.reason = "Forbidden"
        self.headers = Headers({"content-type": "application/json"})
        self.text = '{"type":"error","error":{"details":{"error_code":"account_banned"}}}'


class ClientConn:
    peername = ("203.0.113.42", 12345)


class Flow:
    def __init__(self, host="claude.ai", path="/api/account?"):
        self.request = Request(host, path)
        self.response = Response()
        self.client_conn = ClientConn()


def test_rewrites_only_claude_account_response():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow()

    addon.response(flow)

    assert flow.response.status_code == 401
    assert "session_expired" in flow.response.text
    cookies = flow.response.headers["Set-Cookie"]
    assert any(value.startswith("sessionKey=;") for value in cookies)
    assert any(value.startswith("routingHint=;") for value in cookies)


def test_does_not_rewrite_non_target_path():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow(path="/api/legal?")

    addon.response(flow)

    assert flow.response.status_code == 403
    assert "account_banned" in flow.response.text
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
. .venv/bin/activate
pytest tests/test_mitm_addon.py -q
```

Expected: FAIL because `repair_site.mitm.claude_repair_addon` does not exist.

- [ ] **Step 3: Implement mitmproxy addon**

Create `repair_site/mitm/claude_repair_addon.py`:

```python
from __future__ import annotations

import os
from typing import Any

import httpx

from repair_site.status_app.models import sanitize_claude_event

SESSION_EXPIRED_BODY = (
    '{"type":"error","error":{"type":"authentication_error",'
    '"message":"session_expired","details":{"error_code":"session_expired"}}}'
)

COOKIE_DELETIONS = [
    "sessionKey=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Secure; HttpOnly; SameSite=None",
    "sessionKey=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Domain=claude.ai; Secure; HttpOnly; SameSite=None",
    "routingHint=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Secure; SameSite=None",
    "routingHint=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Domain=claude.ai; Secure; SameSite=None",
]


class ClaudeRepairAddon:
    def __init__(self, status_url: str | None = None, session_id: str | None = None) -> None:
        self.status_url = status_url or os.getenv("REPAIR_STATUS_URL")
        self.session_id = session_id or os.getenv("REPAIR_SESSION_ID", "default")

    def _client_ip(self, flow: Any) -> str | None:
        peername = getattr(getattr(flow, "client_conn", None), "peername", None)
        if isinstance(peername, tuple) and peername:
            return str(peername[0])
        return None

    def _headers(self, flow: Any) -> dict[str, str]:
        return {str(k): str(v) for k, v in getattr(flow.request, "headers", {}).items()}

    def _is_target(self, flow: Any) -> bool:
        return flow.request.host == "claude.ai" and flow.request.path.split("?", 1)[0] == "/api/account"

    def _emit(self, event: dict[str, Any]) -> None:
        if not self.status_url:
            return
        try:
            httpx.post(self.status_url, json=event, timeout=2.0)
        except httpx.HTTPError:
            return

    def response(self, flow: Any) -> None:
        if not self._is_target(flow):
            return

        flow.response.status_code = 401
        flow.response.reason = "Unauthorized"
        flow.response.text = SESSION_EXPIRED_BODY
        flow.response.headers["content-type"] = "application/json"
        for value in COOKIE_DELETIONS:
            flow.response.headers.add("Set-Cookie", value)

        event = sanitize_claude_event(
            session_id=self.session_id,
            client_ip=self._client_ip(flow),
            method=flow.request.method,
            host=flow.request.host,
            path=flow.request.path,
            request_headers=self._headers(flow),
            response_status=flow.response.status_code,
            rewrite_applied=True,
            error_code="session_expired",
            cookie_deletion_headers_sent=True,
        )
        self._emit(event)


addons = [ClaudeRepairAddon()]
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
. .venv/bin/activate
pytest tests/test_mitm_addon.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
. .venv/bin/activate
pytest tests/test_models.py tests/test_store.py tests/test_status_api.py tests/test_mitm_addon.py -q
```

Expected: PASS.

## Task 6: Static Website and Dashboard Client

**Files:**
- Create: `repair_site/web/index.html`
- Create: `repair_site/web/styles.css`
- Create: `repair_site/web/app.js`
- Test: `tests/test_static_site.py`

- [ ] **Step 1: Write failing static site tests**

Create `tests/test_static_site.py`:

```python
from pathlib import Path


WEB = Path("repair_site/web")


def test_site_contains_required_user_guidance():
    html = (WEB / "index.html").read_text()

    assert "Claude iOS 登录卡死修复指南" in html
    assert "联系管理员获取临时代理配置" in html
    assert "/certs/mitmproxy-ca-cert.cer" in html
    assert "实时状态" in html


def test_public_site_does_not_embed_proxy_credentials_or_sensitive_values():
    combined = "\\n".join(path.read_text() for path in WEB.glob("*.*"))

    forbidden = [
        "sessionKey=sk-",
        "routingHint=sk-",
        "Authorization: Bearer",
        "proxyPassword",
        "sshPassword",
    ]
    for value in forbidden:
        assert value not in combined


def test_dashboard_client_uses_status_api_and_sse():
    js = (WEB / "app.js").read_text()

    assert "/api/status/" in js
    assert "EventSource" in js
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: FAIL because website files do not exist.

- [ ] **Step 3: Implement `index.html`**

Create `repair_site/web/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claude iOS 登录卡死修复指南</title>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="#top">Claude iOS Repair</a>
    <nav>
      <a href="#steps">步骤</a>
      <a href="#status">实时状态</a>
      <a href="#safety">安全说明</a>
    </nav>
  </header>

  <main id="top">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">iPhone / Claude App / 会话清理</p>
        <h1>Claude iOS 登录卡死修复指南</h1>
        <p class="lede">当 Claude App 一直停在 <strong>Something went wrong</strong>，且重装无效时，可以通过临时修复代理清理旧会话，让 App 重新显示登录入口。</p>
        <div class="actions">
          <a class="button primary" href="#steps">查看步骤</a>
          <a class="button secondary" href="/certs/mitmproxy-ca-cert.cer">下载证书</a>
        </div>
      </div>
      <aside class="status-card">
        <span class="pill">代理配置不公开</span>
        <h2>联系管理员获取临时代理配置</h2>
        <p>页面不展示代理账号密码。拿到临时配置后，再按下方步骤操作。</p>
      </aside>
    </section>

    <section id="steps" class="section">
      <h2>修复流程</h2>
      <div class="steps">
        <article>
          <span>1</span>
          <h3>配置 iPhone 代理</h3>
          <p>在 Wi-Fi 详情页选择手动 HTTP 代理，填写管理员提供的服务器、端口、用户名和密码。</p>
        </article>
        <article>
          <span>2</span>
          <h3>安装并信任证书</h3>
          <p>用 Safari 下载根证书，在设置中安装描述文件，并在证书信任设置中启用完全信任。</p>
        </article>
        <article>
          <span>3</span>
          <h3>打开 Claude 一次</h3>
          <p>强退 Claude 后重新打开。看到登录入口后，立即关闭代理并取消证书信任。</p>
        </article>
      </div>
    </section>

    <section id="status" class="section status-section">
      <div>
        <p class="eyebrow">Live diagnostics</p>
        <h2>实时状态</h2>
        <p>输入管理员给你的 repair session ID。这里只显示脱敏元数据，不显示 Cookie、Authorization、请求体或完整设备 ID。</p>
      </div>
      <form id="session-form" class="session-form">
        <label for="session-id">Repair session ID</label>
        <div>
          <input id="session-id" name="session-id" autocomplete="off" placeholder="例如 repair-abc">
          <button type="submit">连接状态</button>
        </div>
      </form>
      <div class="dashboard">
        <div class="panel">
          <h3>设备状态</h3>
          <dl id="device-summary"></dl>
        </div>
        <div class="panel">
          <h3>检查项</h3>
          <ol id="checklist" class="checklist"></ol>
        </div>
        <div class="panel wide">
          <h3>Claude 请求事件</h3>
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>Path</th>
                <th>状态</th>
                <th>Rewrite</th>
                <th>Cookie</th>
              </tr>
            </thead>
            <tbody id="event-table"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="safety" class="section safety">
      <h2>安全说明</h2>
      <ul>
        <li>这个方法只清理卡住的本地旧会话，不解封账号。</li>
        <li>修复完成后关闭 iPhone 代理，并取消证书完全信任。</li>
        <li>不要向任何人公开 Cookie、sessionKey、routingHint 或 Authorization。</li>
        <li>证书被信任期间，修复代理具备 HTTPS 检查能力，只在需要修复时临时启用。</li>
      </ul>
    </section>
  </main>

  <script src="/app.js" defer></script>
</body>
</html>
```

- [ ] **Step 4: Implement `styles.css`**

Create `repair_site/web/styles.css`:

```css
:root {
  --bg: #f7f8fb;
  --ink: #17202a;
  --muted: #5f6b7a;
  --line: #dbe2ec;
  --panel: #ffffff;
  --blue: #2563eb;
  --green: #0f9f6e;
  --warn: #a15c06;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: inherit; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 5vw;
  background: rgba(247, 248, 251, 0.92);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(12px);
}
.brand { font-weight: 800; text-decoration: none; }
nav { display: flex; gap: 18px; color: var(--muted); font-size: 14px; }
nav a { text-decoration: none; }
main { max-width: 1160px; margin: 0 auto; padding: 44px 24px 80px; }
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.8fr);
  gap: 28px;
  align-items: stretch;
}
.hero-copy, .status-card, .panel, .steps article, .safety {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.hero-copy { padding: 44px; }
.eyebrow {
  margin: 0 0 10px;
  color: var(--blue);
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 800;
}
h1 { margin: 0; font-size: 44px; line-height: 1.08; letter-spacing: 0; }
h2 { margin: 0 0 14px; font-size: 28px; letter-spacing: 0; }
h3 { margin: 0 0 8px; }
.lede { color: var(--muted); font-size: 18px; line-height: 1.7; max-width: 680px; }
.actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 28px; }
.button, .session-form button {
  border: 0;
  border-radius: 6px;
  padding: 12px 16px;
  font-weight: 800;
  text-decoration: none;
  cursor: pointer;
}
.primary, .session-form button { background: var(--blue); color: white; }
.secondary { background: #e8eefc; color: var(--blue); }
.status-card { padding: 28px; }
.pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eafaf3;
  color: var(--green);
  font-weight: 800;
  font-size: 12px;
}
.section { margin-top: 34px; }
.steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}
.steps article { padding: 22px; }
.steps span {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--blue);
  color: white;
  font-weight: 900;
  margin-bottom: 16px;
}
.status-section {
  display: grid;
  gap: 18px;
}
.session-form {
  display: grid;
  gap: 8px;
}
.session-form label { font-weight: 800; }
.session-form div { display: flex; gap: 10px; }
.session-form input {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px;
  font: inherit;
}
.dashboard {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.panel { padding: 20px; overflow: auto; }
.wide { grid-column: 1 / -1; }
dl { display: grid; grid-template-columns: 150px 1fr; gap: 8px 12px; margin: 0; }
dt { color: var(--muted); }
dd { margin: 0; font-weight: 700; }
.checklist { margin: 0; padding-left: 22px; }
.checklist li { margin: 8px 0; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border-bottom: 1px solid var(--line); padding: 10px; text-align: left; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.safety { padding: 24px; }
.safety li { margin: 10px 0; color: var(--muted); }

@media (max-width: 760px) {
  .topbar { align-items: flex-start; gap: 12px; flex-direction: column; }
  main { padding: 24px 16px 60px; }
  .hero, .steps, .dashboard { grid-template-columns: 1fr; }
  .hero-copy { padding: 28px; }
  h1 { font-size: 34px; }
  .session-form div { flex-direction: column; }
  dl { grid-template-columns: 1fr; }
}
```

- [ ] **Step 5: Implement `app.js`**

Create `repair_site/web/app.js`:

```javascript
const form = document.querySelector("#session-form");
const input = document.querySelector("#session-id");
const summary = document.querySelector("#device-summary");
const checklist = document.querySelector("#checklist");
const eventTable = document.querySelector("#event-table");
let source = null;

const checks = [
  ["proxy", "代理已连接"],
  ["cert", "证书已信任并可解密 Claude 请求"],
  ["account", "已观察到 /api/account"],
  ["rewrite", "已执行 session_expired rewrite"],
  ["cookies", "已发送 Cookie 删除 Header"],
];

function setSummary(data) {
  const latest = data.events?.at(-1) || {};
  summary.innerHTML = `
    <dt>连接状态</dt><dd>${data.connection_status || "not connected"}</dd>
    <dt>证书状态</dt><dd>${data.certificate_status || "unknown"}</dd>
    <dt>首次看到</dt><dd>${data.first_seen_at || "-"}</dd>
    <dt>最后活动</dt><dd>${data.last_seen_at || "-"}</dd>
    <dt>客户端 IP</dt><dd>${latest.client_ip || "-"}</dd>
    <dt>App 版本</dt><dd>${latest.claude_app_version || "-"}</dd>
    <dt>iOS 版本</dt><dd>${latest.ios_version || "-"}</dd>
  `;
}

function setChecklist(data) {
  const events = data.events || [];
  const hasAccount = events.some((event) => event.path === "/api/account");
  const hasRewrite = events.some((event) => event.rewrite_applied);
  const hasCookieDeletion = events.some((event) => event.cookie_deletion_headers_sent);
  const state = {
    proxy: data.connection_status === "connected",
    cert: data.certificate_status === "trusted",
    account: hasAccount,
    rewrite: hasRewrite,
    cookies: hasCookieDeletion,
  };
  checklist.innerHTML = checks
    .map(([key, label]) => `<li>${state[key] ? "✅" : "○"} ${label}</li>`)
    .join("");
}

function setEvents(data) {
  const rows = (data.events || []).slice(-20).reverse();
  eventTable.innerHTML = rows
    .map((event) => `
      <tr>
        <td>${event.timestamp || "-"}</td>
        <td>${event.path || "-"}</td>
        <td>${event.response_status || "-"}</td>
        <td>${event.rewrite_applied ? "yes" : "no"}</td>
        <td>sessionKey: ${event.session_key_present ? "yes" : "no"} / routingHint: ${event.routing_hint_present ? "yes" : "no"}</td>
      </tr>
    `)
    .join("");
}

function render(data) {
  setSummary(data);
  setChecklist(data);
  setEvents(data);
}

async function connect(sessionId) {
  if (source) source.close();
  const response = await fetch(`/api/status/${encodeURIComponent(sessionId)}`);
  render(await response.json());
  source = new EventSource(`/api/status/${encodeURIComponent(sessionId)}/events`);
  source.addEventListener("snapshot", (event) => render(JSON.parse(event.data)));
  source.addEventListener("update", async () => {
    const fresh = await fetch(`/api/status/${encodeURIComponent(sessionId)}`);
    render(await fresh.json());
  });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const sessionId = input.value.trim();
  if (sessionId) connect(sessionId);
});
```

- [ ] **Step 6: Run tests to verify GREEN**

Run:

```bash
. .venv/bin/activate
pytest tests/test_static_site.py -q
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

Run:

```bash
. .venv/bin/activate
pytest -q
```

Expected: PASS.

## Task 7: Local Run Script

**Files:**
- Create: `repair_site/scripts/run_local.sh`

- [ ] **Step 1: Add local development runner**

Create `repair_site/scripts/run_local.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
. .venv/bin/activate

uvicorn repair_site.status_app.main:app --host 127.0.0.1 --port 9000
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x repair_site/scripts/run_local.sh
```

Expected: command exits successfully.

- [ ] **Step 3: Verify backend starts**

Run:

```bash
. .venv/bin/activate
uvicorn repair_site.status_app.main:app --host 127.0.0.1 --port 9000
```

Expected: uvicorn starts and logs `Application startup complete`. Stop with `Ctrl-C`.

- [ ] **Step 4: Checkpoint**

Run:

```bash
. .venv/bin/activate
pytest -q
```

Expected: PASS.

## Task 8: Deployment Files

**Files:**
- Create: `repair_site/deploy/nginx.conf`
- Create: `repair_site/deploy/claude-repair-status.service`
- Create: `repair_site/deploy/claude-repair-mitm.service`

- [ ] **Step 1: Create Nginx config**

Create `repair_site/deploy/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name sg2.claude89757.cc;

    ssl_certificate /etc/letsencrypt/live/sg2.claude89757.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sg2.claude89757.cc/privkey.pem;

    root /var/www/claude-ios-repair;
    index index.html;

    location /api/status/ {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
    }

    location /api/health {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 2: Create status systemd service**

Create `repair_site/deploy/claude-repair-status.service`:

```ini
[Unit]
Description=Claude iOS repair status backend
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/claude-ios-repair
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/claude-ios-repair/.venv/bin/uvicorn repair_site.status_app.main:app --host 127.0.0.1 --port 9000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Create mitmproxy systemd service**

Create `repair_site/deploy/claude-repair-mitm.service`:

```ini
[Unit]
Description=Claude iOS repair mitmproxy
After=network-online.target claude-repair-status.service
Wants=network-online.target

[Service]
WorkingDirectory=/opt/claude-ios-repair
Environment=PYTHONUNBUFFERED=1
Environment=REPAIR_STATUS_URL=http://127.0.0.1:9000/api/internal/events
Environment=REPAIR_SESSION_ID=default
ExecStart=/opt/claude-ios-repair/.venv/bin/mitmdump --listen-host 0.0.0.0 --listen-port 9443 --mode regular --set block_global=false -s /opt/claude-ios-repair/repair_site/mitm/claude_repair_addon.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 4: Validate Nginx config syntax locally if Nginx is available**

Run:

```bash
nginx -t -c "$PWD/repair_site/deploy/nginx.conf"
```

Expected: On a non-root local machine this may fail because certificate paths do not exist. Acceptable local failure is missing certificate files; syntax errors must be fixed.

- [ ] **Step 5: Checkpoint**

Run:

```bash
rg -n "sessionKey=sk-|routingHint=sk-|Authorization: Bearer|proxyPassword|sshPassword" repair_site requirements.txt tests || true
```

Expected: no output.

## Task 9: Server Deployment

**Files:**
- Use local files from `repair_site/`
- Remote paths:
  - `/opt/claude-ios-repair`
  - `/var/www/claude-ios-repair`
  - `/etc/nginx/conf.d/claude-ios-repair.conf`
  - `/etc/systemd/system/claude-repair-status.service`
  - `/etc/systemd/system/claude-repair-mitm.service`

- [ ] **Step 1: Verify SSH access**

Run:

```bash
ssh root@sg2.claude89757.cc 'hostname && uname -a'
```

Expected: remote shell prints hostname and kernel. If password authentication is required, use the credentials from the private local proxy note, not from public site files.

- [ ] **Step 2: Copy application files**

Run:

```bash
rsync -av --delete repair_site requirements.txt root@sg2.claude89757.cc:/opt/claude-ios-repair/
```

Expected: files sync to `/opt/claude-ios-repair`.

- [ ] **Step 3: Install Python dependencies remotely**

Run:

```bash
ssh root@sg2.claude89757.cc '
  cd /opt/claude-ios-repair &&
  python3 -m venv .venv &&
  . .venv/bin/activate &&
  pip install -r requirements.txt
'
```

Expected: dependencies install.

- [ ] **Step 4: Publish static site**

Run:

```bash
ssh root@sg2.claude89757.cc '
  mkdir -p /var/www/claude-ios-repair &&
  rsync -av --delete /opt/claude-ios-repair/repair_site/web/ /var/www/claude-ios-repair/
'
```

Expected: static files copied.

- [ ] **Step 5: Install Nginx config and services**

Run:

```bash
ssh root@sg2.claude89757.cc '
  cp /opt/claude-ios-repair/repair_site/deploy/nginx.conf /etc/nginx/conf.d/claude-ios-repair.conf &&
  cp /opt/claude-ios-repair/repair_site/deploy/claude-repair-status.service /etc/systemd/system/ &&
  cp /opt/claude-ios-repair/repair_site/deploy/claude-repair-mitm.service /etc/systemd/system/ &&
  systemctl daemon-reload
'
```

Expected: files installed and daemon reload succeeds.

- [ ] **Step 6: Move existing 443 proxy before enabling Nginx**

Run:

```bash
ssh root@sg2.claude89757.cc 'ss -ltnp | grep ":443 " || true'
```

Expected: identify current `443` owner. Stop or reconfigure the existing GOST `443` listener before starting Nginx on `443`. Do not change `8443`.

- [ ] **Step 7: Start services**

Run:

```bash
ssh root@sg2.claude89757.cc '
  systemctl enable --now claude-repair-status.service &&
  systemctl enable --now claude-repair-mitm.service &&
  nginx -t &&
  systemctl restart nginx
'
```

Expected: status backend, mitmproxy, and Nginx are active.

- [ ] **Step 8: Server smoke tests**

Run:

```bash
curl -i https://sg2.claude89757.cc/ | sed -n "1,20p"
curl -i https://sg2.claude89757.cc/api/health | sed -n "1,20p"
curl -x https://sg2.claude89757.cc:8443 https://api.anthropic.com/v1/messages -i | sed -n "1,30p"
```

Expected:
- Website returns `200`.
- Health endpoint returns `{"ok":true}`.
- `8443` still reaches Anthropic and returns an authentication error if no API key is provided.

## Task 10: End-to-End Repair Smoke Test

**Files:**
- No new files.

- [ ] **Step 1: Create or choose a repair session ID**

Use a non-secret identifier such as:

```text
repair-manual-001
```

For the first implementation, set `REPAIR_SESSION_ID=repair-manual-001` in `claude-repair-mitm.service`, then restart:

```bash
ssh root@sg2.claude89757.cc '
  sed -i "s/REPAIR_SESSION_ID=.*/REPAIR_SESSION_ID=repair-manual-001/" /etc/systemd/system/claude-repair-mitm.service &&
  systemctl daemon-reload &&
  systemctl restart claude-repair-mitm.service
'
```

Expected: service restarts.

- [ ] **Step 2: Open dashboard**

Open:

```text
https://sg2.claude89757.cc/#status
```

Enter:

```text
repair-manual-001
```

Expected: dashboard shows empty session state.

- [ ] **Step 3: Configure iPhone repair proxy**

On iPhone Wi-Fi settings, configure manual HTTP proxy using administrator-provided repair proxy host, port `9443`, username, and password if configured.

Expected: iPhone traffic reaches the proxy.

- [ ] **Step 4: Install and trust mitmproxy certificate**

Open the certificate download link on iPhone Safari, install the profile, and enable full trust.

Expected: dashboard moves from connection-only state to certificate-trusted state after a decrypted Claude request is observed.

- [ ] **Step 5: Trigger Claude repair**

Force quit Claude iOS, reopen it once, and watch the dashboard.

Expected:
- `/api/account` event appears.
- `response_status` is `401`.
- `rewrite_applied` is `true`.
- `cookie_deletion_headers_sent` is `true`.
- iPhone Claude returns to login screen.

- [ ] **Step 6: Cleanup**

Disable iPhone proxy and certificate trust.

Expected: iPhone no longer sends traffic through repair proxy.

- [ ] **Step 7: Final privacy scan**

Run locally:

```bash
rg -n "sessionKey=sk-|routingHint=sk-|Authorization: Bearer|proxyPassword|sshPassword" repair_site tests || true
```

Expected: no real secret values appear.
