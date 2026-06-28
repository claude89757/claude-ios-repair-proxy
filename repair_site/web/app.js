const inviteForm = document.querySelector("#invite-form");
const inviteInput = document.querySelector("#invite-code");
const feedbacks = Array.from(document.querySelectorAll("[data-claim-feedback]"));
const summary = document.querySelector("#device-summary");
const checklist = document.querySelector("#checklist");
const eventTable = document.querySelector("#event-table");
const proxyConfig = document.querySelector("#proxy-config");
const proxyHost = document.querySelector("#proxy-host");
const proxyPort = document.querySelector("#proxy-port");
const proxyCertificateUrl = document.querySelector("#proxy-certificate-url");
const statusRefreshButton = document.querySelector("#status-refresh");
const languageToggle = document.querySelector("#language-toggle");
const stepButtons = Array.from(document.querySelectorAll("[data-step-button]"));
const stepPanels = Array.from(document.querySelectorAll("[data-step-panel]"));
const stepCompleteButtons = Array.from(document.querySelectorAll("[data-step-complete]"));
const statusSidebar = document.querySelector("#status-sidebar");
const statusDrawerToggle = document.querySelector("#status-drawer-toggle");
const statusDockLabel = document.querySelector("#status-dock-label");
const statusDockDetail = document.querySelector("#status-dock-detail");
const inviteGateScreen = document.querySelector("#invite-gate");
const repairWorkspace = document.querySelector("#repair-workspace");
const inviteGateViews = Array.from(document.querySelectorAll("[data-invite-view]"));
const inviteMethodPages = Array.from(document.querySelectorAll(".invite-method-page"));
const inviteMethodSelectButtons = Array.from(document.querySelectorAll("[data-invite-method-select]"));
const inviteMethodPanels = Array.from(document.querySelectorAll("[data-invite-method-panel]"));
const autoClaimButtons = Array.from(document.querySelectorAll("[data-invite-auto-claim]"));
const focusInviteButtons = Array.from(document.querySelectorAll("[data-focus-invite]"));
const copyInviteLinkButtons = Array.from(document.querySelectorAll("[data-copy-invite-link]"));
const inviteBackButtons = Array.from(document.querySelectorAll("[data-invite-back]"));
const qrPreviewButtons = Array.from(document.querySelectorAll("[data-qr-preview]"));
const qrCloseButtons = Array.from(document.querySelectorAll("[data-qr-close]"));
const qrPreviewModal = document.querySelector("#qr-preview-modal");
const qrPreviewTitle = document.querySelector("#qr-preview-title");
const qrPreviewImage = document.querySelector("#qr-preview-image");
const qrPreviewOpen = document.querySelector("#qr-preview-open");
const qrPreviewDownload = document.querySelector("#qr-preview-download");
const INVITE_CACHE_KEY = "claudeRepairInviteCode";
const LANGUAGE_CACHE_KEY = "claudeRepairLanguage";
const PATH_LANGUAGE_PREFIXES = new Set(["en", "zh"]);
const LANGUAGE_PATHS = { en: "/en", zh: "/zh" };
const PUBLIC_INVITE_CODE = "INV-VXK44LB9URXY";

const I18N = {
  zh: {
    "page.title": "Claude iOS 登录卡死修复指南",
    "nav.guide": "修复向导",
    "nav.status": "实时状态",
    "nav.safety": "安全",
    "hero.eyebrow": "iPhone / Claude App / 临时修复代理",
    "hero.title": "Claude iOS 登录卡死修复指南",
    "hero.lede":
      "主要用于账号被 ban、禁用或异常后，Claude iOS 反复出现 “Something went wrong, try again”，删除并重装后仍回不到登录页的场景。按步骤临时连接修复代理，清理旧 session、cookie、routing hint 后立即关闭代理并撤销证书信任。",
    "hero.cta": "开始修复",
    "entry.kicker": "状态入口",
    "entry.title": "验证邀请码并查看临时代理",
    "entry.copy": "使用顶部固定的邀请码栏输入管理员提供的邀请码。验证后页面会显示默认 24 小时失效的专属代理端口和脱敏实时状态。",
    "entry.label": "邀请码",
    "entry.placeholder": "输入邀请码",
    "entry.submit": "验证",
    "flow.phoneScreen": "重新登录",
    "flow.proxyLink": "临时代理",
    "flow.proxy": "修复代理",
    "flow.certLink": "证书信任",
    "flow.cert": "CA 证书",
    "guide.kicker": "操作顺序",
    "guide.title": "修复向导",
    "guide.copy": "按卡片逐步操作。每完成一步点击“我已完成，下一步”，右侧实时状态会同步显示代理连接、证书信任和 Claude 请求事件。",
    "step.next": "我已完成，下一步",
    "step.finish": "完成修复",
    "step.statusCurrent": "当前步骤",
    "step.statusDone": "已完成",
    "step.statusWaiting": "等待",
    "step.kickerPrepare": "准备",
    "step.kickerCertificate": "证书",
    "step.kickerNetwork": "网络",
    "step.kickerRepair": "修复",
    "step.kickerFinish": "收尾",
    "step1.title": "获取邀请码",
    "step1.copy": "邀请码验证成功。页面已解锁临时代理配置和修复步骤，请继续安装并信任证书。",
    "step1.taskTitle": "已有邀请码",
    "step1.taskCopy": "如果你已从群公告、群主或闲鱼售后拿到邀请码，请在顶部输入后点击“验证”。验证成功会自动进入下一步。",
    "step1.verifiedTitle": "邀请码已验证",
    "step1.verifiedCopy": "专属代理端口已在右侧状态栏显示。下一步只需要按提示完成证书和 Wi-Fi 代理设置。",
    "inviteGate.eyebrow": "Invite Access / Claude iOS Repair",
    "inviteGate.title": "获取修复邀请码",
    "inviteGate.copy": "选择一个获取方式，按提示拿到邀请码后继续修复。",
    "inviteGate.choiceHint": "闲鱼最推荐；免费方式为自助使用。",
    "inviteGate.back": "返回选择",
    "inviteGate.scopeNote": "仅修复 Claude iOS App 卡 “Something went wrong” 回到登录页；无法帮助解决被封号；不解决梯子或网络问题；公开页面不内置代理账号密码。",
    "inviteGate.limit1": "无法帮助解决被封号、账号恢复或账号申诉问题。",
    "inviteGate.limit2": "不解决梯子或网络问题；修复完成后请清理 Wi-Fi 代理。",
    "inviteGate.limit3": "公开页面不内置代理账号密码，验证成功后才显示临时代理配置和证书链接。",
    "inviteGate.freeLabel": "免费自助",
    "inviteGate.freeTitle": "免费使用",
    "inviteGate.freeBrief": "适合完全自助操作，无售后支持。",
    "inviteGate.freeDetailTitle": "一键三连后自动验证",
    "inviteGate.freeCopy": "适合愿意自助操作的用户。请先去小红书一键三连，点击后会自动填入并验证固定邀请码。",
    "inviteGate.freePageCopy": "先打开小红书完成一键三连，也可扫码进群查看公告。完成后点击按钮自动验证。",
    "inviteGate.selfServe": "自助使用，无售后和远程支持",
    "inviteGate.autoVerify": "点击后自动验证",
    "inviteGate.groupHint": "群公告也会定期更新免费邀请码。",
    "inviteGate.openXhs": "打开小红书",
    "inviteGate.startFree": "已完成一键三连，自动验证",
    "inviteGate.alipayLabel": "支持开发",
    "inviteGate.alipayTitle": "支付宝随缘付费",
    "inviteGate.alipayBrief": "随缘打赏后自动填入固定邀请码。",
    "inviteGate.alipayDetailTitle": "打赏后自动验证",
    "inviteGate.alipayCopy": "适合想支持工具维护，并希望获得远程指导和后续售后技术支持的用户。扫码打赏后点击下方按钮，系统会自动处理邀请码。",
    "inviteGate.alipayPageCopy": "扫码随缘打赏，点击“已打赏”后自动填入邀请码并验证。包含远程指导和后续售后技术支持。",
    "inviteGate.alipayHint": "打赏金额随缘，感谢支持个人开发者维护工具。",
    "inviteGate.remoteSupport": "含远程指导",
    "inviteGate.afterSupport": "含后续售后技术支持",
    "inviteGate.startAlipay": "已打赏，自动验证",
    "inviteGate.xianyuLabel": "售后支持",
    "inviteGate.xianyuTitle": "闲鱼下单购买",
    "inviteGate.xianyuBrief": "适合需要远程指导和售后支持的用户。",
    "inviteGate.xianyuDetailTitle": "闲鱼购买后获取售后邀请码",
    "inviteGate.xianyuCopy": "适合需要售后支持、远程指导和完整协助的用户。购买后按售后指引获取邀请码，再在顶部输入并验证。",
    "inviteGate.xianyuPageCopy": "购买后按售后指引获取邀请码，再在顶部输入并验证。",
    "inviteGate.xianyuCodeLabel": "闲鱼购买链接",
    "inviteGate.openXianyu": "打开闲鱼下单链接",
    "inviteGate.copyXianyu": "复制链接",
    "inviteGate.xianyuFootnote": "此方式不使用固定邀请码；请以下单后的售后邀请码为准。",
    "inviteGate.recommended": "推荐",
    "inviteGate.focusInvite": "去顶部输入邀请码",
    "inviteGate.scanAlipayTitle": "支付宝收款二维码",
    "inviteGate.scanAlipayCopy": "请用支付宝扫码，或放大后保存再打开。",
    "inviteGate.scanGroupTitle": "加群二维码",
    "inviteGate.scanGroupCopy": "群公告会定期更新免费邀请码，可长按保存后扫码。",
    "inviteGate.previewQr": "放大查看",
    "inviteGate.openOriginal": "打开原图",
    "inviteGate.downloadQr": "下载保存",
    "inviteGate.qrPreviewTitle": "二维码预览",
    "inviteGate.closePreview": "关闭",
    "step2.title": "安装并信任证书",
    "step2.item1": '使用 Safari 打开 <a href="/certs/mitmproxy-ca-cert.cer">证书链接</a>，允许下载描述文件。',
    "step2.item2": "进入 <strong>设置 → 通用 → VPN 与设备管理</strong>，确认证书描述文件已经安装。",
    "step2.item3": "进入 <strong>设置 → 通用 → 关于本机 → 证书信任设置</strong>，确认 mitmproxy 证书已经打开“完全信任”。",
    "step3.title": "只让 Wi-Fi 走代理",
    "step3.item1": "打开飞行模式，然后只打开 Wi-Fi，保持蜂窝网络关闭。",
    "step3.item2": "关闭手机上的其它 VPN、代理或梯子工具，否则 Claude 流量可能不会走到修复代理。",
    "step3.item3": "进入当前 Wi-Fi 的信息页，找到 HTTP 代理，选择手动。",
    "step3.item4": "填写页面显示的服务器和端口，认证保持关闭，其余认证字段不用填写。",
    "step4.title": "打开 Claude",
    "step4.item1": "强退 Claude App，再重新打开。",
    "step4.item2": "等待 10-20 秒，保持当前 Wi-Fi 和代理不变。",
    "step4.item3": "看到登录入口，或状态出现 /api/account、rewrite、Cookie 删除，即可下一步；不需要长时间保持代理。",
    "step5.title": "恢复网络",
    "step5.item1": "把当前 Wi-Fi 的 HTTP 代理改回“关闭”。",
    "step5.item2": "关闭飞行模式，恢复蜂窝网络；恢复你日常使用的 VPN、代理或梯子。",
    "step5.item3": "关闭 mitmproxy 证书“完全信任”。这一步做完后再继续正常使用 Claude。",
    "status.title": "实时状态",
    "status.refresh": "刷新状态",
    "status.copy": "邀请码验证后，这里会显示你的专属代理端口、脱敏状态和事件元数据。正常已登录的 Claude App 可能只显示代理已连接，不一定触发修复事件。",
    "proxy.kicker": "临时代理配置",
    "proxy.title": "请按以下信息配置当前 Wi-Fi 的 HTTP 代理，认证保持关闭；专属端口默认 24 小时失效",
    "proxy.host": "服务器",
    "proxy.port": "端口",
    "proxy.certUrl": "证书链接",
    "summary.title": "设备状态",
    "summary.connection": "连接状态",
    "summary.certificate": "证书状态",
    "summary.firstSeen": "首次看到",
    "summary.lastSeen": "最后活动",
    "summary.clientIp": "客户端 IP",
    "summary.appVersion": "App 版本",
    "summary.iosVersion": "iOS 版本",
    "summary.deviceId": "设备标识",
    "checklist.title": "检查项",
    "checks.proxy": "代理已连接",
    "checks.cert": "证书已信任并可解密 Claude 请求",
    "checks.account": "已观察到 /api/account",
    "checks.rewrite": "已执行 session_expired rewrite",
    "checks.cookies": "已发送 Cookie 删除 Header",
    "state.complete": "完成",
    "state.wait": "等待",
    "events.title": "Claude 请求事件",
    "events.note": "只显示 Claude/Anthropic 相关连接和请求；普通代理连接不会显示在此表。",
    "events.time": "时间",
    "events.response": "响应",
    "events.cookie": "Cookie 标记",
    "events.tlsUninspected": "TLS 未解密",
    "events.empty": "尚未观察到 Claude/Anthropic 请求；当前只看到代理连接或其他系统流量。",
    "cookie.yes": "yes",
    "cookie.no": "no",
    "safety.kicker": "使用后处理",
    "safety.title": "安全说明",
    "safety.item1": "请只在自己的设备和账号上使用，修复代理只用于清理卡住的本地旧会话，不用于绕过账号限制。",
    "safety.item2": "修复期间不要提交、记录或共享真实 Cookie、sessionKey、routingHint、Authorization、mitmproxy 证书或设备标识。",
    "safety.item3": "服务端只记录脱敏状态和事件元数据，不记录 Cookie、请求体或完整设备标识。",
    "safety.item4": "完成后关闭 Wi-Fi 代理，并取消修复 CA 的完全信任；专属端口默认 24 小时失效。",
    "safety.item5": "如果状态只显示已连接但没有 Claude 请求，优先检查是否还有其它 VPN、代理或梯子工具未关闭。",
    "safety.item6": "如果状态长期没有变化，先确认 iPhone 当前 Wi-Fi、证书信任和代理配置是否一致。",
    "feedback.restoring": "正在恢复上次的邀请码...",
    "feedback.tokenExpired": "状态凭证已失效，请重新输入邀请码。",
    "feedback.statusUnavailable": "代理配置已显示，但实时状态暂时不可用。",
    "feedback.refreshNeedsInvite": "请先验证邀请码，再刷新实时状态。",
    "feedback.refreshing": "正在刷新实时状态...",
    "feedback.refreshed": "实时状态已刷新。",
    "feedback.loaded": "该邀请码的临时代理配置已加载。",
    "feedback.validating": "正在验证邀请码...",
    "feedback.claimLoaded": "邀请码验证成功，已显示临时代理配置。",
    "feedback.claimConfigLoaded": "邀请码验证成功，临时代理配置已显示。",
    "feedback.invalidInvite": "邀请码无效或已失效。",
    "feedback.claimUnavailable": "暂时无法验证邀请码，请稍后重试。",
    "feedback.enterInvite": "请输入邀请码。",
    "feedback.publicInviteReady": "已填入固定邀请码，正在自动验证。",
    "feedback.xianyuCopied": "闲鱼购买链接已复制。",
    "feedback.xianyuCopyUnavailable": "当前浏览器无法自动复制，请手动复制闲鱼购买链接。",
    "status.waitingInvite": "等待邀请码验证",
    "status.unavailable": "状态暂时不可用",
    "status.processing": "状态数据处理中",
    "status.reconnecting": "正在重新连接状态流",
    "statusValue.not_connected": "not connected",
    "statusValue.connected": "connected",
    "statusValue.unknown": "unknown",
  },
  en: {
    "page.title": "Claude iOS sign-in loop repair guide",
    "nav.guide": "Guide",
    "nav.status": "Live status",
    "nav.safety": "Safety",
    "hero.eyebrow": "iPhone / Claude App / Temporary repair proxy",
    "hero.title": "Claude iOS sign-in loop repair guide",
    "hero.lede":
      'Use this when Claude iOS keeps showing "Something went wrong, try again" after an account ban, disablement, or abnormal session state, and reinstalling the app still does not bring back the sign-in screen. Temporarily route traffic through the repair proxy, clear stale session, cookie, and routing hint state, then turn the proxy and CA trust off immediately.',
    "hero.cta": "Start repair",
    "entry.kicker": "Status entry",
    "entry.title": "Verify invite and view temporary proxy",
    "entry.copy": "Use the sticky invite bar at the top to enter the invite code from the administrator. After verification, this page shows your dedicated proxy port and sanitized live status.",
    "entry.label": "Invite code",
    "entry.placeholder": "Enter invite code",
    "entry.submit": "Verify",
    "flow.phoneScreen": "Sign in again",
    "flow.proxyLink": "Temporary proxy",
    "flow.proxy": "Repair proxy",
    "flow.certLink": "Certificate trust",
    "flow.cert": "CA certificate",
    "guide.kicker": "Order",
    "guide.title": "Repair guide",
    "guide.copy": "Follow the cards one by one. After each task, tap Done and next. The live status panel stays visible with proxy, certificate, and Claude request signals.",
    "step.next": "Done, next",
    "step.finish": "Finish repair",
    "step.statusCurrent": "Current",
    "step.statusDone": "Done",
    "step.statusWaiting": "Waiting",
    "step.kickerPrepare": "Prepare",
    "step.kickerCertificate": "Certificate",
    "step.kickerNetwork": "Network",
    "step.kickerRepair": "Repair",
    "step.kickerFinish": "Finish",
    "step1.title": "Get an invite",
    "step1.copy": "Invite verification succeeded. The temporary proxy configuration and repair steps are unlocked. Continue by installing and trusting the certificate.",
    "step1.taskTitle": "Already have an invite",
    "step1.taskCopy": "If you already received an invite from the group notice, admin, or after-sales support, enter it in the top bar and tap Verify. A successful claim moves you to the next step.",
    "step1.verifiedTitle": "Invite verified",
    "step1.verifiedCopy": "Your dedicated proxy port is shown in the status panel. Next, follow the certificate and Wi-Fi proxy setup steps.",
    "inviteGate.eyebrow": "Invite Access / Claude iOS Repair",
    "inviteGate.title": "Get a repair invite",
    "inviteGate.copy": "Choose one option, follow the prompt, then continue the repair.",
    "inviteGate.choiceHint": "Xianyu is recommended. The free option is self-service.",
    "inviteGate.back": "Back",
    "inviteGate.scopeNote": 'Only fixes the Claude iOS App stuck on "Something went wrong" back to the sign-in screen. It cannot help with banned accounts, tunneling, or network problems. Proxy credentials are never embedded on the public page.',
    "inviteGate.limit1": "It cannot help with banned accounts, account recovery, or appeals.",
    "inviteGate.limit2": "It does not fix tunneling or network problems. Clear the Wi-Fi proxy after repair.",
    "inviteGate.limit3": "The public page does not include proxy credentials. Temporary proxy details appear only after invite verification.",
    "inviteGate.freeLabel": "Free self-service",
    "inviteGate.freeTitle": "Use for free",
    "inviteGate.freeBrief": "For fully self-service use. No after-sales support.",
    "inviteGate.freeDetailTitle": "Auto-verify after the Xiaohongshu action",
    "inviteGate.freeCopy": "Best for users who can operate on their own. Visit Xiaohongshu first, then tap to auto-fill and verify the fixed invite.",
    "inviteGate.freePageCopy": "Open Xiaohongshu first, then scan the group QR if you need the notice. After that, tap the button to auto-verify.",
    "inviteGate.selfServe": "Self-service, no after-sales or remote support",
    "inviteGate.autoVerify": "Auto-verifies after tapping",
    "inviteGate.groupHint": "Free invite codes are also updated in the group notice.",
    "inviteGate.openXhs": "Open Xiaohongshu",
    "inviteGate.startFree": "Done, auto-verify",
    "inviteGate.alipayLabel": "Support the tool",
    "inviteGate.alipayTitle": "Alipay optional tip",
    "inviteGate.alipayBrief": "Tip any amount, then use the fixed invite automatically.",
    "inviteGate.alipayDetailTitle": "Auto-verify after tipping",
    "inviteGate.alipayCopy": "For users who want to support maintenance and receive remote guidance plus follow-up technical support. Scan to tip, then tap below and the page handles the invite.",
    "inviteGate.alipayPageCopy": "Scan to tip any amount, then tap the button to fill and verify the invite automatically. Remote guidance and follow-up technical support are included.",
    "inviteGate.alipayHint": "Any amount is appreciated. Thanks for supporting an independent developer.",
    "inviteGate.remoteSupport": "Remote guidance included",
    "inviteGate.afterSupport": "Follow-up technical support included",
    "inviteGate.startAlipay": "Tipped, auto-verify",
    "inviteGate.xianyuLabel": "After-sales support",
    "inviteGate.xianyuTitle": "Buy on Xianyu",
    "inviteGate.xianyuBrief": "Recommended for remote guidance and after-sales support.",
    "inviteGate.xianyuDetailTitle": "Buy on Xianyu to receive an after-sales invite",
    "inviteGate.xianyuCopy": "For users who need after-sales support, remote guidance, and complete assistance. After purchase, use the invite from support in the top bar.",
    "inviteGate.xianyuPageCopy": "After purchase, use the after-sales invite in the top bar to verify.",
    "inviteGate.xianyuCodeLabel": "Xianyu purchase link",
    "inviteGate.openXianyu": "Open Xianyu order link",
    "inviteGate.copyXianyu": "Copy link",
    "inviteGate.xianyuFootnote": "This option does not use the fixed invite. Use the after-sales invite from your order.",
    "inviteGate.recommended": "Recommended",
    "inviteGate.focusInvite": "Enter invite in top bar",
    "inviteGate.scanAlipayTitle": "Alipay QR code",
    "inviteGate.scanAlipayCopy": "Scan with Alipay, or enlarge and save it first.",
    "inviteGate.scanGroupTitle": "Group QR code",
    "inviteGate.scanGroupCopy": "Free invite codes are updated in the group notice. Long-press or save the image if needed.",
    "inviteGate.previewQr": "Preview",
    "inviteGate.openOriginal": "Open image",
    "inviteGate.downloadQr": "Download",
    "inviteGate.qrPreviewTitle": "QR preview",
    "inviteGate.closePreview": "Close",
    "step2.title": "Install and trust the certificate",
    "step2.item1": 'Open the <a href="/certs/mitmproxy-ca-cert.cer">certificate link</a> in Safari and allow the profile download.',
    "step2.item2": "Go to <strong>Settings → General → VPN & Device Management</strong> and confirm the certificate profile is installed.",
    "step2.item3": "Go to <strong>Settings → General → About → Certificate Trust Settings</strong> and make sure the mitmproxy certificate is fully trusted.",
    "step3.title": "Route only Wi-Fi through the proxy",
    "step3.item1": "Turn on Airplane Mode, then enable Wi-Fi only and keep cellular data off.",
    "step3.item2": "Turn off any other VPN, proxy, or tunneling app on the phone, otherwise Claude traffic may not reach the repair proxy.",
    "step3.item3": "Open the current Wi-Fi details page, find HTTP Proxy, and choose Manual.",
    "step3.item4": "Enter the server and port shown on this page. Keep authentication off and leave the other auth fields empty.",
    "step4.title": "Open Claude",
    "step4.item1": "Force quit the Claude App, then open it again.",
    "step4.item2": "Wait 10-20 seconds and keep the same Wi-Fi and proxy settings.",
    "step4.item3": "If sign-in appears, or status shows /api/account, rewrite, or Cookie deletion, move on. Do not keep the proxy on.",
    "step5.title": "Restore network",
    "step5.item1": "Return to the current Wi-Fi settings and turn the HTTP proxy back to Off.",
    "step5.item2": "Turn off Airplane Mode, restore cellular data, and restore your usual VPN, proxy, or tunneling app.",
    "step5.item3": "In Certificate Trust Settings, turn off full trust for the mitmproxy certificate. Continue using Claude after cleanup.",
    "status.title": "Live status",
    "status.refresh": "Refresh status",
    "status.copy": "After invite verification, this area shows your dedicated proxy port, sanitized status, and event metadata. A normally signed-in Claude App may only show that the proxy is connected and may not trigger repair events.",
    "proxy.kicker": "Temporary proxy configuration",
    "proxy.title": "Configure the current Wi-Fi HTTP proxy with the following values. Keep authentication off. The dedicated port expires after 24 hours by default.",
    "proxy.host": "Server",
    "proxy.port": "Port",
    "proxy.certUrl": "Certificate link",
    "summary.title": "Device status",
    "summary.connection": "Connection",
    "summary.certificate": "Certificate",
    "summary.firstSeen": "First seen",
    "summary.lastSeen": "Last activity",
    "summary.clientIp": "Client IP",
    "summary.appVersion": "App version",
    "summary.iosVersion": "iOS version",
    "summary.deviceId": "Device ID",
    "checklist.title": "Checks",
    "checks.proxy": "Proxy connected",
    "checks.cert": "Certificate trusted and Claude requests decryptable",
    "checks.account": "Observed /api/account",
    "checks.rewrite": "Ran session_expired rewrite",
    "checks.cookies": "Sent Cookie deletion headers",
    "state.complete": "Done",
    "state.wait": "Waiting",
    "events.title": "Claude request events",
    "events.note": "Only Claude/Anthropic connections and requests are shown here. Ordinary proxy connection events are hidden from this table.",
    "events.time": "Time",
    "events.response": "Response",
    "events.cookie": "Cookie marker",
    "events.tlsUninspected": "TLS not decrypted",
    "events.empty": "No Claude/Anthropic request observed yet. Only proxy connections or other system traffic have been seen.",
    "cookie.yes": "yes",
    "cookie.no": "no",
    "safety.kicker": "After use",
    "safety.title": "Safety notes",
    "safety.item1": "Use this only on your own device and account. The repair proxy is for clearing stuck local session state, not for bypassing account restrictions.",
    "safety.item2": "Do not submit, log, or share real Cookie, sessionKey, routingHint, Authorization, mitmproxy certificates, or device identifiers during repair.",
    "safety.item3": "The service stores only sanitized status and event metadata. It does not store cookies, request bodies, or full device identifiers.",
    "safety.item4": "After repair, turn off the Wi-Fi proxy and disable full trust for the repair CA. The dedicated port expires after 24 hours by default.",
    "safety.item5": "If status only shows connected but no Claude requests, first check whether another VPN, proxy, or tunneling app is still enabled.",
    "safety.item6": "If status does not change for a long time, verify the iPhone Wi-Fi, certificate trust, and proxy configuration match this page.",
    "feedback.restoring": "Restoring the last invite code...",
    "feedback.tokenExpired": "The status credential expired. Enter the invite code again.",
    "feedback.statusUnavailable": "Proxy configuration is shown, but live status is temporarily unavailable.",
    "feedback.refreshNeedsInvite": "Verify an invite code before refreshing live status.",
    "feedback.refreshing": "Refreshing live status...",
    "feedback.refreshed": "Live status refreshed.",
    "feedback.loaded": "Temporary proxy configuration for this invite is already loaded.",
    "feedback.validating": "Verifying invite code...",
    "feedback.claimLoaded": "Invite verified. Temporary proxy configuration is shown.",
    "feedback.claimConfigLoaded": "Invite verified. Temporary proxy configuration is shown.",
    "feedback.invalidInvite": "Invite code is invalid or expired.",
    "feedback.claimUnavailable": "Unable to verify the invite right now. Try again later.",
    "feedback.enterInvite": "Enter an invite code.",
    "feedback.publicInviteReady": "Fixed invite filled. Verifying automatically.",
    "feedback.xianyuCopied": "Xianyu purchase link copied.",
    "feedback.xianyuCopyUnavailable": "This browser cannot copy automatically. Copy the Xianyu purchase link manually.",
    "status.waitingInvite": "Waiting for invite verification",
    "status.unavailable": "Status temporarily unavailable",
    "status.processing": "Processing status data",
    "status.reconnecting": "Reconnecting status stream",
    "statusValue.not_connected": "not connected",
    "statusValue.connected": "connected",
    "statusValue.unknown": "unknown",
  },
};

let streamController = null;
let statusToken = "";
let activeInviteCode = "";
let activeProxyPort = "";
let currentLanguage = loadInitialLanguage();
let currentSnapshot = null;
let currentFeedback = { key: "", message: "", tone: "" };
let activeStep = 1;
let lastQrPreviewFocus = null;
const completedSteps = new Set();

const checks = [
  ["proxy", "checks.proxy"],
  ["cert", "checks.cert"],
  ["account", "checks.account"],
  ["rewrite", "checks.rewrite"],
  ["cookies", "checks.cookies"],
];

function initialRepairProgress() {
  return {
    proxy: false,
    cert: false,
    account: false,
    rewrite: false,
    cookies: false,
  };
}

let repairProgress = initialRepairProgress();

function resetRepairProgress() {
  repairProgress = initialRepairProgress();
}

function normalizeLanguage(language) {
  return language === "en" ? "en" : "zh";
}

function loadCachedLanguage() {
  try {
    return normalizeLanguage(localStorage.getItem(LANGUAGE_CACHE_KEY));
  } catch (_error) {
    return "zh";
  }
}

function saveCachedLanguage(language) {
  try {
    localStorage.setItem(LANGUAGE_CACHE_KEY, normalizeLanguage(language));
  } catch (_error) {
    // Language preference is cosmetic; the page still works without storage.
  }
}

function languageFromPath(pathname = window.location.pathname) {
  const prefix = pathname.split("/").filter(Boolean)[0] || "";
  return PATH_LANGUAGE_PREFIXES.has(prefix) ? prefix : "";
}

function pathForLanguage(language) {
  const normalizedLanguage = normalizeLanguage(language);
  const segments = window.location.pathname.split("/").filter(Boolean);

  if (!segments.length) {
    return LANGUAGE_PATHS[normalizedLanguage];
  }

  if (PATH_LANGUAGE_PREFIXES.has(segments[0])) {
    segments[0] = normalizedLanguage;
  } else {
    segments.unshift(normalizedLanguage);
  }

  return `/${segments.join("/")}`;
}

function replaceCurrentPath(pathname) {
  const target = `${pathname}${window.location.search}${window.location.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (target !== current) {
    window.history.replaceState(null, "", target);
  }
}

function pushLanguagePath(language) {
  const target = `${pathForLanguage(language)}${window.location.search}${window.location.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (target !== current) {
    window.history.pushState(null, "", target);
  }
}

function loadInitialLanguage() {
  const pathLanguage = languageFromPath();
  if (!pathLanguage) {
    return loadCachedLanguage();
  }

  saveCachedLanguage(pathLanguage);
  replaceCurrentPath(pathForLanguage(pathLanguage));
  return pathLanguage;
}

function t(key) {
  return I18N[currentLanguage]?.[key] || I18N.zh[key] || key;
}

function translateStatus(value) {
  const raw = text(value);
  const key = `statusValue.${raw.replace(/\s+/g, "_")}`;
  return I18N[currentLanguage]?.[key] || raw;
}

function translateStaticText() {
  document.documentElement.lang = currentLanguage === "en" ? "en" : "zh-CN";
  document.title = t("page.title");
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.innerHTML = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder));
  });
}

function updateLanguageToggle() {
  if (!languageToggle) {
    return;
  }
  languageToggle.textContent = currentLanguage === "en" ? "中文" : "EN";
  languageToggle.setAttribute("aria-pressed", currentLanguage === "en" ? "true" : "false");
}

function refreshDynamicLanguage() {
  if (currentSnapshot) {
    renderSummary(currentSnapshot);
    renderChecklist(currentSnapshot);
    renderEvents(currentSnapshot);
  }
  if (currentFeedback.key) {
    setFeedback(t(currentFeedback.key), currentFeedback.tone, currentFeedback.key);
  }
  updateStepControls();
  updateStatusDock(currentSnapshot);
}

function applyLanguage(language = currentLanguage) {
  currentLanguage = normalizeLanguage(language);
  translateStaticText();
  updateLanguageToggle();
  refreshDynamicLanguage();
}

function setLanguage(language, { updatePath = false } = {}) {
  currentLanguage = normalizeLanguage(language);
  saveCachedLanguage(currentLanguage);
  applyLanguage(currentLanguage);
  if (updatePath) {
    pushLanguagePath(currentLanguage);
  }
}

function text(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function loadCachedInviteCode() {
  try {
    return (localStorage.getItem(INVITE_CACHE_KEY) || "").trim();
  } catch (_error) {
    return "";
  }
}

function saveCachedInviteCode(inviteCode) {
  try {
    localStorage.setItem(INVITE_CACHE_KEY, inviteCode);
  } catch (_error) {
    // Browser storage can be disabled; the repair flow still works without it.
  }
}

function clearCachedInviteCode() {
  try {
    localStorage.removeItem(INVITE_CACHE_KEY);
  } catch (_error) {
    // Ignore storage failures so invalid invites still reset the visible state.
  }
}

function restoreCachedInvite() {
  const inviteCode = loadCachedInviteCode();
  if (!inviteCode) {
    return;
  }

  if (inviteInput) {
    inviteInput.value = inviteCode;
  }
  setFeedbackKey("feedback.restoring", "info");
  void activateInvite(inviteCode, { restored: true });
}

function latestEvent(data) {
  const events = Array.isArray(data?.events) ? data.events : [];
  return events.length ? events[events.length - 1] : {};
}

function replaceChildren(parent, children) {
  parent.replaceChildren(...children);
}

function term(label, value) {
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = label;
  dd.textContent = text(value);
  return [dt, dd];
}

function setFeedback(message = "", tone = "", key = "") {
  currentFeedback = { key, message, tone };
  feedbacks.forEach((node) => {
    node.textContent = message;
    node.dataset.tone = tone;
    node.hidden = !message;
  });
}

function setFeedbackKey(key, tone = "") {
  setFeedback(t(key), tone, key);
}

function setBusy(isBusy) {
  if (!inviteForm) {
    return;
  }
  inviteForm.classList.toggle("is-busy", isBusy);
  const button = inviteForm.querySelector("button");
  if (inviteInput) {
    inviteInput.disabled = isBusy;
  }
  if (button) {
    button.disabled = isBusy;
  }
  if (statusRefreshButton) {
    statusRefreshButton.disabled = isBusy;
  }
}

function setRefreshBusy(isBusy) {
  if (!statusRefreshButton) {
    return;
  }
  statusRefreshButton.disabled = isBusy;
  statusRefreshButton.classList.toggle("is-busy", isBusy);
}

function unlockRepairWorkspace() {
  document.body.classList.add("is-invite-unlocked");
  if (inviteGateScreen) {
    inviteGateScreen.hidden = true;
  }
  if (repairWorkspace) {
    repairWorkspace.hidden = false;
  }
}

function lockRepairWorkspace() {
  document.body.classList.remove("is-invite-unlocked");
  if (inviteGateScreen) {
    inviteGateScreen.hidden = false;
  }
  if (repairWorkspace) {
    repairWorkspace.hidden = true;
  }
  resetInviteGateView();
}

function setAutoClaimBusy(isBusy) {
  autoClaimButtons.forEach((button) => {
    button.disabled = isBusy;
    button.classList.toggle("is-busy", isBusy);
  });
}

function showInviteGateView(view = "choice") {
  const targetView = inviteGateViews.some((item) => item.dataset.inviteView === view)
    ? view
    : "choice";

  inviteGateViews.forEach((item) => {
    item.hidden = item.dataset.inviteView !== targetView;
  });
  inviteMethodPages.forEach((page) => {
    page.classList.toggle("is-active", page.dataset.inviteView === targetView);
  });
  inviteMethodSelectButtons.forEach((button) => {
    const isSelected = button.dataset.inviteMethodSelect === targetView;
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", isSelected ? "true" : "false");
  });

  if (inviteGateScreen) {
    inviteGateScreen.dataset.activeView = targetView;
    inviteGateScreen.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function resetInviteGateView() {
  showInviteGateView("choice");
}

function selectInviteMethod(method) {
  showInviteGateView(method || "xianyu");
}

function autoClaimPublicInvite(channel = "free") {
  showInviteGateView(channel);
  if (inviteInput) {
    inviteInput.value = PUBLIC_INVITE_CODE;
  }
  setFeedbackKey("feedback.publicInviteReady", "info");
  setAutoClaimBusy(true);
  void activateInvite(PUBLIC_INVITE_CODE).finally(() => {
    setAutoClaimBusy(false);
  });
}

function focusInviteInput() {
  inviteInput?.scrollIntoView({ behavior: "smooth", block: "center" });
  inviteInput?.focus({ preventScroll: true });
}

async function copyInviteLink(button) {
  const value = button.dataset.copyValue || "";
  if (!value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(value);
    setFeedbackKey("feedback.xianyuCopied", "success");
  } catch (_error) {
    setFeedback(`${t("feedback.xianyuCopyUnavailable")} ${value}`, "info");
  }
}

function openQrPreview(trigger) {
  const source = trigger?.dataset?.qrPreview || "";
  if (!source || !qrPreviewModal || !qrPreviewImage) {
    return;
  }

  const title = trigger.dataset.qrTitle || t("inviteGate.qrPreviewTitle");
  lastQrPreviewFocus = document.activeElement;
  qrPreviewImage.src = source;
  qrPreviewImage.alt = title;
  if (qrPreviewTitle) {
    qrPreviewTitle.textContent = title;
  }
  if (qrPreviewOpen) {
    qrPreviewOpen.href = source;
  }
  if (qrPreviewDownload) {
    qrPreviewDownload.href = source;
  }
  qrPreviewModal.hidden = false;
  document.body.classList.add("has-qr-preview");
  qrPreviewModal.querySelector("[data-qr-close]")?.focus({ preventScroll: true });
}

function closeQrPreview() {
  if (!qrPreviewModal) {
    return;
  }

  qrPreviewModal.hidden = true;
  document.body.classList.remove("has-qr-preview");
  if (qrPreviewImage) {
    qrPreviewImage.removeAttribute("src");
    qrPreviewImage.alt = "";
  }
  if (qrPreviewTitle) {
    qrPreviewTitle.textContent = t("inviteGate.qrPreviewTitle");
  }
  lastQrPreviewFocus?.focus?.({ preventScroll: true });
  lastQrPreviewFocus = null;
}

function stepNumber(value) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 1;
  }
  return Math.min(Math.max(parsed, 1), Math.max(stepPanels.length, 1));
}

function updateStepControls() {
  stepButtons.forEach((button) => {
    const step = stepNumber(button.dataset.stepButton);
    const isActive = step === activeStep;
    const isComplete = completedSteps.has(step);
    button.classList.toggle("is-active", isActive);
    button.classList.toggle("is-complete", isComplete);
    if (isActive) {
      button.setAttribute("aria-current", "step");
    } else {
      button.removeAttribute("aria-current");
    }

    const status = button.querySelector("small");
    if (status) {
      status.textContent = isActive
        ? t("step.statusCurrent")
        : isComplete
          ? t("step.statusDone")
          : t("step.statusWaiting");
    }
  });

  stepPanels.forEach((panel) => {
    const step = stepNumber(panel.dataset.stepPanel);
    const isActive = step === activeStep;
    panel.hidden = !isActive;
    panel.classList.toggle("is-active", isActive);
    panel.classList.toggle("is-complete", completedSteps.has(step));
  });
}

function setActiveStep(step) {
  activeStep = stepNumber(step);
  updateStepControls();
}

function markStepComplete(step, { advance = true } = {}) {
  const nextStep = stepNumber(step);
  completedSteps.add(nextStep);
  if (advance && nextStep < stepPanels.length) {
    setActiveStep(nextStep + 1);
  } else {
    updateStepControls();
  }
}

function connectionValue(data) {
  if (data?.connection_status_key) {
    return t(data.connection_status_key);
  }
  return translateStatus(data?.connection_status || "not connected");
}

function updateStatusDock(data = currentSnapshot) {
  if (statusDockLabel) {
    statusDockLabel.textContent = t("status.title");
  }
  if (!statusDockDetail) {
    return;
  }

  const connection = connectionValue(data || {});
  const detail = activeProxyPort
    ? `${t("proxy.port")} ${activeProxyPort} · ${connection}`
    : connection;
  statusDockDetail.textContent = detail;
  statusSidebar?.classList.toggle("has-token", Boolean(statusToken));
  statusSidebar?.classList.toggle("is-connected", data?.connection_status === "connected");
}

function renderSummary(data) {
  const latest = latestEvent(data);
  const connectionStatus = connectionValue(data);
  const fields = [
    [t("summary.connection"), connectionStatus],
    [t("summary.certificate"), translateStatus(data?.certificate_status || "unknown")],
    [t("summary.firstSeen"), data?.first_seen_at],
    [t("summary.lastSeen"), data?.last_seen_at],
    [t("summary.clientIp"), latest.client_ip],
    [t("summary.appVersion"), latest.claude_app_version],
    [t("summary.iosVersion"), latest.ios_version],
    [t("summary.deviceId"), latest.device_id_hash],
  ];
  replaceChildren(summary, fields.flatMap(([label, value]) => term(label, value)));
}

function observedChecklistState(data) {
  const events = Array.isArray(data?.events) ? data.events : [];
  return {
    proxy: data?.connection_status === "connected",
    cert: data?.certificate_status === "trusted",
    account: events.some((event) => event.path === "/api/account"),
    rewrite: events.some((event) => event.rewrite_applied === true),
    cookies: events.some((event) => event.cookie_deletion_headers_sent === true),
  };
}

function mergeRepairProgress(data) {
  const observed = observedChecklistState(data);
  Object.keys(repairProgress).forEach((key) => {
    repairProgress[key] = Boolean(repairProgress[key] || observed[key]);
  });
  return repairProgress;
}

function renderChecklist(data) {
  const state = mergeRepairProgress(data);

  const items = checks.map(([key, labelKey]) => {
    const li = document.createElement("li");
    const labelSpan = document.createElement("span");
    const stateSpan = document.createElement("span");
    labelSpan.textContent = t(labelKey);
    stateSpan.className = `check-state ${state[key] ? "yes" : "no"}`;
    stateSpan.textContent = state[key] ? t("state.complete") : t("state.wait");
    li.append(labelSpan, stateSpan);
    return li;
  });

  replaceChildren(checklist, items);
}

function cookieSummary(event) {
  const session = event?.session_key_present
    ? `sessionKey ${t("cookie.yes")}`
    : `sessionKey ${t("cookie.no")}`;
  const routing = event?.routing_hint_present
    ? `routingHint ${t("cookie.yes")}`
    : `routingHint ${t("cookie.no")}`;
  return `${session} / ${routing}`;
}

function isClaudeEvent(event) {
  return event?.type === "claude_connect" || event?.type === "claude_request";
}

function eventPathSummary(event) {
  if (event?.type === "claude_connect") {
    return `CONNECT ${text(event.host)}`;
  }
  return text(event?.path);
}

function eventRewriteSummary(event) {
  if (event?.type === "claude_connect") {
    return "-";
  }
  return event?.rewrite_applied ? "yes" : "no";
}

function eventCookieSummary(event) {
  if (event?.type === "claude_connect") {
    return t("events.tlsUninspected");
  }
  return cookieSummary(event);
}

function renderEvents(data) {
  const rows = (Array.isArray(data?.events) ? data.events : [])
    .filter(isClaudeEvent)
    .slice(-20)
    .reverse();
  const elements = rows.map((event) => {
    const tr = document.createElement("tr");
    [
      text(event.timestamp),
      eventPathSummary(event),
      text(event.response_status),
      eventRewriteSummary(event),
      eventCookieSummary(event),
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });
    return tr;
  });

  if (!elements.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.textContent = t("events.empty");
    tr.appendChild(td);
    elements.push(tr);
  }

  replaceChildren(eventTable, elements);
}

function render(data) {
  currentSnapshot = data || {};
  renderSummary(data || {});
  renderChecklist(data || {});
  renderEvents(data || {});
  updateStatusDock(data || {});
}

function setCertificateLink(url) {
  if (!proxyCertificateUrl) {
    return;
  }

  if (!url) {
    proxyCertificateUrl.textContent = "-";
    return;
  }

  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noreferrer noopener";
  link.textContent = url;
  replaceChildren(proxyCertificateUrl, [link]);
}

function renderProxyConfig(claim) {
  if (!proxyConfig) {
    return;
  }

  proxyConfig.hidden = false;
  activeProxyPort = text(claim?.proxy_port, "");
  if (proxyHost) {
    proxyHost.textContent = text(claim?.proxy_host);
  }
  if (proxyPort) {
    proxyPort.textContent = text(claim?.proxy_port);
  }
  setCertificateLink(claim?.certificate_url);
  updateStatusDock(currentSnapshot);
}

function resetProxyConfig() {
  activeProxyPort = "";
  if (proxyConfig) {
    proxyConfig.hidden = true;
  }
  if (proxyHost) {
    proxyHost.textContent = "-";
  }
  if (proxyPort) {
    proxyPort.textContent = "-";
  }
  setCertificateLink("");
  updateStatusDock(currentSnapshot);
}

function closeStream() {
  if (streamController) {
    streamController.abort();
    streamController = null;
  }
}

function renderWaitingState(statusKey) {
  render({
    connection_status: t(statusKey),
    connection_status_key: statusKey,
    certificate_status: "unknown",
    events: [],
  });
}

async function readJson(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return await response.json();
  } catch (_error) {
    return null;
  }
}

async function claimInvite(inviteCode) {
  const response = await fetch("/api/invites/claim", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ invite_code: inviteCode }),
  });
  const payload = await readJson(response);

  if (!response.ok) {
    const error = new Error("claim failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload || {};
}

async function loadSnapshot() {
  const response = await fetch("/api/invites/me/status", {
    headers: {
      Accept: "application/json",
      "x-status-token": statusToken,
    },
  });

  if (!response.ok) {
    const error = new Error("snapshot failed");
    error.status = response.status;
    throw error;
  }

  return response.json();
}

function expireTokenState() {
  statusToken = "";
  activeInviteCode = "";
  resetRepairProgress();
  lockRepairWorkspace();
  closeStream();
}

async function refreshSnapshot({ silent = false } = {}) {
  try {
    render(await loadSnapshot());
    return true;
  } catch (error) {
    if (error?.status === 401) {
      expireTokenState();
      setFeedbackKey("feedback.tokenExpired", "error");
    } else if (!silent) {
      setFeedbackKey("feedback.statusUnavailable", "info");
    }

    renderWaitingState("status.unavailable");
    return false;
  }
}

async function refreshStatusManually() {
  if (!statusToken) {
    setFeedbackKey("feedback.refreshNeedsInvite", "error");
    renderWaitingState("status.waitingInvite");
    return;
  }

  setRefreshBusy(true);
  setFeedbackKey("feedback.refreshing", "info");
  try {
    const refreshed = await refreshSnapshot();
    if (refreshed && statusToken) {
      setFeedbackKey("feedback.refreshed", "success");
      startEventStream();
    }
  } finally {
    setRefreshBusy(false);
  }
}

function handleSseBlock(block) {
  let eventType = "message";
  const dataLines = [];

  block.split(/\r?\n/).forEach((line) => {
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  });

  const data = dataLines.join("\n");
  if (eventType === "snapshot") {
    try {
      render(JSON.parse(data));
    } catch (_error) {
      renderWaitingState("status.processing");
    }
    return;
  }

  if (eventType === "update") {
    void refreshSnapshot({ silent: true });
  }
}

async function consumeStatusStream(signal) {
  try {
    const response = await fetch("/api/invites/me/events", {
      headers: {
        Accept: "text/event-stream",
        "x-status-token": statusToken,
      },
      signal,
    });

    if (!response.ok || !response.body) {
      if (response.status === 401) {
        expireTokenState();
        setFeedbackKey("feedback.tokenExpired", "error");
      } else {
        renderWaitingState("status.reconnecting");
      }
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary).trim();
        buffer = buffer.slice(boundary + 2);
        if (block) {
          handleSseBlock(block);
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
  } catch (error) {
    if (error?.name !== "AbortError") {
      renderWaitingState("status.reconnecting");
    }
  }
}

function startEventStream() {
  closeStream();
  if (!statusToken) {
    return;
  }

  streamController = new AbortController();
  void consumeStatusStream(streamController.signal);
}

async function activateInvite(inviteCode, { restored = false } = {}) {
  if (activeInviteCode === inviteCode && statusToken) {
    setFeedbackKey("feedback.loaded", "success");
    await refreshSnapshot();
    startEventStream();
    return;
  }

  resetRepairProgress();
  setBusy(true);
  setFeedbackKey(restored ? "feedback.restoring" : "feedback.validating", "info");

  try {
    const claim = await claimInvite(inviteCode);
    if (typeof claim.status_token !== "string" || !claim.status_token) {
      throw new Error("missing status token");
    }

    saveCachedInviteCode(inviteCode);
    statusToken = claim.status_token;
    activeInviteCode = inviteCode;
    renderProxyConfig(claim);
    unlockRepairWorkspace();
    markStepComplete(1);

    const snapshotLoaded = await refreshSnapshot({ silent: true });
    if (snapshotLoaded) {
      setFeedbackKey("feedback.claimLoaded", "success");
    } else if (statusToken) {
      setFeedbackKey("feedback.claimConfigLoaded", "success");
    }

    startEventStream();
    if (!restored) {
      document.querySelector("#guide")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    expireTokenState();
    resetProxyConfig();

    if (error?.status === 400 || error?.status === 404) {
      clearCachedInviteCode();
      setFeedbackKey("feedback.invalidInvite", "error");
    } else {
      setFeedbackKey("feedback.claimUnavailable", "error");
    }

    renderWaitingState("status.waitingInvite");
  } finally {
    setBusy(false);
  }
}

inviteForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const inviteCode = inviteInput?.value.trim();

  if (!inviteCode) {
    setFeedbackKey("feedback.enterInvite", "error");
    return;
  }

  void activateInvite(inviteCode);
});

autoClaimButtons.forEach((button) => {
  button.addEventListener("click", () => {
    autoClaimPublicInvite(button.dataset.inviteAutoClaim || "free");
  });
});

inviteMethodSelectButtons.forEach((button) => {
  button.addEventListener("click", () => {
    selectInviteMethod(button.dataset.inviteMethodSelect);
  });
});

inviteBackButtons.forEach((button) => {
  button.addEventListener("click", resetInviteGateView);
});

focusInviteButtons.forEach((button) => {
  button.addEventListener("click", focusInviteInput);
});

copyInviteLinkButtons.forEach((button) => {
  button.addEventListener("click", () => {
    void copyInviteLink(button);
  });
});

qrPreviewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    openQrPreview(button);
  });
});

qrCloseButtons.forEach((button) => {
  button.addEventListener("click", closeQrPreview);
});

statusRefreshButton?.addEventListener("click", () => {
  void refreshStatusManually();
});

stepButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setActiveStep(button.dataset.stepButton);
  });
});

stepCompleteButtons.forEach((button) => {
  button.addEventListener("click", () => {
    markStepComplete(button.dataset.stepComplete);
    document.querySelector("#guide")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

statusDrawerToggle?.addEventListener("click", () => {
  const isExpanded = statusSidebar?.classList.toggle("is-expanded") || false;
  statusDrawerToggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
});

languageToggle?.addEventListener("click", () => {
  setLanguage(currentLanguage === "en" ? "zh" : "en", { updatePath: true });
});

window.addEventListener("popstate", () => {
  const pathLanguage = languageFromPath();
  setLanguage(pathLanguage || loadCachedLanguage());
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && qrPreviewModal && !qrPreviewModal.hidden) {
    closeQrPreview();
  }
});

applyLanguage(currentLanguage);
lockRepairWorkspace();
setActiveStep(1);
resetProxyConfig();
setFeedback("");
renderWaitingState("status.waitingInvite");
restoreCachedInvite();
