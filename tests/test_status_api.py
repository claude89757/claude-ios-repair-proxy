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


def test_ingest_rejects_missing_session_id():
    client = TestClient(app)

    response = client.post("/api/internal/events", json={"type": "claude_request"})

    assert response.status_code == 400


def test_ingest_rejects_empty_session_id():
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        json={"type": "claude_request", "session_id": ""},
    )

    assert response.status_code == 400


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
    assert ingest.content == b""
    assert snapshot.status_code == 200
    assert snapshot.json()["events"][0]["rewrite_applied"] is True


def test_ingest_snapshot_does_not_echo_sensitive_payload_values():
    client = TestClient(app)
    event = {
        "type": "claude_request",
        "session_id": "repair-abc",
        "request_headers": {
            "Cookie": "sessionKey=secret; routingHint=secret2",
            "Authorization": "Bearer secret3",
            "anthropic-device-id": "b93c2bd9-9c8c-4524-8d7d-f7882895a5d8",
        },
    }

    response = client.post("/api/internal/events", json=event)
    snapshot = client.get("/api/status/repair-abc")

    assert response.status_code == 204
    body = str(snapshot.json())
    assert "secret" not in body
    assert "b93c2bd9" not in body
    assert "request_headers" not in body


def test_events_endpoint_returns_finite_initial_sse_snapshot():
    client = TestClient(app)

    with client.stream("GET", "/api/status/repair-abc/events?once=true") as response:
        body = next(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: snapshot" in body
    assert '"session_id": "repair-abc"' in body
