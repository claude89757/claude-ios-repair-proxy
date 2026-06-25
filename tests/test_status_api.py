from fastapi.testclient import TestClient

from repair_site.status_app.config import Settings
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.store import StatusStore

from repair_site.status_app.main import create_app


INTERNAL_HEADERS = {"x-internal-secret": "internal-secret"}


def settings(database_path: str = ":memory:") -> Settings:
    return Settings(
        admin_username="admin",
        admin_password_hash="sha256:unused",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=database_path,
    )


def app_parts():
    app_settings = settings()
    invite_store = InviteStore(app_settings)
    status_store = StatusStore(ttl_seconds=3600)
    app = create_app(
        settings=app_settings,
        invite_store=invite_store,
        status_store=status_store,
    )
    return app, invite_store, status_store


def test_health_endpoint():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_ingest_rejects_missing_session_id():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        headers=INTERNAL_HEADERS,
        json={"type": "claude_request"},
    )

    assert response.status_code == 400


def test_ingest_rejects_empty_session_id():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        headers=INTERNAL_HEADERS,
        json={"type": "claude_request", "session_id": ""},
    )

    assert response.status_code == 400


def test_ingest_rejects_missing_internal_secret():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        json={"type": "claude_request", "session_id": "repair-abc"},
    )

    assert response.status_code == 401


def test_ingest_rejects_wrong_internal_secret():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        headers={"x-internal-secret": "wrong-secret"},
        json={"type": "claude_request", "session_id": "repair-abc"},
    )

    assert response.status_code == 401


def test_ingest_and_snapshot_round_trip():
    app, _invite_store, status_store = app_parts()
    client = TestClient(app)
    event = {
        "type": "claude_request",
        "session_id": "repair-abc",
        "timestamp": "2026-06-25T00:00:00+00:00",
        "host": "claude.ai",
        "path": "/api/account",
        "rewrite_applied": True,
    }

    ingest = client.post("/api/internal/events", headers=INTERNAL_HEADERS, json=event)
    snapshot = status_store.snapshot("repair-abc")

    assert ingest.status_code == 204
    assert ingest.content == b""
    assert snapshot["events"][0]["rewrite_applied"] is True


def test_ingest_snapshot_does_not_echo_sensitive_payload_values():
    app, _invite_store, status_store = app_parts()
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

    response = client.post("/api/internal/events", headers=INTERNAL_HEADERS, json=event)
    snapshot = status_store.snapshot("repair-abc")

    assert response.status_code == 204
    body = str(snapshot)
    assert "secret" not in body
    assert "b93c2bd9" not in body
    assert "request_headers" not in body


def test_legacy_status_endpoint_is_removed():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get("/api/status/repair-abc", headers=INTERNAL_HEADERS)

    assert response.status_code == 404


def test_legacy_status_events_endpoint_is_removed():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get("/api/status/repair-abc/events?once=true", headers=INTERNAL_HEADERS)

    assert response.status_code == 404


def test_internal_events_rejects_malformed_json():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/events",
        headers={**INTERNAL_HEADERS, "content-type": "application/json"},
        content="{bad",
    )

    assert response.status_code == 400


def test_create_app_instances_have_isolated_status_stores():
    first_app, _first_invites, first_store = app_parts()
    _second_app, _second_invites, second_store = app_parts()
    first_client = TestClient(first_app)

    event = {
        "type": "proxy_connected",
        "session_id": "repair-abc",
    }
    first_client.post("/api/internal/events", headers=INTERNAL_HEADERS, json=event)

    assert first_store.snapshot("repair-abc")["events"]
    assert second_store.snapshot("repair-abc")["events"] == []
