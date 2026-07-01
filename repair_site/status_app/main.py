from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from repair_site.status_app.config import (
    Settings,
    load_settings,
    require_configured,
    sign_status_token,
    verify_admin_password,
    verify_status_token,
)
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.store import StatusStore

ADMIN_SESSION_COOKIE = "admin_session"


def _settings(app: FastAPI) -> Settings:
    return cast(Settings, app.state.settings)


def _invite_store(app: FastAPI) -> InviteStore:
    invite_store = getattr(app.state, "invite_store", None)
    if invite_store is None:
        raise HTTPException(status_code=503, detail="invite store is not initialized")
    return cast(InviteStore, invite_store)


def _status_store(app: FastAPI) -> StatusStore:
    return cast(StatusStore, app.state.status_store)


def _require_internal_secret(request: Request) -> None:
    expected = _settings(request.app).internal_api_secret
    provided = request.headers.get("x-internal-secret", "")
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="invalid internal secret")


def _require_status_session_id(request: Request, token: str | None) -> str:
    if token is None or not token.strip():
        raise HTTPException(status_code=401, detail="invalid status token")
    session_id = verify_status_token(
        token.strip(),
        secret=_settings(request.app).status_token_secret,
    )
    if session_id is None:
        raise HTTPException(status_code=401, detail="invalid status token")
    return session_id


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _sign_admin_session_token(username: str, *, secret: str) -> str:
    payload = {
        "purpose": "admin_session",
        "username": username,
        "exp": int(time.time()) + 3600,
    }
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _b64encode(
        hmac.new(
            secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    return f"{encoded_payload}.{signature}"


def _verify_admin_session_token(token: str | None, *, secret: str) -> str | None:
    if not token:
        return None
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError:
        return None
    expected_signature = _b64encode(
        hmac.new(
            secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("purpose") != "admin_session":
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    username = payload.get("username")
    if not isinstance(username, str):
        return None
    return username


def _set_admin_session_cookie(response: Response, settings: Settings) -> None:
    response.set_cookie(
        ADMIN_SESSION_COOKIE,
        _sign_admin_session_token(
            settings.admin_username,
            secret=settings.status_token_secret,
        ),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def _clear_admin_session_cookie(response: Response) -> None:
    response.delete_cookie(
        ADMIN_SESSION_COOKIE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def _require_admin_username(request: Request) -> str:
    settings = _settings(request.app)
    token = request.cookies.get(ADMIN_SESSION_COOKIE)
    username = _verify_admin_session_token(
        token,
        secret=settings.status_token_secret,
    )
    if username is None or not hmac.compare_digest(username, settings.admin_username):
        raise HTTPException(status_code=401, detail="invalid admin session")
    return settings.admin_username


def _validate_expires_at(expires_at: str) -> str:
    normalized = expires_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="expires_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


async def _json_object(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid json") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="json object required")
    return cast(dict[str, Any], payload)


def _strip_session_ids(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_session_ids(item)
            for key, item in value.items()
            if key != "session_id"
        }
    if isinstance(value, list):
        return [_strip_session_ids(item) for item in value]
    return value


def _strip_proxy_password(value: dict[str, Any]) -> dict[str, Any]:
    output = dict(value)
    output.pop("proxy_password", None)
    return output


def _client_source_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    candidates = [
        request.headers.get("cf-connecting-ip", ""),
        request.headers.get("x-real-ip", ""),
        forwarded_for.split(",", 1)[0].strip() if forwarded_for else "",
        request.client.host if request.client else "",
    ]
    for candidate in candidates:
        if candidate:
            return candidate.strip()
    return "unknown"


def _client_source_geo(request: Request) -> str:
    parts = [
        request.headers.get("cf-ipcountry", ""),
        request.headers.get("cf-region", "") or request.headers.get("cf-region-code", ""),
        request.headers.get("cf-city", ""),
    ]
    clean_parts = [part.strip() for part in parts if part and part.strip()]
    return " / ".join(clean_parts) if clean_parts else "unknown"


def _invite_claim_payload(
    invite: dict[str, Any],
    settings: Settings,
    *,
    include_invite_metadata: bool = False,
) -> dict[str, Any]:
    payload = {
        "proxy_host": "sg2.claude89757.cc",
        "proxy_port": invite["proxy_port"],
        "certificate_url": "/certs/mitmproxy-ca-cert.cer",
        "expires_at": invite.get("expires_at"),
        "status_token": sign_status_token(
            invite["session_id"],
            secret=settings.status_token_secret,
        ),
    }
    if include_invite_metadata:
        payload["invite_code"] = invite["invite_code"]
        payload["expires_at"] = invite.get("expires_at")
    return payload


def _status_stream_response(
    status_store: StatusStore,
    session_id: str,
    *,
    once: bool = False,
    public: bool = False,
) -> StreamingResponse:
    queue = status_store.subscribe(session_id)

    def encode_payload(payload: dict[str, Any]) -> str:
        output = _strip_session_ids(payload) if public else payload
        return json.dumps(output)

    async def stream() -> AsyncIterator[str]:
        try:
            yield "event: snapshot\n"
            yield "data: " + encode_payload(status_store.snapshot(session_id)) + "\n\n"
            if once:
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    yield "event: update\n"
                    yield "data: " + encode_payload(event) + "\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\n"
                    yield "data: {}\n\n"
        finally:
            status_store.unsubscribe(session_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream")


def set_invite_store_for_tests(new_store: InviteStore, new_settings: Settings) -> None:
    app.state.invite_store = new_store
    app.state.settings = new_settings
    app.state.owns_invite_store = False


def create_app(
    *,
    settings: Settings | None = None,
    invite_store: InviteStore | None = None,
    status_store: StatusStore | None = None,
) -> FastAPI:
    app_settings = settings or load_settings()
    app_status_store = status_store or StatusStore(ttl_seconds=3600)

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
        if getattr(app_instance.state, "invite_store", None) is None:
            require_configured(_settings(app_instance))
            app_instance.state.invite_store = InviteStore(_settings(app_instance))
            app_instance.state.owns_invite_store = True
        try:
            yield
        finally:
            if getattr(app_instance.state, "owns_invite_store", False):
                cast(InviteStore, app_instance.state.invite_store).close()
                app_instance.state.invite_store = None
                app_instance.state.owns_invite_store = False

    created_app = FastAPI(title="Claude iOS Repair Status", lifespan=lifespan)
    created_app.state.status_store = app_status_store
    created_app.state.settings = app_settings
    created_app.state.invite_store = invite_store
    created_app.state.owns_invite_store = False
    web_root = Path(__file__).resolve().parents[1] / "web"

    @created_app.get("/api/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @created_app.get("/api/public/stats")
    def public_stats(request: Request) -> dict[str, int]:
        return _invite_store(request.app).public_stats()

    @created_app.post("/api/admin/login", status_code=204)
    async def admin_login(request: Request) -> Response:
        payload = await _json_object(request)
        username = payload.get("username")
        password = payload.get("password")
        settings = _settings(request.app)
        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or username != settings.admin_username
            or not verify_admin_password(password, settings)
        ):
            raise HTTPException(status_code=401, detail="invalid admin credentials")
        response = Response(status_code=204)
        _set_admin_session_cookie(response, settings)
        return response

    @created_app.post("/api/admin/logout", status_code=204)
    def admin_logout() -> Response:
        response = Response(status_code=204)
        _clear_admin_session_cookie(response)
        return response

    @created_app.get("/api/admin/invites")
    def admin_list_invites(
        request: Request,
        page: int = 1,
        page_size: int = 20,
        q: str = "",
        status: str = "all",
        repair_status: str = "all",
        quick_filter: str = "all",
    ) -> dict[str, Any]:
        _require_admin_username(request)
        normalized_status = status.strip().lower()
        normalized_repair_status = repair_status.strip().lower()
        normalized_quick_filter = quick_filter.strip().lower()
        if normalized_status not in {"all", "active", "disabled", "expired"}:
            raise HTTPException(status_code=400, detail="invalid status filter")
        if normalized_repair_status not in {"all", "completed", "pending"}:
            raise HTTPException(status_code=400, detail="invalid repair status filter")
        if normalized_quick_filter not in {
            "all",
            "needs_followup",
            "used_pending",
            "expiring_soon",
            "completed_today",
        }:
            raise HTTPException(status_code=400, detail="invalid quick filter")
        return _invite_store(request.app).list_invites_page(
            page=page,
            page_size=page_size,
            query=q,
            status=normalized_status,
            repair_status=normalized_repair_status,
            quick_filter=normalized_quick_filter,
        )

    @created_app.post("/api/admin/invites")
    async def admin_create_invite(request: Request) -> dict[str, Any]:
        _require_admin_username(request)
        payload = await _json_object(request)
        note = payload.get("note")
        expires_at = payload.get("expires_at")
        if not isinstance(note, str):
            raise HTTPException(status_code=400, detail="note is required")
        if expires_at is not None and not isinstance(expires_at, str):
            raise HTTPException(status_code=400, detail="expires_at must be a string")
        if isinstance(expires_at, str):
            expires_at = _validate_expires_at(expires_at)
        return _strip_proxy_password(
            _invite_store(request.app).create_invite(note=note, expires_at=expires_at)
        )

    @created_app.post("/api/admin/invites/{invite_id}/disable")
    def admin_disable_invite(request: Request, invite_id: int) -> dict[str, Any]:
        _require_admin_username(request)
        invite = _invite_store(request.app).disable_invite(invite_id)
        if invite is None:
            raise HTTPException(status_code=404, detail="invite not found")
        return _strip_proxy_password(invite)

    @created_app.post("/api/admin/invites/{invite_id}/reset-password")
    def admin_reset_invite_password(request: Request, invite_id: int) -> dict[str, Any]:
        _require_admin_username(request)
        invite = _invite_store(request.app).reset_proxy_password(invite_id)
        if invite is None:
            raise HTTPException(status_code=404, detail="invite not found")
        return _strip_proxy_password(invite)

    @created_app.post("/api/internal/events", status_code=204)
    async def ingest_event(request: Request) -> Response:
        _require_internal_secret(request)
        event = await _json_object(request)
        session_id = event.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            raise HTTPException(status_code=400, detail="session_id is required")
        event["session_id"] = session_id.strip()
        sanitized = _status_store(request.app).ingest(event)
        if sanitized.get("rewrite_applied") or sanitized.get("cookie_deletion_headers_sent"):
            _invite_store(request.app).mark_repair_completed_by_session(
                session_id.strip(),
                timestamp=str(sanitized.get("timestamp") or ""),
            )
        return Response(status_code=204)

    @created_app.post("/api/internal/proxy-auth/verify")
    async def verify_proxy_auth(request: Request) -> dict[str, str]:
        _require_internal_secret(request)
        payload = await _json_object(request)
        proxy_username = payload.get("proxy_username")
        proxy_password = payload.get("proxy_password")
        if not isinstance(proxy_username, str) or not isinstance(proxy_password, str):
            raise HTTPException(status_code=401, detail="invalid proxy auth")
        invite = _invite_store(request.app).verify_proxy_auth(proxy_username, proxy_password)
        if invite is None:
            raise HTTPException(status_code=401, detail="invalid proxy auth")
        session_id = invite.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            raise HTTPException(status_code=401, detail="invalid proxy auth")
        return {"session_id": session_id.strip()}

    @created_app.post("/api/invites/public")
    async def create_public_invite(request: Request) -> dict[str, Any]:
        payload = await _json_object(request)
        channel = payload.get("channel", "free")
        if not isinstance(channel, str) or channel not in {"free", "alipay"}:
            raise HTTPException(status_code=400, detail="unsupported public invite channel")
        settings = _settings(request.app)
        source_ip = _client_source_ip(request)
        source_geo = _client_source_geo(request)
        invite_store = _invite_store(request.app)
        if channel == "free" and invite_store.has_public_invite_for_source_ip(
            source_ip=source_ip,
            channel="free",
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "free_invite_limit_reached",
                    "message": "free invite already created for this IP",
                },
            )
        note = f"public temporary invite: {channel} | IP {source_ip} | {source_geo}"
        ttl_seconds = (
            settings.public_free_invite_ttl_seconds
            if channel == "free"
            else settings.public_invite_ttl_seconds
        )
        invite = invite_store.create_temporary_invite(
            note=note,
            ttl_seconds=ttl_seconds,
            source_ip=source_ip,
            source_geo=source_geo,
        )
        return _invite_claim_payload(
            invite,
            settings,
            include_invite_metadata=True,
        )

    @created_app.post("/api/invites/claim")
    async def claim_invite(request: Request) -> dict[str, Any]:
        payload = await _json_object(request)
        invite_code = payload.get("invite_code")
        if not isinstance(invite_code, str) or not invite_code.strip():
            raise HTTPException(status_code=400, detail="invite_code is required")

        normalized_invite_code = invite_code.strip()
        settings = _settings(request.app)
        invite_store = _invite_store(request.app)
        invite = invite_store.claim_invite(normalized_invite_code)
        if invite is None:
            raise HTTPException(status_code=404, detail="invite not found")

        return _invite_claim_payload(invite, settings)

    @created_app.get("/api/invites/me/status")
    def invite_status(request: Request) -> dict[str, Any]:
        session_id = _require_status_session_id(
            request,
            request.headers.get("x-status-token"),
        )
        return cast(dict[str, Any], _strip_session_ids(_status_store(request.app).snapshot(session_id)))

    @created_app.get("/api/invites/me/events")
    async def invite_status_events(
        request: Request,
        once: bool = False,
    ) -> StreamingResponse:
        session_id = _require_status_session_id(
            request,
            request.headers.get("x-status-token"),
        )
        return _status_stream_response(
            _status_store(request.app),
            session_id,
            once=once,
            public=True,
        )

    @created_app.get("/admin", include_in_schema=False)
    @created_app.get("/admin/", include_in_schema=False)
    def admin_page() -> FileResponse:
        admin_html = web_root / "admin.html"
        if not admin_html.exists():
            raise HTTPException(status_code=404, detail="admin page not found")
        return FileResponse(admin_html)

    @created_app.get("/zh", include_in_schema=False)
    @created_app.get("/en", include_in_schema=False)
    def localized_public_page() -> FileResponse:
        index_html = web_root / "index.html"
        if not index_html.exists():
            raise HTTPException(status_code=404, detail="public page not found")
        return FileResponse(index_html)

    if web_root.exists():
        created_app.mount("/", StaticFiles(directory=web_root, html=True), name="web")

    return created_app


store = StatusStore(ttl_seconds=3600)
app = create_app(status_store=store)
