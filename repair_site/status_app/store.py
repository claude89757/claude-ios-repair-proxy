from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from repair_site.status_app.models import (
    RepairSession,
    sanitize_event_payload,
)


class StatusStore:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self.sessions: dict[str, RepairSession] = {}
        self.subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    def _expired(self, session: RepairSession) -> bool:
        touched_at = datetime.fromtimestamp(session._touched_at, tz=timezone.utc)
        return datetime.now(timezone.utc) - touched_at > self.ttl

    def cleanup(self) -> None:
        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if self._expired(session)
        ]
        for session_id in expired_ids:
            self.sessions.pop(session_id, None)
            self.subscribers.pop(session_id, None)

    def ingest(self, event: dict[str, Any]) -> dict[str, Any]:
        self.cleanup()
        sanitized = sanitize_event_payload(event)
        session_id = sanitized["session_id"]
        session = self.sessions.setdefault(session_id, RepairSession(session_id=session_id))
        session.add_event(sanitized)
        for queue in list(self.subscribers.get(session_id, [])):
            queue.put_nowait(sanitized)
        return sanitized

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
