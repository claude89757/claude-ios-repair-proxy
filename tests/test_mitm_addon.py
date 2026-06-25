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

    def fake_post(url, json, timeout):
        posts.append((url, json, timeout))

    monkeypatch.setattr("repair_site.mitm.claude_repair_addon.httpx.post", fake_post)
    addon = ClaudeRepairAddon(
        status_url="http://127.0.0.1:9000/api/internal/events",
        session_id="repair-abc",
    )
    flow = Flow()

    addon.response(flow)

    assert len(posts) == 1
    assert posts[0][0] == "http://127.0.0.1:9000/api/internal/events"
    assert posts[0][2] == 2.0
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
