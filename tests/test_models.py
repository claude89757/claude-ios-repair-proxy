from repair_site.status_app.models import (
    sanitize_claude_event,
    sanitize_client_ip,
    summarize_headers,
)


def test_sanitize_client_ip_masks_ipv4_last_octet():
    assert sanitize_client_ip("203.0.113.42") == "203.0.113.x"


def test_summarize_headers_never_exposes_raw_cookie_or_device_id():
    headers = {
        "cookie": "sessionKey=secret; routingHint=secret2",
        "user-agent": "Claude/26723259874 CFNetwork/3860.600.12 Darwin/25.5.0",
        "anthropic-client-version": "1.260528.0",
        "anthropic-client-build": "26723259874",
        "anthropic-client-os-version": "26.5.1",
        "anthropic-device-id": "b93c2bd9-9c8c-4524-8d7d-f7882895a5d8",
    }

    summary = summarize_headers(headers)

    assert summary["session_key_present"] is True
    assert summary["routing_hint_present"] is True
    assert summary["claude_app_version"] == "1.260528.0"
    assert summary["claude_app_build"] == "26723259874"
    assert summary["ios_version"] == "26.5.1"
    assert summary["device_id_hash"].startswith("sha256:")
    assert "b93c2bd9" not in str(summary)
    assert "secret" not in str(summary)


def test_sanitize_claude_event_keeps_only_safe_metadata():
    event = sanitize_claude_event(
        session_id="repair-abc",
        client_ip="203.0.113.42",
        method="GET",
        host="claude.ai",
        path="/api/account?",
        request_headers={"cookie": "sessionKey=secret; routingHint=secret2"},
        response_status=401,
        rewrite_applied=True,
        error_code="session_expired",
        cookie_deletion_headers_sent=True,
    )

    assert event["session_id"] == "repair-abc"
    assert event["client_ip"] == "203.0.113.x"
    assert event["path"] == "/api/account"
    assert event["session_key_present"] is True
    assert event["routing_hint_present"] is True
    assert event["rewrite_applied"] is True
    assert "secret" not in str(event)
