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


def test_emits_observed_anthropic_request_without_rewrite(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret="internal-secret",
    )
    flow = Flow(host="a-api.anthropic.com", path="/api/bootstrap")
    flow.metadata["session_id"] = "repair-abc"
    flow.response.status_code = 200
    flow.response.reason = "OK"
    flow.response.text = "{}"

    addon.response(flow)

    assert flow.response.status_code == 200
    assert flow.response.reason == "OK"
    assert flow.response.text == "{}"
    assert "Set-Cookie" not in flow.response.headers
    assert len(posts) == 1
    event = posts[0][1]
    assert event["type"] == "claude_request"
    assert event["host"] == "a-api.anthropic.com"
    assert event["path"] == "/api/bootstrap"
    assert event["response_status"] == 200
    assert event["rewrite_applied"] is False


def test_http_connect_ignores_stale_proxy_auth_and_response_emits_configured_session(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))
        return None

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.http_connect(flow)
    addon.response(flow)

    assert flow.metadata["session_id"] == "sess-port-10001"
    assert "Proxy-Authorization" not in flow.request.headers
    assert len(posts) == 2
    assert posts[0][0] == "http://127.0.0.1:9000/api/internal/events"
    assert posts[0][1]["type"] == "proxy_connected"
    event = posts[1][1]
    assert event["session_id"] == "sess-port-10001"


def test_http_connect_allows_claude_without_proxy_auth_and_uses_configured_session(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.request.host = "claude.ai"
    flow.response = None

    addon.http_connect(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "sess-port-10001"
    assert len(posts) == 1
    assert posts[0][0].endswith("/api/internal/events")
    assert posts[0][1] == {
        "type": "proxy_connected",
        "session_id": "sess-port-10001",
        "client_ip": "203.0.113.42",
        "connection_status": "connected",
    }


def test_requestheaders_allows_arbitrary_host_without_auth_challenge():
    addon = ClaudeRepairAddon(session_id="sess-port-10001")
    flow = Flow(host="example.com", path="/")
    flow.response = None

    addon.requestheaders(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "sess-port-10001"


def test_requestheaders_allows_connectivity_test_host_without_proxy_auth():
    addon = ClaudeRepairAddon(session_id="sess-port-10001")
    flow = Flow(host="neverssl.com", path="/online")
    flow.response = None

    addon.requestheaders(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "sess-port-10001"


def test_requestheaders_allows_cloudflare_challenge_host_without_proxy_auth():
    addon = ClaudeRepairAddon(session_id="sess-port-10001")
    flow = Flow(host="challenges.cloudflare.com", path="/cdn-cgi/challenge-platform/h/b")
    flow.response = None

    addon.requestheaders(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "sess-port-10001"


def test_http_connect_emits_proxy_connected_event_for_configured_session(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))
        return None

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.http_connect(flow)

    assert len(posts) == 1
    assert posts[0][0].endswith("/api/internal/events")
    assert posts[0][1] == {
        "type": "proxy_connected",
        "session_id": "sess-port-10001",
        "client_ip": "203.0.113.42",
        "connection_status": "connected",
    }


def test_requestheaders_ignores_and_removes_proxy_authorization(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "sess-port-10001"
    assert "Proxy-Authorization" not in flow.request.headers
    assert posts == []


def test_requestheaders_removes_lowercase_proxy_authorization(monkeypatch):
    posts = []
    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.headers["proxy-authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "sess-port-10001"
    assert "proxy-authorization" not in flow.request.headers
    assert posts == []


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


def test_http_connect_missing_proxy_auth_uses_configured_session():
    addon = ClaudeRepairAddon(session_id="sess-port-10001")
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.response = None

    addon.http_connect(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "sess-port-10001"


def test_http_connect_can_use_configured_public_session_id_without_proxy_auth():
    addon = ClaudeRepairAddon(session_id="default")
    flow = Flow()
    flow.request.method = "CONNECT"
    flow.response = None

    addon.http_connect(flow)

    assert flow.response is None
    assert flow.metadata["session_id"] == "default"


def test_requestheaders_wrong_proxy_auth_is_ignored_for_allowed_host(monkeypatch):
    posts = []
    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret="internal-secret",
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "sess-port-10001"
    assert "Proxy-Authorization" not in flow.request.headers
    assert posts == []


def test_requestheaders_missing_internal_secret_still_allows_public_proxy(monkeypatch):
    posts = []

    def fake_post(url, json, headers, timeout):
        posts.append((url, json, headers, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        auth_url="http://127.0.0.1:9000/api/internal/proxy-auth/verify",
        internal_secret=None,
        session_id="sess-port-10001",
    )
    flow = Flow()
    flow.request.headers["Proxy-Authorization"] = basic_auth()

    addon.requestheaders(flow)

    assert flow.metadata["session_id"] == "sess-port-10001"
    assert "Proxy-Authorization" not in flow.request.headers
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
