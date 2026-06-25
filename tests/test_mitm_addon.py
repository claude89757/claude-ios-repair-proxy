import base64

from repair_site.mitm.claude_repair_addon import (
    ClaudeRepairAddon,
    COOKIE_DELETIONS,
    SESSION_EXPIRED_BODY,
)


class HeadersWithAdd(dict):
    def add(self, name, value):
        self.setdefault(name, [])
        if isinstance(self[name], list):
            self[name].append(value)
        else:
            self[name] = [self[name], value]


class HeadersWithoutAdd(dict):
    pass


class Request:
    def __init__(self, host="claude.ai", path="/api/account?foo=bar"):
        self.host = host
        self.path = path
        self.method = "GET"
        self.headers = {
            "cookie": "sessionKey=secret; routingHint=secret2",
            "authorization": "Bearer raw-token",
            "anthropic-client-version": "1.260528.0",
            "anthropic-device-id": "b93c2bd9-9c8c-4524-8d7d-f7882895a5d8",
        }


class Response:
    def __init__(self, headers=None):
        self.status_code = 403
        self.reason = "Forbidden"
        self.headers = headers or HeadersWithAdd({"content-type": "application/json"})
        self.text = '{"type":"error","error":{"details":{"error_code":"account_banned"}}}'


class ClientConn:
    peername = ("203.0.113.42", 12345)


class Flow:
    def __init__(
        self,
        host="claude.ai",
        path="/api/account?foo=bar",
        response_headers=None,
    ):
        self.request = Request(host, path)
        self.response = Response(response_headers)
        self.client_conn = ClientConn()
        self.metadata = {}


def basic_auth(username="proxy-user", password="proxy-pass") -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def test_rewrites_only_claude_account_response():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow()

    addon.response(flow)

    assert flow.response.status_code == 401
    assert flow.response.reason == "Unauthorized"
    assert flow.response.text == SESSION_EXPIRED_BODY
    assert flow.response.headers["content-type"] == "application/json"
    assert flow.response.headers["Set-Cookie"] == COOKIE_DELETIONS


def test_does_not_rewrite_claude_legal_path():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow(path="/api/legal?")

    addon.response(flow)

    assert flow.response.status_code == 403
    assert flow.response.reason == "Forbidden"
    assert "account_banned" in flow.response.text
    assert "Set-Cookie" not in flow.response.headers


def test_does_not_rewrite_other_hosts():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow(host="example.com")

    addon.response(flow)

    assert flow.response.status_code == 403
    assert "account_banned" in flow.response.text
    assert "Set-Cookie" not in flow.response.headers


def test_rewrites_account_path_with_header_assignment_fallback():
    addon = ClaudeRepairAddon(status_url=None)
    flow = Flow(response_headers=HeadersWithoutAdd({"content-type": "text/plain"}))

    addon.response(flow)

    assert flow.response.status_code == 401
    assert flow.response.headers["content-type"] == "application/json"
    assert flow.response.headers["Set-Cookie"] == COOKIE_DELETIONS


def test_emits_sanitized_status_event(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.metadata["session_id"] = "repair-abc"

    addon.response(flow)

    assert len(posts) == 1
    assert posts[0][0] == "http://127.0.0.1:9000/api/internal/events"
    assert posts[0][2] == {"x-internal-secret": "internal-secret"}
    assert posts[0][3] == 2.0
    event = posts[0][1]
    assert event["session_id"] == "repair-abc"
    assert event["client_ip"] == "203.0.113.x"
    assert event["host"] == "claude.ai"
    assert event["path"] == "/api/account"
    assert event["response_status"] == 401
    assert event["rewrite_applied"] is True
    assert event["error_code"] == "session_expired"
    assert event["cookie_deletion_headers_sent"] is True
    assert event["session_key_present"] is True
    assert event["routing_hint_present"] is True
    assert "secret" not in str(event)
    assert "raw-token" not in str(event)
    assert "b93c2bd9" not in str(event)


def test_http_connect_authenticates_and_response_emits_mapped_session(monkeypatch):
    posts = []

    class FakeAuthResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"session_id": "repair-connect"}

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))
        if url.endswith("/proxy-auth/verify"):
            return FakeAuthResponse()
        return None

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.http_connect(flow)
    addon.response(flow)

    assert flow.metadata["session_id"] == "repair-connect"
    assert len(posts) == 2
    assert posts[0][0] == "http://127.0.0.1:9000/api/internal/proxy-auth/verify"
    assert posts[0][1] == {
        "proxy_username": "proxy-user",
        "proxy_password": "proxy-pass",
    }
    event = posts[1][1]
    assert event["session_id"] == "repair-connect"


def test_requestheaders_authenticates_and_removes_proxy_authorization(monkeypatch):
    class FakeAuthResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"session_id": "repair-request"}

    def fake_post(url, json, headers, timeout):
        assert url.endswith("/proxy-auth/verify")
        assert headers == {"x-internal-secret": "internal-secret"}
        assert json == {
            "proxy_username": "proxy-user",
            "proxy_password": "proxy-pass",
        }
        assert timeout == 2.0
        return FakeAuthResponse()

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "repair-request"
    assert "Proxy-Authorization" not in flow.request.headers


def test_requestheaders_removes_lowercase_proxy_authorization(monkeypatch):
    class FakeAuthResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"session_id": "repair-request"}

    def fake_post(url, json, headers, timeout):
        return FakeAuthResponse()

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.request.headers["proxy-authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "repair-request"
    assert "proxy-authorization" not in flow.request.headers


def test_connect_session_mapping_uses_connection_object_weakrefs(monkeypatch):
    class FakeAuthResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"session_id": "repair-request"}

    def fake_post(url, json, headers, timeout):
        return FakeAuthResponse()

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.client_conn in addon._authenticated_sessions
    assert id(flow.client_conn) not in addon._authenticated_sessions


def test_http_connect_missing_proxy_auth_returns_407():
    addon = ClaudeRepairAddon()
    flow = Flow()
    flow.request.method = "CONNECT"

    addon.http_connect(flow)

    assert flow.response.status_code == 407
    assert flow.response.headers["Proxy-Authenticate"] == 'Basic realm="claude-repair"'


def test_http_connect_ignores_legacy_default_session_without_proxy_auth():
    addon = ClaudeRepairAddon(session_id="default")
    flow = Flow()
    flow.request.method = "CONNECT"

    addon.http_connect(flow)

    assert flow.response.status_code == 407
    assert flow.metadata == {}


def test_requestheaders_wrong_proxy_auth_returns_407(monkeypatch):
    class FakeAuthResponse:
        status_code = 401

        @staticmethod
        def json():
            return {"detail": "invalid proxy auth"}

    def fake_post(url, json, headers, timeout):
        return FakeAuthResponse()

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.response.status_code == 407
    assert flow.response.headers["Proxy-Authenticate"] == 'Basic realm="claude-repair"'
    assert flow.metadata == {}


def test_requestheaders_missing_internal_secret_fails_closed(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret=None,
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.response.status_code == 407
    assert posts == []


def test_response_rewrites_without_emitting_default_session_when_unknown(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret="internal-secret",
    )
    flow = Flow()

    addon.response(flow)

    assert flow.response.status_code == 401
    assert posts == []


def test_response_does_not_emit_legacy_default_session_when_unknown(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret="internal-secret",
        session_id="default",
    )
    flow = Flow()

    addon.response(flow)

    assert flow.response.status_code == 401
    assert posts == []


def test_response_missing_internal_secret_does_not_post_event(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret=None,
    )
    flow = Flow()
    flow.metadata["session_id"] = "repair-abc"

    addon.response(flow)

    assert flow.response.status_code == 401
    assert posts == []
