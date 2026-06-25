from __future__ import annotations

import base64
import os
import weakref
from collections.abc import MutableMapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from repair_site.status_app.models import is_claude_service_host, sanitize_claude_event

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

PUBLIC_PROXY_TEST_HOSTS = {
    "captive.apple.com",
    "challenges.cloudflare.com",
    "neverssl.com",
}
DEFAULT_REPAIR_SESSION_ID = "public"


class ClaudeRepairAddon:
    def __init__(
        self,
        status_url: str | None = None,
        auth_url: str | None = None,
        internal_secret: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.status_url = status_url or os.getenv("REPAIR_STATUS_URL")
        self.auth_url = auth_url or os.getenv("REPAIR_AUTH_URL") or self._derive_auth_url(
            self.status_url
        )
        self.internal_secret = internal_secret or os.getenv("INTERNAL_API_SECRET")
        self.session_id = session_id or os.getenv("REPAIR_SESSION_ID") or DEFAULT_REPAIR_SESSION_ID
        self._authenticated_sessions: MutableMapping[Any, str] = weakref.WeakKeyDictionary()

    def _client_ip(self, flow: Any) -> str | None:
        peername = getattr(getattr(flow, "client_conn", None), "peername", None)
        if isinstance(peername, tuple) and peername:
            return str(peername[0])
        return None

    def _headers(self, flow: Any) -> dict[str, str]:
        headers = getattr(getattr(flow, "request", None), "headers", {})
        return {str(key): str(value) for key, value in headers.items()}

    def _derive_auth_url(self, status_url: str | None) -> str | None:
        if not status_url:
            return None
        parsed = urlsplit(status_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        path = parsed.path or ""
        if path.endswith("/api/internal/events"):
            path = path[: -len("/api/internal/events")] + "/api/internal/proxy-auth/verify"
        else:
            path = "/api/internal/proxy-auth/verify"
        return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))

    def _is_target(self, flow: Any) -> bool:
        request = getattr(flow, "request", None)
        if request is None:
            return False
        path_without_query = str(getattr(request, "path", "")).split("?", 1)[0]
        return getattr(request, "host", None) == "claude.ai" and path_without_query == "/api/account"

    def _is_observable_claude_request(self, flow: Any) -> bool:
        request = getattr(flow, "request", None)
        if request is None:
            return False
        return is_claude_service_host(getattr(request, "host", None))

    def _normalized_request_host(self, flow: Any) -> str:
        request = getattr(flow, "request", None)
        host = getattr(request, "host", None)
        if host is None:
            host = getattr(request, "pretty_host", None)
        return str(host or "").strip().lower().rstrip(".")

    def _is_public_proxy_allowed(self, flow: Any) -> bool:
        host = self._normalized_request_host(flow)
        return is_claude_service_host(host) or host in PUBLIC_PROXY_TEST_HOSTS

    def _internal_headers(self) -> dict[str, str] | None:
        if not self.internal_secret:
            return None
        return {"x-internal-secret": self.internal_secret}

    def _add_header(self, headers: Any, name: str, value: str) -> None:
        add = getattr(headers, "add", None)
        if callable(add):
            add(name, value)
            return

        existing = headers.get(name)
        if existing is None:
            headers[name] = [value]
        elif isinstance(existing, list):
            existing.append(value)
        else:
            headers[name] = [existing, value]

    def _get_header(self, headers: Any, name: str) -> str | None:
        get = getattr(headers, "get", None)
        if callable(get):
            value = get(name)
            if value is not None:
                return str(value)
        for key, value in getattr(headers, "items", lambda: [])():
            if str(key).lower() == name.lower():
                return str(value)
        return None

    def _pop_header(self, headers: Any, name: str) -> None:
        pop = getattr(headers, "pop", None)
        if callable(pop):
            try:
                pop(name)
                return
            except KeyError:
                pass
        for key in list(getattr(headers, "keys", lambda: [])()):
            if str(key).lower() == name.lower():
                del headers[key]
                return

    def _client_conn_key(self, flow: Any) -> Any | None:
        client_conn = getattr(flow, "client_conn", None)
        if client_conn is None:
            return None
        return client_conn

    def _set_flow_session_id(self, flow: Any, session_id: str) -> None:
        metadata = getattr(flow, "metadata", None)
        if isinstance(metadata, dict):
            metadata["session_id"] = session_id

    def _authenticated_session_id(self, flow: Any) -> str | None:
        metadata = getattr(flow, "metadata", None)
        if isinstance(metadata, dict):
            session_id = metadata.get("session_id")
            if isinstance(session_id, str) and session_id.strip():
                return session_id.strip()
        conn_key = self._client_conn_key(flow)
        if conn_key is not None:
            session_id = self._authenticated_sessions.get(conn_key)
            if isinstance(session_id, str) and session_id.strip():
                return session_id
        return None

    def _decode_basic_proxy_auth(self, flow: Any) -> tuple[str, str] | None:
        headers = getattr(getattr(flow, "request", None), "headers", None)
        if headers is None:
            return None
        raw_value = self._get_header(headers, "Proxy-Authorization")
        if not raw_value:
            return None
        scheme, _, token = raw_value.partition(" ")
        if scheme.lower() != "basic" or not token.strip():
            return None
        try:
            decoded = base64.b64decode(token.strip().encode("ascii"), validate=True).decode(
                "utf-8"
            )
        except (ValueError, UnicodeDecodeError):
            return None
        username, separator, password = decoded.partition(":")
        if not separator:
            return None
        return username, password

    def _verify_proxy_auth(self, flow: Any) -> str | None:
        credentials = self._decode_basic_proxy_auth(flow)
        headers = self._internal_headers()
        if credentials is None or not self.auth_url or headers is None:
            return None
        username, password = credentials
        try:
            response = httpx.post(
                self.auth_url,
                json={
                    "proxy_username": username,
                    "proxy_password": password,
                },
                headers=headers,
                timeout=2.0,
            )
        except httpx.HTTPError:
            return None
        if response.status_code != 200:
            return None
        try:
            payload = response.json()
        except ValueError:
            return None
        session_id = payload.get("session_id") if isinstance(payload, dict) else None
        if not isinstance(session_id, str) or not session_id.strip():
            return None
        return session_id.strip()

    def _mark_authenticated(self, flow: Any, session_id: str) -> None:
        conn_key = self._client_conn_key(flow)
        if conn_key is not None:
            self._authenticated_sessions[conn_key] = session_id
        self._set_flow_session_id(flow, session_id)
        headers = getattr(getattr(flow, "request", None), "headers", None)
        if headers is not None:
            self._pop_header(headers, "Proxy-Authorization")
        self._emit(
            {
                "type": "proxy_connected",
                "session_id": session_id,
                "client_ip": self._client_ip(flow),
                "connection_status": "connected",
            }
        )

    def _make_407_response(self) -> Any:
        try:
            from mitmproxy import http as mitmproxy_http

            return mitmproxy_http.Response.make(
                407,
                b"Proxy Authentication Required",
                {"Proxy-Authenticate": 'Basic realm="claude-repair"'},
            )
        except ImportError:
            class SimpleResponse:
                def __init__(self) -> None:
                    self.status_code = 407
                    self.reason = "Proxy Authentication Required"
                    self.headers = {"Proxy-Authenticate": 'Basic realm="claude-repair"'}
                    self.text = "Proxy Authentication Required"

            return SimpleResponse()

    def _make_403_response(self) -> Any:
        try:
            from mitmproxy import http as mitmproxy_http

            return mitmproxy_http.Response.make(
                403,
                b"Proxy target not allowed",
                {"content-type": "text/plain"},
            )
        except ImportError:
            class SimpleResponse:
                def __init__(self) -> None:
                    self.status_code = 403
                    self.reason = "Forbidden"
                    self.headers = {"content-type": "text/plain"}
                    self.text = "Proxy target not allowed"

            return SimpleResponse()

    def _require_proxy_auth(self, flow: Any) -> bool:
        existing_session_id = self._authenticated_session_id(flow)
        if existing_session_id is not None:
            self._set_flow_session_id(flow, existing_session_id)
            headers = getattr(getattr(flow, "request", None), "headers", None)
            if headers is not None:
                self._pop_header(headers, "Proxy-Authorization")
            return True

        session_id = self._verify_proxy_auth(flow)
        if session_id is None:
            flow.response = self._make_407_response()
            return False

        self._mark_authenticated(flow, session_id)
        return True

    def _require_public_proxy_target(self, flow: Any) -> bool:
        if not self._is_public_proxy_allowed(flow):
            flow.response = self._make_403_response()
            return False

        existing_session_id = self._authenticated_session_id(flow)
        if existing_session_id is not None:
            self._set_flow_session_id(flow, existing_session_id)
            headers = getattr(getattr(flow, "request", None), "headers", None)
            if headers is not None:
                self._pop_header(headers, "Proxy-Authorization")
            return True

        self._mark_authenticated(flow, self.session_id)
        return True

    def _emit(self, event: dict[str, Any]) -> None:
        headers = self._internal_headers()
        if not self.status_url or headers is None:
            return
        try:
            httpx.post(
                self.status_url,
                json=event,
                headers=headers,
                timeout=2.0,
            )
        except httpx.HTTPError:
            return

    def http_connect(self, flow: Any) -> None:
        self._require_public_proxy_target(flow)

    def requestheaders(self, flow: Any) -> None:
        self._require_public_proxy_target(flow)

    def response(self, flow: Any) -> None:
        is_rewrite_target = self._is_target(flow)
        if not is_rewrite_target and not self._is_observable_claude_request(flow):
            return

        if is_rewrite_target:
            flow.response.status_code = 401
            flow.response.reason = "Unauthorized"
            flow.response.text = SESSION_EXPIRED_BODY
            flow.response.headers["content-type"] = "application/json"
            for value in COOKIE_DELETIONS:
                self._add_header(flow.response.headers, "Set-Cookie", value)

        session_id = self._authenticated_session_id(flow)
        if session_id is None:
            return

        event = sanitize_claude_event(
            session_id=session_id,
            client_ip=self._client_ip(flow),
            method=flow.request.method,
            host=flow.request.host,
            path=flow.request.path,
            request_headers=self._headers(flow),
            response_status=flow.response.status_code,
            rewrite_applied=is_rewrite_target,
            error_code="session_expired" if is_rewrite_target else None,
            cookie_deletion_headers_sent=is_rewrite_target,
        )
        self._emit(event)


addons = [ClaudeRepairAddon()]
