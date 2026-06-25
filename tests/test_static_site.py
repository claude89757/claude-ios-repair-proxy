from pathlib import Path
import re


WEB = Path("repair_site/web")
DEPLOY = Path("repair_site/deploy")


def test_site_contains_required_user_guidance():
    html = (WEB / "index.html").read_text()

    assert "Claude iOS 登录卡死修复指南" in html
    assert "邀请码" in html
    assert "proxy-config" in html
    assert "/certs/mitmproxy-ca-cert.cer" in html
    assert "实时状态" in html
    assert "Repair session ID" not in html
    assert "repair session ID" not in html
    assert "default" not in html


def test_public_site_does_not_embed_proxy_credentials_or_sensitive_values():
    combined = "\n".join(path.read_text() for path in WEB.glob("*.*"))

    forbidden = [
        "sessionKey=sk-",
        "routingHint=sk-",
        "Authorization: Bearer",
        "sshPassword",
        "proxy_pass@",
        "username:password",
        "stack",
        "traceback",
        "?token=",
    ]
    for value in forbidden:
        assert value not in combined


def test_dashboard_client_uses_invite_api_and_header_stream():
    js = (WEB / "app.js").read_text()

    assert "/api/invites/claim" in js
    assert "/api/invites/me/status" in js
    assert "/api/invites/me/events" in js
    assert "x-status-token" in js
    assert "fetch(" in js
    assert "EventSource" not in js
    assert "/api/status/" not in js
    assert "localStorage" not in js
    assert "sessionStorage" not in js


def test_initial_proxy_config_contains_placeholders_only():
    html = (WEB / "index.html").read_text()

    for element_id in [
        "proxy-host",
        "proxy-port",
        "proxy-username",
        "proxy-password",
        "proxy-certificate-url",
    ]:
        assert re.search(rf'id="{element_id}"[^>]*>-</dd>', html)


def test_deploy_config_does_not_expose_legacy_status_route():
    combined = "\n".join(path.read_text() for path in DEPLOY.glob("*.*"))

    assert "location /api/status/" not in combined
