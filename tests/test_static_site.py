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


def test_public_status_dashboard_has_manual_refresh_button():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert 'id="status-refresh"' in html
    assert 'type="button"' in html
    assert "刷新状态" in html
    assert 'document.querySelector("#status-refresh")' in js
    assert "请先验证邀请码，再刷新实时状态。" in js
    assert "refreshSnapshot()" in js


def test_public_site_has_single_invite_entry_point():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert html.count("<form ") == 1
    assert html.count('name="invite-code"') == 1
    assert html.count("data-claim-feedback") == 1
    assert 'id="invite-form"' in html
    assert 'id="invite-code"' in html
    assert "hero-invite-form" not in html + js
    assert "hero-invite-code" not in html + js


def test_admin_site_contains_required_management_ui():
    html = (WEB / "admin.html").read_text()

    assert "管理员登录" in html
    assert "创建邀请码" in html
    assert "邀请码列表" in html
    assert "代理密码" in html
    assert 'type="password"' in html
    assert "admin-password" in html
    assert "value=\"secret\"" not in html
    assert "Repair session ID" not in html
    assert "repair session ID" not in html


def test_admin_login_password_can_be_revealed_with_toggle_button():
    html = (WEB / "admin.html").read_text()
    js = (WEB / "admin.js").read_text()

    assert 'class="password-field"' in html
    assert 'id="password-toggle"' in html
    assert 'aria-label="显示密码"' in html
    assert 'aria-controls="admin-password"' in html
    assert 'type="button"' in html
    assert 'class="password-toggle"' in html
    assert 'passwordInput.type = "text"' in js
    assert 'passwordInput.type = "password"' in js
    assert "aria-pressed" in js


def test_admin_client_uses_admin_api_and_cookie_session_only():
    js = (WEB / "admin.js").read_text()

    assert "/api/admin/login" in js
    assert "/api/admin/logout" in js
    assert "/api/admin/invites" in js
    assert "/disable" in js
    assert "/reset-password" in js
    assert 'credentials: "same-origin"' in js
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "?token=" not in js


def test_admin_forms_are_read_before_controls_are_disabled():
    js = (WEB / "admin.js").read_text()

    login_start = js.index("async function handleLogin")
    login_end = js.index("async function handleCreate")
    login_block = js[login_start:login_end]
    assert login_block.index("const data = new FormData(loginForm);") < login_block.index(
        "setBusy(loginForm, true);"
    )

    create_start = js.index("async function handleCreate")
    create_end = js.index("async function handleInviteAction")
    create_block = js[create_start:create_end]
    assert create_block.index("const data = new FormData(createForm);") < create_block.index(
        "setBusy(createForm, true);"
    )


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
