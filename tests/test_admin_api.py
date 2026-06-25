from http.cookies import SimpleCookie

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


def test_admin_login_sets_cookie_and_create_invite_returns_proxy_password():
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
    assert body["proxy_username"].startswith("repair_")
    assert isinstance(body["proxy_password"], str)
    assert body["proxy_password"]


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
    invites = list_response.json()
    assert len(invites) == 1
    assert "proxy_password" not in invites[0]


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


def test_admin_reset_password_returns_new_password_and_invalidates_old_auth():
    client, invite_store, _status_store = admin_client()
    assert login(client).status_code == 204
    invite = client.post("/api/admin/invites", json={"note": "ios user"}).json()
    old_password = invite["proxy_password"]

    reset_response = client.post(f"/api/admin/invites/{invite['id']}/reset-password")

    assert reset_response.status_code == 200
    reset_body = reset_response.json()
    assert reset_body["proxy_password"] != old_password
    assert (
        invite_store.verify_proxy_auth(invite["proxy_username"], old_password) is None
    )
    assert invite_store.verify_proxy_auth(
        invite["proxy_username"],
        reset_body["proxy_password"],
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
