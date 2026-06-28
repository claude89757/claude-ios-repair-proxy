import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from repair_site.status_app.config import Settings, verify_status_token
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.store import StatusStore

from repair_site.status_app.main import _status_stream_response, create_app


INTERNAL_HEADERS = {"x-internal-secret": "internal-secret"}


def settings(
    database_path: str = ":memory:",
    *,
    public_invite_ttl_seconds: int = 3600,
) -> Settings:
    return Settings(
        admin_username="admin",
        admin_password_hash="sha256:unused",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=database_path,
        public_invite_ttl_seconds=public_invite_ttl_seconds,
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


def test_localized_public_pages_return_index_html():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    for path in ("/zh", "/en"):
        response = client.get(path)

        assert response.status_code == 200
        assert "Claude iOS Repair" in response.text


def test_static_assets_are_not_shadowed_by_localized_routes():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    for path, expected_content in (
        ("/styles.css", ".topbar"),
        ("/app.js", "LANGUAGE_CACHE_KEY"),
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert expected_content in response.text


def test_claim_invite_returns_proxy_config_and_status_token():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")

    response = client.post(
        "/api/invites/claim",
        json={"invite_code": invite["invite_code"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "proxy_host": "sg2.claude89757.cc",
        "proxy_port": invite["proxy_port"],
        "certificate_url": "/certs/mitmproxy-ca-cert.cer",
        "status_token": body["status_token"],
    }
    assert "session_id" not in body
    assert "proxy_username" not in body
    assert "proxy_password" not in body
    assert verify_status_token(body["status_token"], secret="status-secret") == invite["session_id"]


def test_created_invites_receive_unique_proxy_ports():
    _app, invite_store, _status_store = app_parts()

    first = invite_store.create_invite(note="ios user 1")
    second = invite_store.create_invite(note="ios user 2")

    assert first["proxy_port"] == 10001
    assert second["proxy_port"] == 10002


def test_claim_invite_rejects_invalid_code():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post("/api/invites/claim", json={"invite_code": "INV-MISSING"})

    assert response.status_code == 404


def test_claim_invite_does_not_create_magic_public_invite_code():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/invites/claim",
        json={"invite_code": "INV-VXK44LB9URXY"},
    )

    assert response.status_code == 404
    assert invite_store.list_invites() == []


def test_public_invite_endpoint_creates_one_hour_temporary_invite_each_time():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    before = datetime.now(timezone.utc)

    first = client.post("/api/invites/public", json={"channel": "free"})
    second = client.post("/api/invites/public", json={"channel": "alipay"})

    after = datetime.now(timezone.utc)
    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["invite_code"].startswith("INV-")
    assert second_body["invite_code"].startswith("INV-")
    assert first_body["invite_code"] != second_body["invite_code"]
    assert first_body["proxy_port"] != second_body["proxy_port"]
    assert first_body["certificate_url"] == "/certs/mitmproxy-ca-cert.cer"
    assert "proxy_password" not in first_body
    assert verify_status_token(first_body["status_token"], secret="status-secret")

    stored = invite_store.claim_invite(first_body["invite_code"])
    expires_at = datetime.fromisoformat(stored["expires_at"])
    assert before + timedelta(hours=1) <= expires_at <= after + timedelta(hours=1)
    assert stored["note"].startswith("public temporary invite: free | IP ")


def test_public_invite_records_source_ip_and_geo_in_note():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/invites/public",
        json={"channel": "free"},
        headers={
            "cf-connecting-ip": "203.0.113.9",
            "cf-ipcountry": "SG",
            "cf-region": "Singapore",
            "cf-city": "Singapore",
        },
    )

    assert response.status_code == 200
    invite = invite_store.claim_invite(response.json()["invite_code"])
    assert invite["source_ip"] == "203.0.113.9"
    assert invite["source_geo"] == "SG / Singapore / Singapore"
    assert invite["note"] == (
        "public temporary invite: free | IP 203.0.113.9 | SG / Singapore / Singapore"
    )


def test_public_invite_endpoint_rejects_unknown_channel():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post("/api/invites/public", json={"channel": "xianyu"})

    assert response.status_code == 400


def test_claim_invite_rejects_malformed_json():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/invites/claim",
        content="{bad",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400


def test_claim_invite_rejects_non_object_json():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post("/api/invites/claim", json=["INV-123"])

    assert response.status_code == 400


def test_internal_proxy_auth_verify_returns_session_id_only():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")

    response = client.post(
        "/api/internal/proxy-auth/verify",
        headers=INTERNAL_HEADERS,
        json={
            "proxy_username": invite["proxy_username"],
            "proxy_password": invite["proxy_password"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"session_id": invite["session_id"]}
    assert "proxy_username" not in response.json()
    assert "proxy_password" not in response.json()
    assert "invite_code" not in response.json()


def test_internal_proxy_auth_verify_rejects_invalid_secret():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")

    response = client.post(
        "/api/internal/proxy-auth/verify",
        headers={"x-internal-secret": "wrong-secret"},
        json={
            "proxy_username": invite["proxy_username"],
            "proxy_password": invite["proxy_password"],
        },
    )

    assert response.status_code == 401


def test_internal_proxy_auth_verify_rejects_invalid_password():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")

    response = client.post(
        "/api/internal/proxy-auth/verify",
        headers=INTERNAL_HEADERS,
        json={
            "proxy_username": invite["proxy_username"],
            "proxy_password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_internal_proxy_auth_verify_rejects_malformed_json():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/proxy-auth/verify",
        headers={**INTERNAL_HEADERS, "content-type": "application/json"},
        content="{bad",
    )

    assert response.status_code == 400


def test_internal_proxy_auth_verify_rejects_non_object_json():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.post(
        "/api/internal/proxy-auth/verify",
        headers=INTERNAL_HEADERS,
        json=["bad"],
    )

    assert response.status_code == 400


def test_token_scoped_status_reads_internal_session_events():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")
    event = {
        "type": "claude_request",
        "session_id": invite["session_id"],
        "timestamp": "2026-06-25T00:00:00+00:00",
        "host": "claude.ai",
        "path": "/api/account",
    }

    ingest = client.post("/api/internal/events", headers=INTERNAL_HEADERS, json=event)
    claim = client.post("/api/invites/claim", json={"invite_code": invite["invite_code"]})
    token = claim.json()["status_token"]
    response = client.get("/api/invites/me/status", headers={"x-status-token": token})

    assert ingest.status_code == 204
    assert response.status_code == 200
    assert "session_id" not in response.json()
    assert "session_id" not in response.json()["events"][0]
    assert response.json()["events"][0]["host"] == "claude.ai"


def test_token_scoped_status_rejects_invalid_token():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get(
        "/api/invites/me/status",
        headers={"x-status-token": "bad-token"},
    )

    assert response.status_code == 401


def test_token_scoped_events_once_returns_snapshot_stream():
    app, invite_store, _status_store = app_parts()
    client = TestClient(app)
    invite = invite_store.create_invite(note="ios user")
    client.post(
        "/api/internal/events",
        headers=INTERNAL_HEADERS,
        json={"type": "proxy_connected", "session_id": invite["session_id"]},
    )
    token = client.post(
        "/api/invites/claim",
        json={"invite_code": invite["invite_code"]},
    ).json()["status_token"]

    with client.stream(
        "GET",
        "/api/invites/me/events?once=true",
        headers={"x-status-token": token},
    ) as response:
        body = next(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: snapshot" in body
    assert invite["session_id"] not in body


def test_token_scoped_events_rejects_query_token():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get("/api/invites/me/events?token=bad&once=true")

    assert response.status_code == 401


def test_token_scoped_events_rejects_missing_header_token():
    app, _invite_store, _status_store = app_parts()
    client = TestClient(app)

    response = client.get("/api/invites/me/events?once=true")

    assert response.status_code == 401


def test_status_event_stream_cleans_up_subscriber_on_client_close():
    async def run_stream_cleanup_check() -> None:
        _app, _invite_store, status_store = app_parts()
        response = _status_stream_response(status_store, "repair-abc")

        assert "repair-abc" in status_store.subscribers
        iterator = response.body_iterator
        assert await anext(iterator) == "event: snapshot\n"
        await iterator.aclose()
        assert "repair-abc" not in status_store.subscribers

    asyncio.run(run_stream_cleanup_check())
