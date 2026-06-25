from pathlib import Path


WEB = Path("repair_site/web")


def test_site_contains_required_user_guidance():
    html = (WEB / "index.html").read_text()

    assert "Claude iOS 登录卡死修复指南" in html
    assert "联系管理员获取临时代理配置" in html
    assert "/certs/mitmproxy-ca-cert.cer" in html
    assert "实时状态" in html


def test_public_site_does_not_embed_proxy_credentials_or_sensitive_values():
    combined = "\n".join(path.read_text() for path in WEB.glob("*.*"))

    forbidden = [
        "sessionKey=sk-",
        "routingHint=sk-",
        "Authorization: Bearer",
        "proxyPassword",
        "sshPassword",
        "proxy_pass@",
        "username:password",
        "token=",
    ]
    for value in forbidden:
        assert value not in combined


def test_dashboard_client_uses_status_api_and_sse():
    js = (WEB / "app.js").read_text()

    assert "/api/status/" in js
    assert "EventSource" in js
    assert "/events" in js
