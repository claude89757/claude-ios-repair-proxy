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
        headers = getattr(getattr(flow, "request", None), "headers", {})
        return {str(key): str(value) for key, value in headers.items()}

    def _is_target(self, flow: Any) -> bool:
        request = getattr(flow, "request", None)
        if request is None:
            return False
        path_without_query = str(getattr(request, "path", "")).split("?", 1)[0]
        return getattr(request, "host", None) == "claude.ai" and path_without_query == "/api/account"

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
            self._add_header(flow.response.headers, "Set-Cookie", value)

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
