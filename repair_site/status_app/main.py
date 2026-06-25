from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from repair_site.status_app.store import StatusStore

app = FastAPI(title="Claude iOS Repair Status")
store = StatusStore(ttl_seconds=3600)


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/internal/events", status_code=204)
async def ingest_event(request: Request) -> Response:
    event: dict[str, Any] = await request.json()
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    event["session_id"] = session_id.strip()
    store.ingest(event)
    return Response(status_code=204)


@app.get("/api/status/{session_id}")
def status_snapshot(session_id: str) -> dict[str, Any]:
    return store.snapshot(session_id)


@app.get("/api/status/{session_id}/events")
async def status_events(session_id: str, once: bool = False) -> StreamingResponse:
    queue = store.subscribe(session_id)

    async def stream() -> AsyncIterator[str]:
        try:
            yield "event: snapshot\n"
            yield "data: " + json.dumps(store.snapshot(session_id)) + "\n\n"
            if once:
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    yield "event: update\n"
                    yield "data: " + json.dumps(event) + "\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\n"
                    yield "data: {}\n\n"
        finally:
            store.unsubscribe(session_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream")


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
if WEB_ROOT.exists():
    app.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
