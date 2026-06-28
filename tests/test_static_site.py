from pathlib import Path
import re


WEB = Path("repair_site/web")
DEPLOY = Path("repair_site/deploy")
DCOS = Path("dcos")


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
    assert "关闭手机上的其它 VPN、代理或第三方网络工具" in html
    assert "否则 Claude 流量可能不会进入本次修复通道" in html
    assert "实时状态" in html
    assert "正常已登录" in html
    assert "不一定触发修复事件" in html
    assert "不提供 VPN、翻墙、通用代理或网络加速能力" in html
    assert "免费/打赏入口会生成 1 小时临时邀请码" in html
    assert "公开入口默认 1 小时失效" in html
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
    assert "Turn off any other VPN, proxy, or third-party network tool" in js


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

    assert header is not None
    assert 'id="invite-form"' in header.group(0)
    assert 'class="header-invite-form"' in header.group(0)
    assert 'id="invite-code"' in header.group(0)
    assert 'data-claim-feedback' in header.group(0)
    assert 'class="invite-floating-note"' in header.group(0)
    assert "entry-panel" not in html
    assert html.count('id="invite-form"') == 1
    assert ".topbar {" in css
    assert "position: sticky;" in css
    assert ".header-invite-form" in css


def test_public_site_uses_step_by_step_wizard_cards():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'class="guide-layout"' in html
    assert 'class="wizard-card is-active' in html
    assert html.count("data-step-panel") == 5
    assert html.count("data-step-button") == 5
    assert html.count("data-step-complete") >= 4
    assert 'aria-current="step"' in html
    assert "function setActiveStep" in js
    assert "function markStepComplete" in js
    assert "document.querySelectorAll(\"[data-step-button]\")" in js
    assert "document.querySelectorAll(\"[data-step-complete]\")" in js
    assert ".wizard-card" in css
    assert ".step-rail" in css
    assert ".step-complete-button" in css


def test_public_site_has_invite_acquisition_gate_with_three_options():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'class="invite-gate-screen' in html
    assert "获取修复邀请码" in html
    assert "选择一个获取方式，按提示拿到邀请码后继续修复。" in html
    assert "免费使用" in html
    assert "先打开小红书" in html
    assert "一键三连" in html
    assert "自助使用，无售后和远程支持" in html
    assert "支付宝随缘付费" in html
    assert "远程指导和后续售后技术支持" in html
    assert "闲鱼下单购买" in html
    assert "购买后按售后指引获取邀请码" in html
    assert "无法帮助解决被封号" in html
    assert "不提供 VPN、翻墙、通用代理或网络加速能力" in html
    assert "/assets/alipay-reward-qr.jpg" in html
    assert "/assets/group-invite-qr.jpg" in html
    assert "xiaohongshu.com/explore/6a3d6a840000000015027b6c" in html
    assert "https://www.goofish.com/item" in html
    assert "id=1061136454887" in html
    assert "categoryId=50023914" in html
    assert "#小程序://闲鱼/GI2JHZ8RzMQrHWn" not in html
    assert "推荐" in html
    assert html.index("闲鱼下单购买") < html.index("支付宝随缘付费") < html.index("免费使用")
    assert html.count("data-invite-method-select") == 3
    assert 'data-invite-method-panel="xianyu"' in html
    assert 'data-invite-method-panel="alipay"' in html
    assert 'data-invite-method-panel="free"' in html
    assert html.count("data-invite-auto-claim") == 2
    assert "PUBLIC_INVITE_CODE" not in js
    assert "INV-VXK44LB9URXY" not in js
    assert "/api/invites/public" in js
    assert "function selectInviteMethod" in js
    assert "function showInviteGateView" in js
    assert "function resetInviteGateView" in js
    assert "function autoClaimPublicInvite" in js
    assert "function createPublicInvite" in js
    assert "function unlockRepairWorkspace" in js
    assert "function lockRepairWorkspace" in js
    assert 'data-invite-view="choice"' in html
    assert 'data-invite-view="xianyu"' in html
    assert 'data-invite-view="alipay"' in html
    assert 'data-invite-view="free"' in html
    assert html.count("data-invite-back") == 3
    assert ".invite-methods" in css
    assert ".invite-method-page" in css
    assert ".invite-choice-view" in css
    assert ".invite-gate-screen" in css


def test_public_site_has_compliance_disclaimer_footer():
    html = (WEB / "index.html").read_text()
    disclaimer = (WEB / "disclaimer.html").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'href="/disclaimer.html"' in html
    assert 'data-i18n="nav.safety">使用边界</a>' in html
    assert 'id="disclaimer"' not in html
    assert "免责声明与使用边界" not in html
    assert 'id="disclaimer"' in disclaimer
    assert "免责声明与使用边界" in disclaimer
    assert "本地旧登录态残留" in disclaimer
    assert "不是 VPN、翻墙工具、网络加速器、通用代理或跨境联网服务" in disclaimer
    assert "请勿将本工具用于访问与修复无关的网站、App 或服务" in disclaimer
    assert "本项目与 Anthropic、Claude、Apple 无官方关联" in disclaimer
    assert "Disclaimer and usage boundaries" in disclaimer
    assert "not a VPN, circumvention tool, accelerator, general-purpose proxy" in disclaimer
    assert 'href="/zh"' in disclaimer
    assert ".site-disclaimer" in css
    assert ".disclaimer-card" in css


def test_invite_options_open_isolated_method_pages():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()
    js = (WEB / "app.js").read_text()

    assert "data-active-view=\"choice\"" in html
    assert "invite-view invite-choice-view" in html
    assert html.count("invite-view invite-method-page") == 3
    assert "invite-method-detail-list" not in html
    assert "invite-manual-note" not in html
    assert "data-countdown-slot" not in html
    assert 'inviteMethodPages.forEach((page) =>' in js
    assert 'inviteGateScreen.dataset.activeView = targetView' in js
    assert 'moveInviteCountdownTo(channel)' not in js
    assert ".invite-method-page[hidden]" in css
    assert ".invite-method-page-body" in css
    assert ".method-page-actions" in css


def test_alipay_and_free_invite_pages_use_simple_single_column_layout():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'class="invite-view invite-method-page simple-method-page"' in html
    assert html.count('class="invite-view invite-method-page simple-method-page"') == 2
    assert ".simple-method-page .invite-method-page-body" in css
    assert "grid-template-columns: minmax(0, 680px);" in css
    assert ".simple-method-page .method-page-copy" in css
    assert ".simple-method-page .qr-scan-panel" in css
    assert "box-shadow: none;" in css


def test_public_invite_auto_claim_fills_invite_and_verifies_immediately():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    auto_claim = js.index("function autoClaimPublicInvite")
    next_function = js.index("function focusInviteInput")
    auto_claim_block = js[auto_claim:next_function]

    assert "倒计时" not in html
    assert "开始 60 秒" not in html
    assert "invite-countdown-panel" not in html
    assert "INVITE_COUNTDOWN_SECONDS" not in js
    assert "function startInviteCountdown" not in js
    assert "function finishInviteCountdown" not in js
    assert "setInterval" not in auto_claim_block
    assert "PUBLIC_INVITE_CODE" not in js
    assert "INV-VXK44LB9URXY" not in js
    assert "/api/invites/public" in js
    assert "createPublicInvite(channel)" in auto_claim_block
    assert "activateInviteClaim(claim.invite_code, claim)" in auto_claim_block
    assert "inviteInput.value = claim.invite_code" in auto_claim_block
    assert "临时邀请码" in js
    assert "fixed invite" not in js.lower()


def test_alipay_and_free_primary_actions_appear_before_qr_codes():
    html = (WEB / "index.html").read_text()

    alipay_start = html.index('<section id="invite-method-alipay"')
    free_start = html.index('<section id="invite-method-free"')
    modal_start = html.index('<div id="qr-preview-modal"')
    alipay_block = html[alipay_start:free_start]
    free_block = html[free_start:modal_start]

    assert alipay_block.index('data-invite-auto-claim="alipay"') < alipay_block.index(
        'class="qr-scan-panel"'
    )
    assert free_block.index("打开小红书") < free_block.index('class="qr-scan-panel"')
    assert free_block.index('data-invite-auto-claim="free"') < free_block.index(
        'class="qr-scan-panel"'
    )


def test_public_site_qr_codes_are_large_and_previewable():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()
    css = (WEB / "styles.css").read_text()

    assert (WEB / "assets" / "alipay-reward-qr.jpg").read_bytes() == (
        DCOS / "支付宝二维码.jpg"
    ).read_bytes()
    assert (WEB / "assets" / "group-invite-qr.jpg").exists()
    assert html.count("qr-scan-panel") == 2
    assert html.count("data-qr-preview") == 4
    assert "支付宝收款二维码" in html
    assert "加群二维码" in html
    assert "放大查看" in html
    assert "打开原图" in html
    assert "下载保存" in html
    assert 'class="qr-image-button"' in html
    assert 'class="qr-actions"' in html
    assert 'id="qr-preview-modal"' in html
    assert 'id="qr-preview-image"' in html
    assert "function openQrPreview" in js
    assert "function closeQrPreview" in js
    assert ".qr-scan-image" in css
    assert "min-height: min(64svh, 720px);" in css
    assert ".qr-preview-modal" in css


def test_public_site_has_single_invite_entry_point_after_invite_gate():
    html = (WEB / "index.html").read_text()

    assert html.count("<form ") == 1
    assert html.count('name="invite-code"') == 1
    assert 'id="invite-form"' in html
    assert "data-invite-auto-claim" in html
    assert "data-focus-invite" in html


def test_public_site_invite_gate_is_full_screen_before_repair_workspace():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()
    js = (WEB / "app.js").read_text()

    assert 'id="invite-gate"' in html
    assert 'class="invite-gate-screen"' in html
    assert 'class="guide-layout" hidden' in html
    assert "aria-labelledby=\"invite-gate-title\"" in html
    assert "min-height: calc(100svh - var(--topbar-offset));" in css
    assert ".public-page.is-invite-unlocked .invite-gate-screen" in css
    assert ".public-page.is-invite-unlocked .guide-layout" in css
    assert 'document.body.classList.add("is-invite-unlocked")' in js
    assert 'repairWorkspace.hidden = false' in js


def test_public_site_uses_full_screen_card_workspace():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()

    assert '<body class="public-page">' in html
    assert 'class="workspace-intro"' in html
    assert "flow-node" not in html
    assert ".public-page {" in css
    assert "overflow: hidden;" in css
    assert "height: calc(100svh - var(--topbar-offset));" in css
    assert ".wizard-card-deck" in css
    assert ".wizard-card {" in css
    assert "overflow: auto;" in css


def test_public_site_keeps_live_status_visible_on_desktop_and_mobile():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()
    js = (WEB / "app.js").read_text()

    assert 'id="status-sidebar"' in html
    assert 'class="status-sidebar"' in html
    assert 'id="status-drawer-toggle"' in html
    assert 'class="status-drawer-body"' in html
    assert 'id="status-dock-label"' in html
    assert 'id="status-dock-detail"' in html
    assert ".status-sidebar" in css
    assert "position: sticky;" in css
    assert "position: fixed;" in css
    assert "bottom: 12px;" in css
    assert "function updateStatusDock" in js
    assert "statusDrawerToggle?.addEventListener" in js


def test_mobile_status_dock_has_distinct_collapsed_state():
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'class="status-dock-main"' in html
    assert 'class="status-dock-meta"' in html
    assert 'class="status-drawer-cue"' in html
    assert 'aria-hidden="true"' in html
    assert ".status-drawer-cue" in css
    assert ".status-sidebar:not(.is-expanded)::before" in css
    assert ".status-sidebar:not(.is-expanded) .status-drawer-toggle" in css
    assert ".status-sidebar.is-expanded .status-drawer-cue" in css
    assert "backdrop-filter: blur(16px);" in css
    assert "box-shadow: 0 18px 50px" in css


def test_mobile_wizard_keeps_step_action_reachable_above_status_dock():
    css = (WEB / "styles.css").read_text()

    assert ".public-page .step-complete-button" in css
    assert "position: sticky;" in css
    assert "bottom: 0;" in css
    assert "z-index: 3;" in css


def test_public_site_final_step_tells_users_to_restore_vpn_after_proxy_cleanup():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert "若你原本有其他网络配置，请自行按原状恢复" in html
    assert "本工具不提供 VPN、翻墙、网络加速或地区访问能力" in html
    assert "若你原本有其他网络配置，请自行按原状恢复" in js
    assert "this tool does not provide VPN, circumvention, acceleration, or regional access capabilities" in js


def test_public_site_uses_clear_step_four_and_five_checklists():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()

    assert "step4.item1" in html
    assert "step4.item2" in html
    assert "step4.item3" in html
    assert "step4.item4" not in html
    assert "强退 Claude App，再重新打开" in html
    assert "保持当前 Wi‑Fi 和 HTTP 代理设置不变" in html
    assert "看到登录入口，或状态出现 /api/account、rewrite、Cookie 删除" in html
    assert "不需要长时间保持修复通道" in html
    assert "step5.item1" in html
    assert "step5.item2" in html
    assert "step5.item3" in html
    assert "step5.item4" not in html
    assert "Wi-Fi 的 HTTP 代理改回“关闭”" in html
    assert "关闭飞行模式，恢复蜂窝网络。若你原本有其他网络配置，请自行按原状恢复" in html
    assert "关闭 mitmproxy 证书“完全信任”" in html
    assert "这一步做完后再继续正常使用 Claude" in html
    assert "Force quit the Claude App, then open it again" in js
    assert "turn the HTTP proxy back to Off" in js
    assert "turn off full trust for the mitmproxy certificate" in js


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


def test_admin_invite_list_has_filters_pagination_and_repair_status():
    html = (WEB / "admin.html").read_text()
    js = (WEB / "admin.js").read_text()
    css = (WEB / "styles.css").read_text()

    assert 'id="invite-filters"' in html
    assert 'id="invite-query"' in html
    assert 'id="invite-status-filter"' in html
    assert 'id="invite-repair-filter"' in html
    assert 'id="invite-pagination"' in html
    assert "修复状态" in html
    assert "来源" in html
    assert "renderPagination" in js
    assert "URLSearchParams" in js
    assert "repair_status" in js
    assert ".admin-filters" in css
    assert ".admin-pagination" in css


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
