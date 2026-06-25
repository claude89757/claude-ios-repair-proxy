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
        return ":".join(parts[:3] + ["x"])
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3] + ["x"])
    return "unknown"


def _header(headers: dict[str, str], name: str) -> str:
    lower = {str(key).lower(): str(value) for key, value in headers.items()}
    return lower.get(name.lower(), "")


def safe_path(path: str | None) -> str:
    if not path:
        return "/"
    if path.startswith(("http://", "https://")):
        parsed = urlsplit(path)
        return parsed.path or "/"
    return path.split("?", 1)[0] or "/"


def summarize_headers(headers: dict[str, str]) -> dict[str, Any]:
    cookie = _header(headers, "cookie")
    user_agent = _header(headers, "user-agent")
    device_id = _header(headers, "anthropic-device-id")
    device_hash = None
    if device_id:
        device_hash = "sha256:" + sha256(device_id.encode("utf-8")).hexdigest()[:16]

    return {
        "session_key_present": "sessionKey=" in cookie,
        "routing_hint_present": "routingHint=" in cookie,
        "user_agent_summary": (
            "Claude iOS / CFNetwork / Darwin"
            if "Claude/" in user_agent and "CFNetwork" in user_agent
            else "unknown"
        ),
        "claude_app_version": _header(headers, "anthropic-client-version") or None,
        "claude_app_build": _header(headers, "anthropic-client-build") or None,
        "ios_version": _header(headers, "anthropic-client-os-version") or None,
        "device_id_hash": device_hash,
    }


def sanitize_claude_event(
    *,
    session_id: str,
    client_ip: str | None = None,
    method: str = "",
    host: str = "",
    path: str = "",
    request_headers: dict[str, str] | None = None,
    response_status: int | None = None,
    rewrite_applied: bool = False,
    error_code: str | None = None,
    cookie_deletion_headers_sent: bool = False,
    timestamp: str | None = None,
) -> dict[str, Any]:
    header_summary = summarize_headers(request_headers or {})
    return {
        "type": "claude_request",
        "session_id": session_id,
        "timestamp": timestamp or now_iso(),
        "client_ip": sanitize_client_ip(client_ip),
        "method": method,
        "host": host,
        "path": safe_path(path),
        "response_status": response_status,
        "rewrite_applied": rewrite_applied,
        "error_code": error_code,
        "cookie_deletion_headers_sent": cookie_deletion_headers_sent,
        **header_summary,
    }


def sanitize_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    session_id = str(event["session_id"])
    if event.get("type") == "claude_request" or "request_headers" in event:
        headers = event.get("request_headers")
        return sanitize_claude_event(
            session_id=session_id,
            client_ip=event.get("client_ip"),
            method=str(event.get("method") or ""),
            host=str(event.get("host") or ""),
            path=str(event.get("path") or ""),
            request_headers=headers if isinstance(headers, dict) else {},
            response_status=event.get("response_status"),
            rewrite_applied=bool(event.get("rewrite_applied", False)),
            error_code=event.get("error_code"),
            cookie_deletion_headers_sent=bool(
                event.get("cookie_deletion_headers_sent", False)
            ),
            timestamp=event.get("timestamp"),
        )

    allowed = {
        "type",
        "session_id",
        "timestamp",
        "host",
        "path",
        "method",
        "response_status",
        "rewrite_applied",
        "error_code",
        "cookie_deletion_headers_sent",
        "connection_status",
        "certificate_status",
    }
    sanitized = {key: value for key, value in event.items() if key in allowed}
    sanitized["session_id"] = session_id
    sanitized.setdefault("type", "event")
    sanitized.setdefault("timestamp", now_iso())
    if "path" in sanitized:
        sanitized["path"] = safe_path(str(sanitized["path"]))
    return sanitized


@dataclass
class RepairSession:
    session_id: str
    created_at: str = field(default_factory=now_iso)
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    connection_status: str = "not connected"
    certificate_status: str = "unknown"
    events: list[dict[str, Any]] = field(default_factory=list)
    _touched_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    def add_event(self, event: dict[str, Any], max_events: int = 50) -> None:
        self._touched_at = datetime.now(timezone.utc).timestamp()
        timestamp = str(event.get("timestamp") or now_iso())
        event["timestamp"] = timestamp
        if self.first_seen_at is None:
            self.first_seen_at = timestamp
        self.last_seen_at = timestamp
        self.connection_status = str(event.get("connection_status") or "connected")
        if event.get("host") == "claude.ai" or event.get("certificate_status") == "trusted":
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
