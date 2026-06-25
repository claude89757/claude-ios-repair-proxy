import asyncio

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
    assert snapshot["events"][0]["session_id"] == "repair-abc"
    assert snapshot["events"][0]["host"] == "claude.ai"


def test_unknown_snapshot_is_empty_session():
    store = StatusStore(ttl_seconds=3600)

    snapshot = store.snapshot("missing")

    assert snapshot["session_id"] == "missing"
    assert snapshot["connection_status"] == "not connected"
    assert snapshot["events"] == []


def test_subscriber_receives_ingested_event():
    store = StatusStore(ttl_seconds=3600)
    queue = store.subscribe("repair-abc")
    event = {"type": "proxy_connected", "session_id": "repair-abc"}

    store.ingest(event)

    received = asyncio.run(asyncio.wait_for(queue.get(), timeout=1))
    assert received["type"] == event["type"]
    assert received["session_id"] == event["session_id"]
    assert "timestamp" in received


def test_cleanup_expires_old_sessions_and_subscribers():
    store = StatusStore(ttl_seconds=1)
    queue = store.subscribe("repair-abc")
    store.ingest(
        {
            "type": "claude_request",
            "session_id": "repair-abc",
        }
    )
    store.sessions["repair-abc"]._touched_at = 0

    store.cleanup()

    assert store.snapshot("repair-abc")["events"] == []
    assert "repair-abc" not in store.subscribers


def test_unsubscribe_removes_queue():
    store = StatusStore(ttl_seconds=3600)
    queue = store.subscribe("repair-abc")

    store.unsubscribe("repair-abc", queue)

    assert store.subscribers == {}
