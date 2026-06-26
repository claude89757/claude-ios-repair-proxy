from pathlib import Path
import re


WEB = Path("repair_site/web")
DEPLOY = Path("repair_site/deploy")


def test_site_contains_required_user_guidance():
    html = (WEB / "index.html").read_text()

    assert "Claude iOS 登录卡死修复指南" in html
    assert "Something went wrong, try again" in html
    assert "账号被 ban" in html
    assert "删除并重装" in html
    assert "旧 session、cookie、routing hint" in html
    assert "邀请码" in html
    assert "proxy-config" in html
    assert "/certs/mitmproxy-ca-cert.cer" in html
    assert "设置 → 通用 → VPN 与设备管理" in html
    assert "设置 → 通用 → 关于本机 → 证书信任设置" in html
    assert "完全信任" in html
    assert "打开飞行模式" in html
    assert "只打开 Wi-Fi" in html
    assert "HTTP 代理" in html
    assert "认证保持关闭" in html
    assert "关闭手机上的其它 VPN、代理或梯子工具" in html
    assert "否则 Claude 流量可能不会走到修复代理" in html
    assert "实时状态" in html
    assert "正常已登录" in html
    assert "不一定触发修复事件" in html
    assert "公开页面不内置代理账号密码" in html
    assert "默认 24 小时失效" in html
    assert "脱敏状态和事件元数据" in html
    assert "不记录 Cookie、请求体或完整设备标识" in html
    assert "Repair session ID" not in html
    assert "repair session ID" not in html
    assert "default" not in html


def test_public_site_supports_chinese_english_language_toggle():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert 'id="language-toggle"' in html
    assert 'class="language-toggle"' in html
    assert 'aria-label="Switch language"' in html
    assert 'data-i18n=' in html
    assert 'data-i18n-placeholder=' in html
    assert "LANGUAGE_CACHE_KEY" in js
    assert "claudeRepairLanguage" in js
    assert "function applyLanguage" in js
    assert "function setLanguage" in js
    assert "document.querySelectorAll(\"[data-i18n]\")" in js
    assert "Claude iOS sign-in loop repair guide" in js
    assert "Turn off any other VPN, proxy, or tunneling app" in js


def test_public_site_links_to_github_repository_from_topbar():
    html = (WEB / "index.html").read_text()

    assert "https://github.com/claude89757/claude-ios-repair-proxy" in html
    assert 'class="github-link"' in html
    assert 'aria-label="GitHub 开源地址"' in html
    assert 'target="_blank"' in html
    assert 'rel="noreferrer noopener"' in html
    assert ">GitHub<" in html


def test_public_site_keeps_invite_form_in_sticky_header():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()

    header = re.search(r"<header class=\"topbar\">.*?</header>", html, re.S)
    entry_panel = re.search(r"<aside class=\"entry-panel\".*?</aside>", html, re.S)

    assert header is not None
    assert entry_panel is not None
    assert 'id="invite-form"' in header.group(0)
    assert 'class="header-invite-form"' in header.group(0)
    assert 'id="invite-code"' in header.group(0)
    assert 'data-claim-feedback' in header.group(0)
    assert 'id="invite-form"' not in entry_panel.group(0)
    assert html.count('id="invite-form"') == 1
    assert ".topbar {" in css
    assert "position: sticky;" in css
    assert ".header-invite-form" in css


def test_public_site_supports_language_specific_paths():
    deploy = (DEPLOY / "nginx.conf").read_text()
    js = (WEB / "app.js").read_text()

    assert "try_files $uri $uri/ /index.html;" in deploy
    assert "PATH_LANGUAGE_PREFIXES" in js
    assert "function languageFromPath" in js
    assert "function pathForLanguage" in js
    assert "window.location.pathname" in js
    assert "window.history.replaceState" in js
    assert "window.history.pushState" in js
    assert "window.location.hash" in js
    assert '"/en"' in js
    assert '"/zh"' in js


def test_public_site_does_not_show_duplicate_certificate_download_buttons():
    html = (WEB / "index.html").read_text()

    assert 'id="proxy-certificate"' not in html
    assert "下载 CA 证书" not in html
    assert ">下载证书<" not in html
    assert 'id="proxy-certificate-url"' in html
    assert "/certs/mitmproxy-ca-cert.cer" in html


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
    assert "sessionStorage" not in js


def test_dashboard_latches_completed_repair_checks_for_active_invite():
    js = (WEB / "app.js").read_text()

    assert "let repairProgress = initialRepairProgress();" in js
    assert "function mergeRepairProgress" in js
    assert "function resetRepairProgress" in js
    assert "const state = mergeRepairProgress(data);" in js
    assert "resetRepairProgress();" in js


def test_dashboard_separates_proxy_connections_from_claude_events():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert "只显示 Claude/Anthropic 相关连接和请求" in html
    assert "function isClaudeEvent" in js
    assert 'event?.type === "claude_connect"' in js
    assert 'event?.type === "claude_request"' in js
    assert ".filter(isClaudeEvent)" in js
    assert "CONNECT ${text(event.host)}" in js
    assert "TLS 未解密" in js
    assert "尚未观察到 Claude/Anthropic 请求" in js


def test_dashboard_caches_only_invite_code_for_browser_restore():
    js = (WEB / "app.js").read_text()

    assert "localStorage" in js
    assert "claudeRepairInviteCode" in js
    assert "restoreCachedInvite" in js
    assert "saveCachedInviteCode(inviteCode)" in js
    assert "localStorage.setItem(INVITE_CACHE_KEY, inviteCode)" in js
    assert "localStorage.setItem" in js
    assert "localStorage.setItem(INVITE_CACHE_KEY, statusToken)" not in js
    assert "localStorage.setItem(INVITE_CACHE_KEY, claim.status_token)" not in js
    assert "localStorage.setItem(INVITE_CACHE_KEY, claim.proxy_password)" not in js
    assert "claim.proxy_password" not in js
    assert "proxyPassword" not in js
    assert "proxyUsername" not in js


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
    assert "代理端口" in html
    assert "代理密码" not in html
    assert "代理用户名" not in html
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
    assert "/reset-password" not in js
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
        "proxy-certificate-url",
    ]:
        assert re.search(rf'id="{element_id}"[^>]*>-</dd>', html)

    assert "proxy-username" not in html
    assert "proxy-password" not in html
    assert "用户名和密码" not in html


def test_deploy_config_does_not_expose_legacy_status_route():
    combined = "\n".join(path.read_text() for path in DEPLOY.glob("*.*"))

    assert "location /api/status/" not in combined
