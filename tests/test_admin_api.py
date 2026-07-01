from http.cookies import SimpleCookie
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from repair_site.status_app.config import Settings, sha256_password_hash
from repair_site.status_app.invites import InviteStore
from repair_site.status_app.main import create_app
from repair_site.status_app.store import StatusStore


def settings(database_path: str = ":memory:") -> Settings:
    return Settings(
        admin_username="admin",
        admin_password_hash=sha256_password_hash("secret"),
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


def admin_client():
    app, invite_store, status_store = app_parts()
    client = TestClient(app, base_url="https://testserver")
    return client, invite_store, status_store


def login(client: TestClient, *, username: str = "admin", password: str = "secret"):
    return client.post(
        "/api/admin/login",
        json={"username": username, "password": password},
    )


def cookie_attributes(response, cookie_name: str) -> dict[str, str | bool]:
    parsed = SimpleCookie()
    parsed.load(response.headers["set-cookie"])
    morsel = parsed[cookie_name]
    return {
        "value": morsel.value,
        "path": morsel["path"],
        "max-age": morsel["max-age"],
        "httponly": bool(morsel["httponly"]),
        "secure": bool(morsel["secure"]),
        "samesite": morsel["samesite"],
    }


def test_admin_login_sets_cookie_and_create_invite_returns_proxy_port():
    client, _invite_store, _status_store = admin_client()

    login_response = login(client)
    create_response = client.post("/api/admin/invites", json={"note": "ios user"})

    assert login_response.status_code == 204
    cookie = login_response.cookies.get("admin_session")
    assert cookie
    attrs = cookie_attributes(login_response, "admin_session")
    assert attrs["value"] == cookie
    assert attrs["httponly"] is True
    assert attrs["secure"] is True
    assert attrs["samesite"] == "lax"
    assert attrs["path"] == "/"

    assert create_response.status_code == 200
    body = create_response.json()
    assert body["note"] == "ios user"
    assert body["invite_code"].startswith("INV-")
    assert body["proxy_port"] == 10001
    assert body["proxy_username"].startswith("repair_")
    assert "proxy_password" not in body


def test_admin_page_is_served_from_extensionless_route():
    client, _invite_store, _status_store = admin_client()

    response = client.get("/admin")

    assert response.status_code == 200
    assert "管理员登录" in response.text
    assert "Claude iOS 登录卡死修复指南" not in response.text


def test_admin_login_rejects_wrong_username_and_password():
    client, _invite_store, _status_store = admin_client()

    wrong_username = login(client, username="root")
    wrong_password = login(client, password="wrong")

    assert wrong_username.status_code == 401
    assert wrong_password.status_code == 401


def test_admin_invite_routes_require_login():
    client, _invite_store, _status_store = admin_client()

    list_response = client.get("/api/admin/invites")
    create_response = client.post("/api/admin/invites", json={"note": "ios user"})
    disable_response = client.post("/api/admin/invites/1/disable")
    reset_response = client.post("/api/admin/invites/1/reset-password")

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert disable_response.status_code == 401
    assert reset_response.status_code == 401


def test_admin_invite_routes_reject_malformed_admin_cookie():
    client, _invite_store, _status_store = admin_client()
    client.cookies.set("admin_session", "bad.bad", domain="testserver", path="/")

    response = client.get("/api/admin/invites")

    assert response.status_code == 401


def test_admin_list_invites_omits_proxy_password():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    create_response = client.post("/api/admin/invites", json={"note": "ios user"})
    list_response = client.get("/api/admin/invites")

    assert create_response.status_code == 200
    assert list_response.status_code == 200
    body = list_response.json()
    invites = body["items"]
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 1
    assert len(invites) == 1
    assert invites[0]["proxy_port"] == 10001
    assert invites[0]["repair_completed"] is False
    assert "proxy_password" not in invites[0]


def test_admin_list_invites_supports_pagination_and_filters():
    client, invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    first = invite_store.create_invite(note="alpha user")
    second = invite_store.create_invite(note="beta user")
    third = invite_store.create_invite(note="gamma user")
    invite_store.disable_invite(second["id"])
    invite_store.mark_repair_completed_by_session(third["session_id"], timestamp="2026-06-25T00:00:00+00:00")

    page_response = client.get("/api/admin/invites?page=2&page_size=2")
    query_response = client.get("/api/admin/invites?q=alpha")
    status_response = client.get("/api/admin/invites?status=disabled")
    repaired_response = client.get("/api/admin/invites?repair_status=completed")

    assert page_response.status_code == 200
    page_body = page_response.json()
    assert page_body["total"] == 3
    assert page_body["page"] == 2
    assert page_body["page_size"] == 2
    assert page_body["total_pages"] == 2
    assert [item["invite_code"] for item in page_body["items"]] == [first["invite_code"]]

    assert query_response.status_code == 200
    assert [item["invite_code"] for item in query_response.json()["items"]] == [first["invite_code"]]

    assert status_response.status_code == 200
    assert [item["invite_code"] for item in status_response.json()["items"]] == [second["invite_code"]]

    assert repaired_response.status_code == 200
    repaired = repaired_response.json()["items"]
    assert [item["invite_code"] for item in repaired] == [third["invite_code"]]
    assert repaired[0]["repair_completed"] is True
    assert repaired[0]["repair_completed_at"] == "2026-06-25T00:00:00+00:00"


def test_admin_list_invites_returns_operational_summary_and_quick_filters():
    client, invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    now = datetime.now(timezone.utc)

    unused = invite_store.create_invite(note="unused manual")
    used_pending = invite_store.create_invite(note="used pending")
    invite_store.claim_invite(used_pending["invite_code"])
    expiring = invite_store.create_invite(
        note="expiring soon",
        expires_at=(now + timedelta(minutes=10)).isoformat(),
    )
    done = invite_store.create_invite(note="completed today")
    invite_store.mark_repair_completed_by_session(
        done["session_id"],
        timestamp=now.isoformat(),
    )
    later = invite_store.create_invite(
        note="later pending",
        expires_at=(now + timedelta(hours=3)).isoformat(),
    )
    disabled = invite_store.create_invite(note="disabled pending")
    invite_store.disable_invite(disabled["id"])

    all_response = client.get("/api/admin/invites?page_size=50")
    used_response = client.get("/api/admin/invites?quick_filter=used_pending&page_size=50")
    expiring_response = client.get("/api/admin/invites?quick_filter=expiring_soon&page_size=50")
    completed_response = client.get("/api/admin/invites?quick_filter=completed_today&page_size=50")
    followup_response = client.get("/api/admin/invites?quick_filter=needs_followup&page_size=50")

    assert all_response.status_code == 200
    summary = all_response.json()["summary"]
    assert summary == {
        "total": 6,
        "active": 5,
        "needs_followup": 4,
        "used_pending": 1,
        "expiring_soon": 1,
        "completed_today": 1,
    }

    assert used_response.status_code == 200
    assert used_response.json()["quick_filter"] == "used_pending"
    assert [item["invite_code"] for item in used_response.json()["items"]] == [
        used_pending["invite_code"]
    ]
    assert used_response.json()["summary"] == summary

    assert expiring_response.status_code == 200
    assert [item["invite_code"] for item in expiring_response.json()["items"]] == [
        expiring["invite_code"]
    ]

    assert completed_response.status_code == 200
    assert [item["invite_code"] for item in completed_response.json()["items"]] == [
        done["invite_code"]
    ]

    assert followup_response.status_code == 200
    followup_codes = [item["invite_code"] for item in followup_response.json()["items"]]
    assert followup_codes == [
        later["invite_code"],
        expiring["invite_code"],
        used_pending["invite_code"],
        unused["invite_code"],
    ]


def test_admin_list_invites_rejects_invalid_quick_filter():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    response = client.get("/api/admin/invites?quick_filter=tomorrow")

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid quick filter"


def test_internal_rewrite_event_marks_invite_repair_completed():
    client, invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    invite = invite_store.create_invite(note="needs repair")

    response = client.post(
        "/api/internal/events",
        headers={"x-internal-secret": "internal-secret"},
        json={
            "type": "claude_request",
            "session_id": invite["session_id"],
            "timestamp": "2026-06-25T00:00:00+00:00",
            "host": "claude.ai",
            "path": "/api/account",
            "rewrite_applied": True,
            "cookie_deletion_headers_sent": True,
        },
    )
    list_response = client.get("/api/admin/invites")

    assert response.status_code == 204
    stored = invite_store.get_invite_by_id(invite["id"])
    assert stored["repair_completed_at"] == "2026-06-25T00:00:00+00:00"
    listed = list_response.json()["items"][0]
    assert listed["repair_completed"] is True
    assert listed["repair_completed_at"] == "2026-06-25T00:00:00+00:00"


def test_admin_session_cookie_is_not_accepted_as_status_token():
    client, _invite_store, _status_store = admin_client()
    login_response = login(client)
    admin_token = login_response.cookies.get("admin_session")

    response = client.get(
        "/api/invites/me/status",
        headers={"x-status-token": admin_token},
    )

    assert response.status_code == 401


def test_admin_disable_invite_blocks_future_claims():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    invite = client.post("/api/admin/invites", json={"note": "ios user"}).json()

    disable_response = client.post(f"/api/admin/invites/{invite['id']}/disable")
    claim_response = client.post(
        "/api/invites/claim",
        json={"invite_code": invite["invite_code"]},
    )

    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"
    assert claim_response.status_code == 404


def test_admin_disable_missing_invite_returns_404():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    response = client.post("/api/admin/invites/999/disable")

    assert response.status_code == 404


def test_admin_reset_password_invalidates_old_auth_without_returning_password():
    client, invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    invite = invite_store.create_invite(note="ios user")
    old_password = invite["proxy_password"]

    reset_response = client.post(f"/api/admin/invites/{invite['id']}/reset-password")

    assert reset_response.status_code == 200
    reset_body = reset_response.json()
    assert "proxy_password" not in reset_body
    assert (
        invite_store.verify_proxy_auth(invite["proxy_username"], old_password) is None
    )


def test_admin_reset_missing_invite_password_returns_404():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    response = client.post("/api/admin/invites/999/reset-password")

    assert response.status_code == 404


def test_admin_create_invite_rejects_invalid_expires_at():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    response = client.post(
        "/api/admin/invites",
        json={"note": "ios user", "expires_at": "not-a-date"},
    )

    assert response.status_code == 400


def test_admin_logout_clears_cookie_and_blocks_subsequent_routes():
    client, _invite_store, _status_store = admin_client()
    assert login(client).status_code == 204

    logout_response = client.post("/api/admin/logout")
    list_response = client.get("/api/admin/invites")

    assert logout_response.status_code == 204
    attrs = cookie_attributes(logout_response, "admin_session")
    assert attrs["max-age"] == "0"
    assert list_response.status_code == 401


def test_admin_login_and_create_invite_reject_malformed_or_non_object_json():
    client, _invite_store, _status_store = admin_client()

    bad_login = client.post(
        "/api/admin/login",
        content="{bad",
        headers={"content-type": "application/json"},
    )
    non_object_login = client.post("/api/admin/login", json=["admin", "secret"])

    assert login(client).status_code == 204
    bad_create = client.post(
        "/api/admin/invites",
        content="{bad",
        headers={"content-type": "application/json"},
    )
    non_object_create = client.post("/api/admin/invites", json=["ios user"])

    assert bad_login.status_code == 400
    assert non_object_login.status_code == 400
    assert bad_create.status_code == 400
    assert non_object_create.status_code == 400
