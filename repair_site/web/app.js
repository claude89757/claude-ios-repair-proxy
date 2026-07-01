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
const headerProxyChip = document.querySelector("#header-proxy-chip");
const headerProxyHost = document.querySelector("#header-proxy-host");
const headerProxyPort = document.querySelector("#header-proxy-port");
const headerInviteCountdown = document.querySelector("#header-invite-countdown");
const inviteCountdownValue = document.querySelector("#invite-countdown-value");
const statsTotalInvites = document.querySelector("#stats-total-invites");
const statsCompletedRepairs = document.querySelector("#stats-completed-repairs");
const statusRefreshButton = document.querySelector("#status-refresh");
const languageToggle = document.querySelector("#language-toggle");
const languageToggleLabel = languageToggle?.querySelector(".language-toggle-label");
const stepButtons = Array.from(document.querySelectorAll("[data-step-button]"));
const stepPanels = Array.from(document.querySelectorAll("[data-step-panel]"));
const stepCompleteButtons = Array.from(document.querySelectorAll("[data-step-complete]"));
const stepProgressFeedback = document.querySelector("#step-progress-feedback");
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
const proxyCopyButtons = Array.from(document.querySelectorAll("[data-copy-proxy-value]"));
const inviteBackButtons = Array.from(document.querySelectorAll("[data-invite-back]"));
const qrPreviewButtons = Array.from(document.querySelectorAll("[data-qr-preview]"));
const qrCloseButtons = Array.from(document.querySelectorAll("[data-qr-close]"));
const supportEntryButtons = Array.from(document.querySelectorAll("[data-support-entry]"));
const publicLimitCloseButtons = Array.from(document.querySelectorAll("[data-public-limit-close]"));
const qrPreviewModal = document.querySelector("#qr-preview-modal");
const qrPreviewTitle = document.querySelector("#qr-preview-title");
const qrPreviewImage = document.querySelector("#qr-preview-image");
const qrPreviewOpen = document.querySelector("#qr-preview-open");
const qrPreviewDownload = document.querySelector("#qr-preview-download");
const publicLimitModal = document.querySelector("#public-limit-modal");
const repairCompleteModal = document.querySelector("#repair-complete-modal");
const repairCompleteCloseButtons = Array.from(document.querySelectorAll("[data-repair-complete-close]"));
const INVITE_CACHE_KEY = "claudeRepairInviteState";
const LEGACY_INVITE_CACHE_KEY = "claudeRepairInviteCode";
const LANGUAGE_CACHE_KEY = "claudeRepairLanguage";
const PATH_LANGUAGE_PREFIXES = new Set(["en", "zh"]);
const LANGUAGE_PATHS = { en: "/en", zh: "/zh" };

const I18N = {
  zh: {
    "page.title": "Claude iOS 登录卡死修复指南",
    "nav.guide": "修复向导",
    "nav.status": "实时状态",
    "nav.safety": "免责声明",
    "footer.disclaimer": "免责声明",
    "language.switchToEnglish": "切换到英文",
    "hero.eyebrow": "iPhone / Claude App / 本地登录态修复",
    "hero.title": "Claude iOS 登录卡死修复指南",
    "hero.lede":
      "主要用于账号被 ban、禁用或异常后，Claude iOS 反复出现 “Something went wrong, try again”，删除并重装后仍回不到登录页的场景。按步骤临时配置 Wi‑Fi HTTP 修复通道，帮助 Claude iOS 清理本地旧 session、cookie、routing hint。修复完成后请立即关闭 Wi‑Fi HTTP 代理并撤销证书完全信任。",
    "hero.cta": "开始修复",
    "entry.kicker": "状态入口",
    "entry.title": "验证邀请码并查看临时修复通道",
    "entry.copy": "免费入口会生成 30 分钟临时邀请码；打赏入口会生成 1 小时临时邀请码；售后邀请码以管理员设置为准。",
    "entry.label": "邀请码",
    "entry.placeholder": "输入邀请码",
    "entry.submit": "验证",
    "headerProxy.title": "当前修复通道",
    "inviteCountdown.label": "邀请码剩余",
    "inviteCountdown.expired": "已过期",
    "groupEntry.title": "入群",
    "groupEntry.copy": "交流答疑",
    "groupEntry.badge": "微信群",
    "supportEntry.title": "人工",
    "supportEntry.copy": "售后协助",
    "supportEntry.badge": "推荐",
    "flow.phoneScreen": "重新登录",
    "flow.proxyLink": "临时修复通道",
    "flow.proxy": "修复通道",
    "flow.certLink": "证书信任",
    "flow.cert": "CA 证书",
    "guide.kicker": "操作顺序",
    "guide.title": "修复向导",
    "guide.copy": "按卡片逐步操作。每完成一步点击“我已完成，下一步”，右侧实时状态会同步显示修复通道连接、证书信任和 Claude 请求事件。",
    "step.next": "我已完成，下一步",
    "step.finish": "完成修复",
    "step.completedAction": "已完成",
    "step.completedNotice": "第 {step} 步已完成，已进入第 {next} 步。",
    "step.completedFinalNotice": "第 {step} 步已完成。",
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
    "step1.taskCopy": "如果你已从管理员或闲鱼售后拿到邀请码，请在顶部输入后点击“验证”。验证成功会自动进入下一步。",
    "step1.verifiedTitle": "邀请码已验证",
    "step1.verifiedCopy": "专属修复端口已在右侧状态栏显示。下一步只需要按提示完成证书和 Wi‑Fi HTTP 代理设置。",
    "inviteGate.eyebrow": "Invite Access / Claude iOS Repair",
    "inviteGate.title": "选择修复入口",
    "inviteGate.copy": "需要人工协助请选择售后协助；可以自行按步骤操作请选择自助获取。邀请码仅用于生成本次临时修复端口。",
    "inviteGate.choiceHint": "先判断是否需要人工协助，这会让后续选择更简单。",
    "stats.totalLabel": "累计使用",
    "stats.totalCopy": "已生成修复通道",
    "stats.completedLabel": "完成修复",
    "stats.completedCopy": "已记录成功修复",
    "inviteGate.back": "返回选择",
    "inviteGate.scopeNote": "仅用于 Claude iOS App 卡 “Something went wrong” 时回到登录页；无法帮助解决被封号、账号申诉或地区限制问题；不提供 VPN、翻墙、通用代理或网络加速能力。",
    "inviteGate.limit1": "无法帮助解决被封号、账号恢复或账号申诉问题。",
    "inviteGate.limit2": "不提供 VPN、翻墙、通用代理或网络加速能力；修复完成后请清理 Wi‑Fi HTTP 代理。",
    "inviteGate.limit3": "公开页面不内置网络代理账号密码，验证成功后才显示本次修复配置和证书链接。",
    "inviteGate.freeLabel": "免费自助",
    "inviteGate.freeTitle": "免费自助",
    "inviteGate.freeBrief": "适合完全自助操作，无售后支持。",
    "inviteGate.freeDetailTitle": "一键三连后自动验证",
    "inviteGate.freeCopy": "适合愿意自助操作的用户。请先去小红书一键三连，完成后会生成 30 分钟临时邀请码并自动验证。",
    "inviteGate.freePageCopy": "先打开小红书完成一键三连，也可扫码进群查看公告。完成后点击按钮自动验证。",
    "inviteGate.freePathLabel": "方式一",
    "inviteGate.freePathTitle": "小红书一键三连",
    "inviteGate.freePathCopy": "先打开小红书完成一键三连，再点击确认生成邀请码。",
    "inviteGate.selfLabel": "自助操作",
    "inviteGate.selfTitle": "自助获取",
    "inviteGate.selfBrief": "免费使用会生成 30 分钟临时邀请码；请作者喝杯咖啡会生成 1 小时临时邀请码。适合能自行完成证书和 Wi‑Fi 代理设置的用户。",
    "inviteGate.selfDetailTitle": "自助获取临时邀请码",
    "inviteGate.selfPageCopy": "任选一种自助方式：完成小红书一键三连，或请作者喝杯咖啡。免费入口 30 分钟有效，打赏入口 1 小时有效。",
    "inviteGate.selfServe": "自助使用，无售后和远程支持",
    "inviteGate.autoVerify": "点击后自动验证",
    "inviteGate.groupHint": "微信群主要用于交流修复经验。",
    "inviteGate.openXhs": "打开小红书",
    "inviteGate.startFree": "我已一键三连，生成邀请码",
    "inviteGate.alipayLabel": "开源支持",
    "inviteGate.alipayTitle": "请作者喝杯咖啡",
    "inviteGate.alipayBrief": "请作者喝杯咖啡后生成 1 小时临时邀请码。",
    "inviteGate.alipayDetailTitle": "请作者喝杯咖啡",
    "inviteGate.alipayCopy": "适合想支持工具维护，并希望获得远程指导和后续售后技术支持的用户。扫码打赏后点击下方按钮，系统会自动处理邀请码。",
    "inviteGate.alipayPageCopy": "如果工具帮到了你，可以请作者喝杯咖啡支持维护。",
    "inviteGate.coffeePathLabel": "方式二",
    "inviteGate.coffeePathTitle": "请作者喝杯咖啡",
    "inviteGate.coffeePathCopy": "扫码下方支付宝二维码后，点击确认生成邀请码。",
    "inviteGate.alipayHint": "打赏金额随缘，感谢支持个人开发者维护工具。",
    "inviteGate.remoteSupport": "含远程指导",
    "inviteGate.afterSupport": "含后续售后技术支持",
    "inviteGate.startAlipay": "我已请咖啡，生成邀请码",
    "inviteGate.xianyuLabel": "人工支持",
    "inviteGate.xianyuTitle": "售后协助",
    "inviteGate.xianyuBrief": "通过闲鱼获取售后邀请码，适合需要远程指导或后续技术支持的用户。",
    "inviteGate.xianyuDetailTitle": "闲鱼购买后获取售后邀请码",
    "inviteGate.xianyuCopy": "适合需要售后支持、远程指导和完整协助的用户。购买后按售后指引获取邀请码，再在顶部输入并验证。",
    "inviteGate.xianyuPageCopy": "购买后按售后指引获取邀请码，再在顶部输入并验证。",
    "inviteGate.xianyuCodeLabel": "闲鱼购买链接",
    "inviteGate.openXianyu": "去闲鱼获取售后邀请码",
    "inviteGate.copyXianyu": "复制链接",
    "inviteGate.xianyuFootnote": "此方式使用售后邀请码；请以下单后的售后邀请码为准。",
    "inviteGate.recommended": "推荐",
    "inviteGate.focusInvite": "去顶部输入邀请码",
    "inviteGate.scanAlipayTitle": "支付宝二维码",
    "inviteGate.scanAlipayCopy": "可扫码支持维护，完成后点上方按钮自动验证。",
    "inviteGate.scanGroupTitle": "加入微信群",
    "inviteGate.scanGroupCopy": "微信群主要用于交流修复经验。",
    "inviteGate.openGroupQr": "扫码入群交流",
    "inviteGate.previewQr": "放大查看",
    "inviteGate.openOriginal": "打开原图",
    "inviteGate.downloadQr": "下载保存",
    "inviteGate.qrPreviewTitle": "二维码预览",
    "inviteGate.closePreview": "关闭",
    "step2.title": "安装并信任证书",
    "step2.item1": '使用 Safari 打开 <a href="/certs/mitmproxy-ca-cert.cer">证书链接</a>，允许下载描述文件。',
    "step2.item2": "进入 <strong>设置 → 通用 → VPN 与设备管理</strong>，确认证书描述文件已经安装。",
    "step2.item3": "进入 <strong>设置 → 通用 → 关于本机 → 证书信任设置</strong>，确认 mitmproxy 证书已经打开“完全信任”。",
    "step3.title": "配置 Wi‑Fi 修复通道",
    "step3.item1": "打开飞行模式，然后只打开 Wi‑Fi，保持蜂窝网络关闭；关闭手机上的其它 VPN、代理或第三方网络工具，否则 Claude 流量可能不会进入本次修复通道。",
    "step3.item2": "进入 <strong>设置 → Wi‑Fi</strong>，确认已经连接当前 Wi‑Fi。",
    "step3.item3": "在当前 Wi‑Fi 名称右侧，点击 <strong>蓝色圆圈 i / 信息按钮</strong>，进入 Wi‑Fi 信息页。",
    "step3.item4": "向下找到 <strong>HTTP 代理</strong>，选择 <strong>手动</strong>。",
    "step3.item5": "填写 Header 固定显示的 <strong>服务器</strong> 和 <strong>端口</strong>；<strong>认证保持关闭</strong>，其余认证字段不用填写。",
    "step4.title": "打开 Claude",
    "step4.item1": "强退 Claude App，再重新打开。",
    "step4.item2": "等待 10-20 秒，保持当前 Wi‑Fi 和 HTTP 代理设置不变。",
    "step4.item3": "看到登录入口，或状态出现 /api/account、rewrite、Cookie 删除，即可下一步；不需要长时间保持修复通道。",
    "step5.title": "恢复网络",
    "step5.item1": "把当前 Wi-Fi 的 HTTP 代理改回“关闭”。",
    "step5.item2": "关闭飞行模式，恢复蜂窝网络。若你原本有其他网络配置，请自行按原状恢复；本工具不提供 VPN、翻墙、网络加速或地区访问能力。",
    "step5.item3": "关闭 mitmproxy 证书“完全信任”。这一步做完后再继续正常使用 Claude。",
    "status.title": "实时状态",
    "status.refresh": "刷新状态",
    "status.copy": "邀请码验证后，这里会显示你的一次性修复端口、脱敏状态和事件元数据。正常已登录的 Claude App 可能只显示修复通道已连接，不一定触发修复事件。",
    "proxy.kicker": "临时修复通道配置",
    "proxy.title": "请按以下信息填写当前 Wi‑Fi 的 HTTP 代理，认证保持关闭；该端口仅用于本次 Claude iOS 登录态修复，公开入口会短期失效（免费 30 分钟，打赏 1 小时）",
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
    "checks.proxy": "修复通道已连接",
    "checks.cert": "证书已信任并可解密 Claude 请求",
    "checks.account": "已观察到 /api/account",
    "checks.rewrite": "已执行 session_expired rewrite",
    "checks.cookies": "已发送 Cookie 删除 Header",
    "state.complete": "完成",
    "state.wait": "等待",
    "events.title": "Claude 请求事件",
    "events.note": "只显示 Claude/Anthropic 相关连接和请求；与修复无关的普通网络连接不会显示在此表。",
    "events.time": "时间",
    "events.response": "响应",
    "events.cookie": "Cookie 标记",
    "events.tlsUninspected": "TLS 未解密",
    "events.empty": "尚未观察到 Claude/Anthropic 请求；当前只看到代理连接或其他系统流量。",
    "cookie.yes": "yes",
    "cookie.no": "no",
    "safety.kicker": "使用后处理",
    "safety.title": "安全说明",
    "safety.item1": "请只在自己的设备和账号上使用，本工具只用于清理卡住的本地旧会话，不用于绕过账号、地区或网络限制。",
    "safety.item2": "修复期间不要提交、记录或共享真实 Cookie、sessionKey、routingHint、Authorization、mitmproxy 证书或设备标识。",
    "safety.item3": "服务端只记录脱敏状态和事件元数据，不记录 Cookie、请求体或完整设备标识。",
    "safety.item4": "完成后关闭 Wi‑Fi HTTP 代理，并取消修复 CA 的完全信任；公开入口生成的临时端口会短期失效（免费 30 分钟，打赏 1 小时），售后邀请码以管理员设置为准。",
    "safety.item5": "如果状态只显示已连接但没有 Claude 请求，优先检查是否还有其它 VPN、代理或第三方网络工具未关闭。",
    "safety.item6": "如果状态长期没有变化，先确认 iPhone 当前 Wi-Fi、证书信任和代理配置是否一致。",
    "feedback.restoring": "正在恢复上次的邀请码...",
    "feedback.tokenExpired": "状态凭证已失效，请重新输入邀请码。",
    "feedback.statusUnavailable": "修复配置已显示，但实时状态暂时不可用。",
    "feedback.refreshNeedsInvite": "请先验证邀请码，再刷新实时状态。",
    "feedback.refreshing": "正在刷新实时状态...",
    "feedback.refreshed": "实时状态已刷新。",
    "feedback.loaded": "该邀请码的临时修复配置已加载。",
    "feedback.validating": "正在验证邀请码...",
    "feedback.claimLoaded": "邀请码验证成功，已显示临时修复配置。",
    "feedback.claimConfigLoaded": "邀请码验证成功，临时修复配置已显示。",
    "disclaimer.kicker": "免责声明",
    "disclaimer.title": "免责声明",
    "disclaimer.copy": "本工具仅用于用户本人 iPhone 上 Claude iOS App 因本地旧登录态残留导致无法回到登录页的排障与清理。页面显示的临时 Wi‑Fi HTTP 代理配置只服务于该修复流程，默认短期失效；它不是 VPN、翻墙工具、网络加速器、通用代理或跨境联网服务。",
    "disclaimer.item1": "本工具不提供账号解封、账号申诉、地区限制绕过、网络访问加速或第三方网络服务。",
    "disclaimer.item2": "请勿将本工具用于访问与修复无关的网站、App 或服务，也不要用于规避任何平台规则、地区限制、网络管理要求或适用法律法规。",
    "disclaimer.item3": "请只在自己的设备和账号上操作。修复完成后，应立即关闭 Wi‑Fi HTTP 代理，并取消修复 CA 证书的完全信任。",
    "disclaimer.item4": "本项目与 Anthropic、Claude、Apple 无官方关联。使用前请自行确认符合你所在地法律法规及相关服务条款，使用风险由用户自行承担。",
    "feedback.invalidInvite": "邀请码无效或已失效。",
    "feedback.claimUnavailable": "暂时无法验证邀请码，请稍后重试。",
    "feedback.enterInvite": "请输入邀请码。",
    "feedback.publicInviteReadyFree": "正在生成 30 分钟免费临时邀请码并自动验证。",
    "feedback.publicInviteReadyAlipay": "正在生成 1 小时临时邀请码并自动验证。",
    "feedback.freeInviteLimit": "该网络已使用过免费体验名额。如需继续使用，请通过闲鱼获取售后邀请码。",
    "publicLimit.kicker": "Free Invite Limit",
    "publicLimit.title": "免费体验名额已使用",
    "publicLimit.copy": "为了防止临时修复通道被滥用，每个网络 IP 仅可生成一次免费邀请码。若还需要继续使用或需要人工协助，请通过闲鱼获取售后邀请码。",
    "publicLimit.xianyu": "去闲鱼获取售后邀请码",
    "publicLimit.ack": "我知道了",
    "publicLimit.close": "关闭",
    "repairComplete.kicker": "Repair Complete",
    "repairComplete.title": "恭喜，修复已完成",
    "repairComplete.copy": "现在请关闭 Wi‑Fi HTTP 代理，恢复原来的网络，然后强退并重新打开 Claude App。",
    "repairComplete.ack": "我知道了",
    "feedback.xianyuCopied": "闲鱼购买链接已复制。",
    "feedback.xianyuCopyUnavailable": "当前浏览器无法自动复制，请手动复制闲鱼购买链接。",
    "feedback.proxyHostCopied": "服务器已复制。",
    "feedback.proxyPortCopied": "端口已复制。",
    "feedback.proxyCopyUnavailable": "当前浏览器无法自动复制，请手动复制：",
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
    "nav.safety": "Disclaimer",
    "footer.disclaimer": "Disclaimer",
    "language.switchToChinese": "Switch to Chinese",
    "hero.eyebrow": "iPhone / Claude App / Local session repair",
    "hero.title": "Claude iOS sign-in loop repair guide",
    "hero.lede":
      'Use this when Claude iOS keeps showing "Something went wrong, try again" after an account ban, disablement, or abnormal session state, and reinstalling the app still does not bring back the sign-in screen. Temporarily configure the Wi‑Fi HTTP repair channel to help Claude iOS clear stale local session, cookie, and routing hint state. After repair, turn off the Wi‑Fi HTTP proxy and CA trust immediately.',
    "hero.cta": "Start repair",
    "entry.kicker": "Status entry",
    "entry.title": "Verify invite and view the repair channel",
    "entry.copy": "Free self-service invites last 30 minutes. Tip invites last one hour. After-sales invites follow the administrator's setting.",
    "entry.label": "Invite code",
    "entry.placeholder": "Enter invite code",
    "entry.submit": "Verify",
    "headerProxy.title": "Current repair channel",
    "inviteCountdown.label": "Invite left",
    "inviteCountdown.expired": "Expired",
    "groupEntry.title": "Group",
    "groupEntry.copy": "Repair chat",
    "groupEntry.badge": "WeChat",
    "supportEntry.title": "Human",
    "supportEntry.copy": "After-sales",
    "supportEntry.badge": "Help",
    "flow.phoneScreen": "Sign in again",
    "flow.proxyLink": "Repair channel",
    "flow.proxy": "Repair channel",
    "flow.certLink": "Certificate trust",
    "flow.cert": "CA certificate",
    "guide.kicker": "Order",
    "guide.title": "Repair guide",
    "guide.copy": "Follow the cards one by one. After each task, tap Done and next. The live status panel stays visible with repair-channel, certificate, and Claude request signals.",
    "step.next": "Done, next",
    "step.finish": "Finish repair",
    "step.completedAction": "Done",
    "step.completedNotice": "Step {step} is done. Step {next} is now active.",
    "step.completedFinalNotice": "Step {step} is done.",
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
    "step1.taskCopy": "If you already received an invite from the administrator or after-sales support, enter it in the top bar and tap Verify. A successful claim moves you to the next step.",
    "step1.verifiedTitle": "Invite verified",
    "step1.verifiedCopy": "Your dedicated repair port is shown in the status panel. Next, follow the certificate and Wi‑Fi HTTP proxy setup steps.",
    "inviteGate.eyebrow": "Invite Access / Claude iOS Repair",
    "inviteGate.title": "Choose a repair entry",
    "inviteGate.copy": "Choose assisted support if you need help. Choose self-service if you can follow the steps yourself. The invite only creates a temporary repair port for this session.",
    "inviteGate.choiceHint": "Start with whether you need human help; the rest becomes simpler.",
    "stats.totalLabel": "Channels issued",
    "stats.totalCopy": "Temporary repair channels generated",
    "stats.completedLabel": "Repairs completed",
    "stats.completedCopy": "Successful repair records",
    "inviteGate.back": "Back",
    "inviteGate.scopeNote": 'Only helps Claude iOS return to the sign-in screen when stuck on "Something went wrong". It cannot help with banned accounts, appeals, or regional availability. It does not provide VPN, circumvention, general-purpose proxy, or acceleration capabilities.',
    "inviteGate.limit1": "It cannot help with banned accounts, account recovery, or appeals.",
    "inviteGate.limit2": "It does not provide VPN, circumvention, general-purpose proxy, or acceleration capabilities. Clear the Wi‑Fi HTTP proxy after repair.",
    "inviteGate.limit3": "The public page does not include network proxy credentials. Temporary repair details appear only after invite verification.",
    "inviteGate.freeLabel": "Free self-service",
    "inviteGate.freeTitle": "Free self-service",
    "inviteGate.freeBrief": "For fully self-service use. No after-sales support.",
    "inviteGate.freeDetailTitle": "Auto-verify after the Xiaohongshu action",
    "inviteGate.freeCopy": "Best for users who can operate on their own. Visit Xiaohongshu first, then tap to generate a 30-minute temporary invite and verify it automatically.",
    "inviteGate.freePageCopy": "Open Xiaohongshu first, then scan the group QR if you need the notice. After that, tap the button to auto-verify.",
    "inviteGate.freePathLabel": "Option one",
    "inviteGate.freePathTitle": "Xiaohongshu action",
    "inviteGate.freePathCopy": "Open Xiaohongshu first, complete the action, then confirm to generate an invite.",
    "inviteGate.selfLabel": "Self-service",
    "inviteGate.selfTitle": "Self-service",
    "inviteGate.selfBrief": "Free self-service generates a 30-minute invite. Buying the author a coffee generates a one-hour invite. Best if you can handle certificate and Wi‑Fi proxy setup yourself.",
    "inviteGate.selfDetailTitle": "Get a temporary invite yourself",
    "inviteGate.selfPageCopy": "Choose one self-service path: complete the Xiaohongshu action, or buy the author a coffee. Free invites last 30 minutes; tip invites last one hour.",
    "inviteGate.selfServe": "Self-service, no after-sales or remote support",
    "inviteGate.autoVerify": "Auto-verifies after tapping",
    "inviteGate.groupHint": "The WeChat group is mainly for repair discussion.",
    "inviteGate.openXhs": "Open Xiaohongshu",
    "inviteGate.startFree": "Done, generate invite",
    "inviteGate.alipayLabel": "Open-source support",
    "inviteGate.alipayTitle": "Buy the author a coffee",
    "inviteGate.alipayBrief": "Tip any amount, then generate a one-hour temporary invite.",
    "inviteGate.alipayDetailTitle": "Buy the author a coffee",
    "inviteGate.alipayCopy": "For users who want to support maintenance and receive remote guidance plus follow-up technical support. Scan to tip, then tap below and the page handles the invite.",
    "inviteGate.alipayPageCopy": "If this tool helped, you can buy the author a coffee to support maintenance.",
    "inviteGate.coffeePathLabel": "Option two",
    "inviteGate.coffeePathTitle": "Buy the author a coffee",
    "inviteGate.coffeePathCopy": "Scan the Alipay QR code below, then confirm to generate an invite.",
    "inviteGate.alipayHint": "Any amount is appreciated. Thanks for supporting an independent developer.",
    "inviteGate.remoteSupport": "Remote guidance included",
    "inviteGate.afterSupport": "Follow-up technical support included",
    "inviteGate.startAlipay": "Coffee sent, generate invite",
    "inviteGate.xianyuLabel": "Human support",
    "inviteGate.xianyuTitle": "Assisted support",
    "inviteGate.xianyuBrief": "Get an after-sales invite through Xianyu. Recommended if you need remote guidance or follow-up technical support.",
    "inviteGate.xianyuDetailTitle": "Buy on Xianyu to receive an after-sales invite",
    "inviteGate.xianyuCopy": "For users who need after-sales support, remote guidance, and complete assistance. After purchase, use the invite from support in the top bar.",
    "inviteGate.xianyuPageCopy": "After purchase, use the after-sales invite in the top bar to verify.",
    "inviteGate.xianyuCodeLabel": "Xianyu purchase link",
    "inviteGate.openXianyu": "Get an after-sales invite on Xianyu",
    "inviteGate.copyXianyu": "Copy link",
    "inviteGate.xianyuFootnote": "Use the after-sales invite from your order for this option.",
    "inviteGate.recommended": "Recommended",
    "inviteGate.focusInvite": "Enter invite in top bar",
    "inviteGate.scanAlipayTitle": "Alipay QR code",
    "inviteGate.scanAlipayCopy": "Scan to support maintenance, then use the button above to auto-verify.",
    "inviteGate.scanGroupTitle": "Join WeChat group",
    "inviteGate.scanGroupCopy": "The WeChat group is mainly for repair discussion.",
    "inviteGate.openGroupQr": "Scan to join",
    "inviteGate.previewQr": "Preview",
    "inviteGate.openOriginal": "Open image",
    "inviteGate.downloadQr": "Download",
    "inviteGate.qrPreviewTitle": "QR preview",
    "inviteGate.closePreview": "Close",
    "step2.title": "Install and trust the certificate",
    "step2.item1": 'Open the <a href="/certs/mitmproxy-ca-cert.cer">certificate link</a> in Safari and allow the profile download.',
    "step2.item2": "Go to <strong>Settings → General → VPN & Device Management</strong> and confirm the certificate profile is installed.",
    "step2.item3": "Go to <strong>Settings → General → About → Certificate Trust Settings</strong> and make sure the mitmproxy certificate is fully trusted.",
    "step3.title": "Configure the Wi‑Fi repair channel",
    "step3.item1": "Turn on Airplane Mode, enable Wi‑Fi only, and keep cellular data off. Turn off any other VPN, proxy, or third-party network tool on the phone, otherwise Claude traffic may not enter this repair channel.",
    "step3.item2": "Open <strong>Settings → Wi‑Fi</strong> and confirm that the current Wi‑Fi network is connected.",
    "step3.item3": "Tap the <strong>blue circle i / information button</strong> on the right side of the current Wi‑Fi network name to open the Wi‑Fi details page.",
    "step3.item4": "Scroll down to <strong>HTTP Proxy</strong> and choose <strong>Manual</strong>.",
    "step3.item5": "Enter the <strong>Server</strong> and <strong>Port</strong> fixed in the header. Keep <strong>Authentication off</strong> and leave the other auth fields empty.",
    "step4.title": "Open Claude",
    "step4.item1": "Force quit the Claude App, then open it again.",
    "step4.item2": "Wait 10-20 seconds and keep the same Wi‑Fi and HTTP proxy settings.",
    "step4.item3": "If sign-in appears, or status shows /api/account, rewrite, or Cookie deletion, move on. Do not keep the repair channel on.",
    "step5.title": "Restore network",
    "step5.item1": "Return to the current Wi-Fi settings and turn the HTTP proxy back to Off.",
    "step5.item2": "Turn off Airplane Mode and restore cellular data. If you had other network settings before, restore them yourself; this tool does not provide VPN, circumvention, acceleration, or regional access capabilities.",
    "step5.item3": "In Certificate Trust Settings, turn off full trust for the mitmproxy certificate. Continue using Claude after cleanup.",
    "status.title": "Live status",
    "status.refresh": "Refresh status",
    "status.copy": "After invite verification, this area shows your one-time repair port, sanitized status, and event metadata. A normally signed-in Claude App may only show that the repair channel is connected and may not trigger repair events.",
    "proxy.kicker": "Temporary repair channel configuration",
    "proxy.title": "Enter the following values in the current Wi‑Fi HTTP Proxy settings. Keep authentication off. This port is only for this Claude iOS session repair. Public temporary ports expire soon: 30 minutes for free invites, one hour for tip invites.",
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
    "checks.proxy": "Repair channel connected",
    "checks.cert": "Certificate trusted and Claude requests decryptable",
    "checks.account": "Observed /api/account",
    "checks.rewrite": "Ran session_expired rewrite",
    "checks.cookies": "Sent Cookie deletion headers",
    "state.complete": "Done",
    "state.wait": "Waiting",
    "events.title": "Claude request events",
    "events.note": "Only Claude/Anthropic connections and requests are shown here. Ordinary network connections unrelated to repair are hidden from this table.",
    "events.time": "Time",
    "events.response": "Response",
    "events.cookie": "Cookie marker",
    "events.tlsUninspected": "TLS not decrypted",
    "events.empty": "No Claude/Anthropic request observed yet. Only proxy connections or other system traffic have been seen.",
    "cookie.yes": "yes",
    "cookie.no": "no",
    "safety.kicker": "After use",
    "safety.title": "Safety notes",
    "safety.item1": "Use this only on your own device and account. This tool is for clearing stuck local session state, not for bypassing account, regional, or network restrictions.",
    "safety.item2": "Do not submit, log, or share real Cookie, sessionKey, routingHint, Authorization, mitmproxy certificates, or device identifiers during repair.",
    "safety.item3": "The service stores only sanitized status and event metadata. It does not store cookies, request bodies, or full device identifiers.",
    "safety.item4": "After repair, turn off the Wi‑Fi HTTP proxy and disable full trust for the repair CA. Public temporary ports expire soon: 30 minutes for free invites, one hour for tip invites. After-sales invites follow the administrator's setting.",
    "safety.item5": "If status only shows connected but no Claude requests, first check whether another VPN, proxy, or third-party network tool is still enabled.",
    "safety.item6": "If status does not change for a long time, verify the iPhone Wi-Fi, certificate trust, and proxy configuration match this page.",
    "feedback.restoring": "Restoring the last invite code...",
    "feedback.tokenExpired": "The status credential expired. Enter the invite code again.",
    "feedback.statusUnavailable": "Repair configuration is shown, but live status is temporarily unavailable.",
    "feedback.refreshNeedsInvite": "Verify an invite code before refreshing live status.",
    "feedback.refreshing": "Refreshing live status...",
    "feedback.refreshed": "Live status refreshed.",
    "feedback.loaded": "Temporary repair configuration for this invite is already loaded.",
    "feedback.validating": "Verifying invite code...",
    "feedback.claimLoaded": "Invite verified. Temporary repair configuration is shown.",
    "feedback.claimConfigLoaded": "Invite verified. Temporary repair configuration is shown.",
    "disclaimer.kicker": "Disclaimer",
    "disclaimer.title": "Disclaimer",
    "disclaimer.copy": "This tool is only for troubleshooting and clearing stale local sign-in state on the user's own iPhone when Claude iOS cannot return to the sign-in screen. The temporary Wi‑Fi HTTP proxy configuration shown on this page serves only that repair flow and expires by default; it is not a VPN, circumvention tool, accelerator, general-purpose proxy, or cross-border connectivity service.",
    "disclaimer.item1": "This tool does not provide account unbanning, appeals, regional availability bypassing, network acceleration, or third-party network services.",
    "disclaimer.item2": "Do not use this tool to access websites, apps, or services unrelated to the repair, or to bypass platform rules, regional restrictions, network management requirements, or applicable laws and regulations.",
    "disclaimer.item3": "Use it only on your own device and account. After repair, immediately turn off the Wi‑Fi HTTP proxy and disable full trust for the repair CA certificate.",
    "disclaimer.item4": "This project is not officially affiliated with Anthropic, Claude, or Apple. Before use, confirm that your use complies with local laws, regulations, and relevant service terms. You are responsible for your own use.",
    "feedback.invalidInvite": "Invite code is invalid or expired.",
    "feedback.claimUnavailable": "Unable to verify the invite right now. Try again later.",
    "feedback.enterInvite": "Enter an invite code.",
    "feedback.publicInviteReadyFree": "Generating a 30-minute free temporary invite and verifying it automatically.",
    "feedback.publicInviteReadyAlipay": "Generating a one-hour temporary invite and verifying it automatically.",
    "feedback.freeInviteLimit": "This network has already used the free trial invite. To continue, get an after-sales invite on Xianyu.",
    "publicLimit.kicker": "Free Invite Limit",
    "publicLimit.title": "Free trial invite already used",
    "publicLimit.copy": "To prevent temporary repair channels from being abused, each network IP can generate one free invite only. If you still need to continue or want human assistance, please get an after-sales invite on Xianyu.",
    "publicLimit.xianyu": "Get an after-sales invite on Xianyu",
    "publicLimit.ack": "Got it",
    "publicLimit.close": "Close",
    "repairComplete.kicker": "Repair Complete",
    "repairComplete.title": "Repair complete",
    "repairComplete.copy": "Turn off the Wi‑Fi HTTP proxy now, restore your original network, then force quit and reopen the Claude App.",
    "repairComplete.ack": "Got it",
    "feedback.xianyuCopied": "Xianyu purchase link copied.",
    "feedback.xianyuCopyUnavailable": "This browser cannot copy automatically. Copy the Xianyu purchase link manually.",
    "feedback.proxyHostCopied": "Server copied.",
    "feedback.proxyPortCopied": "Port copied.",
    "feedback.proxyCopyUnavailable": "This browser cannot copy automatically. Copy manually:",
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
let activeInviteExpiresAt = "";
let inviteCountdownTimer = null;
let publicStatsTimer = null;
let currentLanguage = loadInitialLanguage();
let currentSnapshot = null;
let currentPublicStats = null;
let currentFeedback = { key: "", message: "", tone: "" };
let activeStep = 1;
let lastCompletedStep = null;
let lastCompletionNextStep = null;
let lastQrPreviewFocus = null;
let lastRepairCompleteFocus = null;
let repairCompleteModalShown = false;
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
  repairCompleteModalShown = false;
  closeRepairCompleteModal({ restoreFocus: false });
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
  const label = currentLanguage === "en" ? t("language.switchToChinese") : t("language.switchToEnglish");
  languageToggle.setAttribute("aria-label", label);
  languageToggle.setAttribute("title", label);
  languageToggle.setAttribute("aria-pressed", currentLanguage === "en" ? "true" : "false");
  if (languageToggleLabel) {
    languageToggleLabel.textContent = label;
  }
}

function refreshDynamicLanguage() {
  if (currentSnapshot) {
    renderSummary(currentSnapshot);
    renderChecklist(currentSnapshot);
    renderEvents(currentSnapshot);
  }
  if (currentPublicStats) {
    renderPublicStats(currentPublicStats);
  }
  if (currentFeedback.key) {
    setFeedback(t(currentFeedback.key), currentFeedback.tone, currentFeedback.key);
  }
  updateInviteCountdown();
  renderStepProgressFeedback();
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

function formatStatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return new Intl.NumberFormat(currentLanguage === "en" ? "en-US" : "zh-CN").format(number);
}

function renderPublicStats(stats = currentPublicStats) {
  if (!stats) {
    return;
  }
  if (statsTotalInvites) {
    statsTotalInvites.textContent = formatStatNumber(stats.total_invites);
  }
  if (statsCompletedRepairs) {
    statsCompletedRepairs.textContent = formatStatNumber(stats.completed_repairs);
  }
}

async function loadPublicStats({ silent = false } = {}) {
  try {
    const response = await fetch("/api/public/stats", {
      headers: {
        Accept: "application/json",
      },
    });
    const payload = await readJson(response);

    if (!response.ok) {
      throw new Error("public stats failed");
    }

    currentPublicStats = payload || {};
    renderPublicStats(currentPublicStats);
  } catch (_error) {
    if (!silent) {
      renderPublicStats(currentPublicStats);
    }
  }
}

function startPublicStatsRefresh() {
  if (!statsTotalInvites && !statsCompletedRepairs) {
    return;
  }
  void loadPublicStats({ silent: true });
  if (publicStatsTimer) {
    window.clearInterval(publicStatsTimer);
  }
  publicStatsTimer = window.setInterval(() => {
    void loadPublicStats({ silent: true });
  }, 30000);
}

function isCachedInviteExpired(state) {
  const expiryTimestamp = Date.parse(state.expires_at);
  return Number.isNaN(expiryTimestamp) || expiryTimestamp <= Date.now();
}

function clearCachedInviteState() {
  try {
    localStorage.removeItem(INVITE_CACHE_KEY);
    localStorage.removeItem(LEGACY_INVITE_CACHE_KEY);
  } catch (_error) {
    // Ignore storage failures so invalid invites still reset the visible state.
  }
}

function loadCachedInviteState() {
  try {
    localStorage.removeItem(LEGACY_INVITE_CACHE_KEY);
    const rawValue = localStorage.getItem(INVITE_CACHE_KEY);
    if (!rawValue) {
      return null;
    }

    const state = JSON.parse(rawValue);
    if (
      !state ||
      typeof state.invite_code !== "string" ||
      typeof state.expires_at !== "string" ||
      !state.invite_code.trim() ||
      isCachedInviteExpired(state)
    ) {
      clearCachedInviteState();
      return null;
    }

    return {
      inviteCode: state.invite_code.trim(),
      expiresAt: state.expires_at,
    };
  } catch (_error) {
    clearCachedInviteState();
    return null;
  }
}

function saveCachedInviteState(inviteCode, expiresAt) {
  const state = {
    invite_code: inviteCode,
    expires_at: expiresAt,
  };
  try {
    if (!inviteCode || !expiresAt || isCachedInviteExpired(state)) {
      clearCachedInviteState();
      return;
    }
    localStorage.setItem(INVITE_CACHE_KEY, JSON.stringify(state));
    localStorage.removeItem(LEGACY_INVITE_CACHE_KEY);
  } catch (_error) {
    // Browser storage can be disabled; the repair flow still works without it.
  }
}

function restoreCachedInvite() {
  if (window.location.hash === "#support") {
    return;
  }

  const cachedInvite = loadCachedInviteState();
  if (!cachedInvite) {
    return;
  }

  if (inviteInput) {
    inviteInput.value = cachedInvite.inviteCode;
  }
  setFeedbackKey("feedback.restoring", "info");
  void activateInvite(cachedInvite.inviteCode, { restored: true });
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

function parseInviteExpiry(expiresAt) {
  if (!expiresAt) {
    return null;
  }
  const timestamp = Date.parse(expiresAt);
  return Number.isNaN(timestamp) ? null : timestamp;
}

function formatInviteRemaining(milliseconds) {
  const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
  if (totalSeconds <= 0) {
    return t("inviteCountdown.expired");
  }

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const paddedMinutes = hours ? String(minutes).padStart(2, "0") : String(minutes);
  const paddedSeconds = String(seconds).padStart(2, "0");
  return hours ? `${hours}:${paddedMinutes}:${paddedSeconds}` : `${paddedMinutes}:${paddedSeconds}`;
}

function updateInviteCountdown() {
  const expiryTimestamp = parseInviteExpiry(activeInviteExpiresAt);
  if (!headerInviteCountdown || !inviteCountdownValue || expiryTimestamp === null) {
    return;
  }

  const remaining = expiryTimestamp - Date.now();
  inviteCountdownValue.textContent = formatInviteRemaining(remaining);
  headerInviteCountdown.classList.toggle("is-warning", remaining > 0 && remaining <= 5 * 60 * 1000);
  headerInviteCountdown.classList.toggle("is-expired", remaining <= 0);
  if (remaining <= 0) {
    clearCachedInviteState();
  }
}

function stopInviteCountdown() {
  if (inviteCountdownTimer) {
    window.clearInterval(inviteCountdownTimer);
    inviteCountdownTimer = null;
  }
  activeInviteExpiresAt = "";
  if (headerInviteCountdown) {
    headerInviteCountdown.hidden = true;
    headerInviteCountdown.classList.remove("is-warning", "is-expired");
  }
  if (inviteCountdownValue) {
    inviteCountdownValue.textContent = "--:--";
  }
}

function startInviteCountdown(expiresAt) {
  stopInviteCountdown();
  if (!headerInviteCountdown || !inviteCountdownValue) {
    return;
  }
  const expiryTimestamp = parseInviteExpiry(expiresAt);
  if (expiryTimestamp === null) {
    return;
  }

  activeInviteExpiresAt = expiresAt;
  headerInviteCountdown.hidden = false;
  updateInviteCountdown();
  inviteCountdownTimer = window.setInterval(updateInviteCountdown, 1000);
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
  setHeaderProxyVisible(false);
  stopInviteCountdown();
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

async function autoClaimPublicInvite(channel = "free") {
  showInviteGateView("self");
  setFeedbackKey(
    channel === "free" ? "feedback.publicInviteReadyFree" : "feedback.publicInviteReadyAlipay",
    "info",
  );
  setBusy(true);
  setAutoClaimBusy(true);

  try {
    const claim = await createPublicInvite(channel);
    if (!claim.invite_code) {
      throw new Error("missing invite code");
    }
    if (inviteInput) {
      inviteInput.value = claim.invite_code;
    }
    await activateInviteClaim(claim.invite_code, claim);
  } catch (error) {
    expireTokenState();
    resetProxyConfig();
    if (isFreeInviteLimitError(error)) {
      setFeedbackKey("feedback.freeInviteLimit", "info");
      openPublicLimitModal();
    } else {
      setFeedbackKey("feedback.claimUnavailable", "error");
    }
    renderWaitingState("status.waitingInvite");
  } finally {
    setBusy(false);
    setAutoClaimBusy(false);
  }
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

async function copyProxyValue(button) {
  const value = button.dataset.copyProxyValue || "";
  if (!value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(value);
    setFeedbackKey(button.dataset.copyFeedbackKey || "feedback.proxyHostCopied", "success");
    button.classList.add("is-copied");
    window.setTimeout(() => {
      button.classList.remove("is-copied");
    }, 1200);
  } catch (_error) {
    setFeedback(`${t("feedback.proxyCopyUnavailable")} ${value}`, "info");
  }
}

function openSupportEntry() {
  document.body.classList.remove("is-invite-unlocked");
  setHeaderProxyVisible(false);
  if (repairWorkspace) {
    repairWorkspace.hidden = true;
  }
  if (inviteGateScreen) {
    inviteGateScreen.hidden = false;
  }
  showInviteGateView("xianyu");
  inviteGateScreen?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openSupportEntryFromHash() {
  if (window.location.hash === "#support") {
    openSupportEntry();
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

function openPublicLimitModal() {
  if (!publicLimitModal) {
    return;
  }
  publicLimitModal.hidden = false;
  document.body.classList.add("has-public-limit-modal");
  publicLimitModal.querySelector("[data-public-limit-close]")?.focus({ preventScroll: true });
}

function closePublicLimitModal() {
  if (!publicLimitModal) {
    return;
  }
  publicLimitModal.hidden = true;
  document.body.classList.remove("has-public-limit-modal");
}

function openRepairCompleteModal() {
  if (!repairCompleteModal || repairCompleteModalShown) {
    return;
  }
  repairCompleteModalShown = true;
  lastRepairCompleteFocus = document.activeElement;
  repairCompleteModal.hidden = false;
  document.body.classList.add("has-repair-complete-modal");
  repairCompleteModal.querySelector("[data-repair-complete-close]")?.focus({ preventScroll: true });
}

function closeRepairCompleteModal({ restoreFocus = true } = {}) {
  if (!repairCompleteModal) {
    return;
  }
  repairCompleteModal.hidden = true;
  document.body.classList.remove("has-repair-complete-modal");
  if (restoreFocus) {
    lastRepairCompleteFocus?.focus?.({ preventScroll: true });
  }
  lastRepairCompleteFocus = null;
}

function errorCode(error) {
  return error?.payload?.detail?.code || error?.payload?.code || "";
}

function isFreeInviteLimitError(error) {
  return error?.status === 409 && errorCode(error) === "free_invite_limit_reached";
}

function stepNumber(value) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 1;
  }
  return Math.min(Math.max(parsed, 1), Math.max(stepPanels.length, 1));
}

function stepMessage(key, values = {}) {
  return t(key)
    .replace("{step}", String(values.step || ""))
    .replace("{next}", String(values.next || ""));
}

function renderStepProgressFeedback() {
  if (!stepProgressFeedback || lastCompletedStep === null) {
    return;
  }
  const key = lastCompletionNextStep ? "step.completedNotice" : "step.completedFinalNotice";
  stepProgressFeedback.textContent = stepMessage(key, {
    step: lastCompletedStep,
    next: lastCompletionNextStep,
  });
  stepProgressFeedback.hidden = false;
}

function announceStepCompletion(step, nextStep = null) {
  lastCompletedStep = step;
  lastCompletionNextStep = nextStep;
  renderStepProgressFeedback();
  if (!stepProgressFeedback) {
    return;
  }
  stepProgressFeedback.classList.remove("is-fresh");
  void stepProgressFeedback.offsetWidth;
  stepProgressFeedback.classList.add("is-fresh");
}

function updateStepControls() {
  stepButtons.forEach((button) => {
    const step = stepNumber(button.dataset.stepButton);
    const isActive = step === activeStep;
    const isComplete = completedSteps.has(step);
    const state = isComplete ? "complete" : isActive ? "current" : "waiting";
    button.classList.toggle("is-active", isActive);
    button.classList.toggle("is-complete", isComplete);
    button.dataset.stepState = state;
    button.setAttribute("aria-pressed", isComplete ? "true" : "false");
    if (isActive) {
      button.setAttribute("aria-current", "step");
    } else {
      button.removeAttribute("aria-current");
    }

    const index = button.querySelector(".step-index");
    if (index) {
      index.textContent = isComplete ? "✓" : String(step);
      index.setAttribute("aria-hidden", "true");
    }

    const status = button.querySelector("small");
    const statusText = isComplete
      ? t("step.statusDone")
      : isActive
        ? t("step.statusCurrent")
        : t("step.statusWaiting");
    if (status) {
      status.textContent = statusText;
    }
    const title = button.querySelector("strong")?.textContent?.trim() || "";
    button.setAttribute("aria-label", `${step} ${title} ${statusText}`.trim());
  });

  stepPanels.forEach((panel) => {
    const step = stepNumber(panel.dataset.stepPanel);
    const isActive = step === activeStep;
    const isComplete = completedSteps.has(step);
    panel.hidden = !isActive;
    panel.classList.toggle("is-active", isActive);
    panel.classList.toggle("is-complete", isComplete);

    const completeButton = panel.querySelector("[data-step-complete]");
    if (completeButton) {
      completeButton.classList.toggle("is-completed", isComplete);
      completeButton.disabled = isComplete;
      completeButton.setAttribute("aria-pressed", isComplete ? "true" : "false");
      completeButton.textContent = isComplete
        ? t("step.completedAction")
        : t(step === stepPanels.length ? "step.finish" : "step.next");
    }
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
    announceStepCompletion(nextStep, nextStep + 1);
  } else {
    updateStepControls();
    announceStepCompletion(nextStep);
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

function isSuccessfulRepairComplete(data) {
  const events = Array.isArray(data?.events) ? data.events : [];
  const hasAccount = repairProgress.account || events.some((event) => event.path === "/api/account");
  const hasRewrite = repairProgress.rewrite || events.some((event) => event.rewrite_applied === true);
  const hasCookieCleanup =
    repairProgress.cookies || events.some((event) => event.cookie_deletion_headers_sent === true);
  return Boolean(hasAccount && hasRewrite && hasCookieCleanup);
}

function maybeShowRepairCompleteModal(data) {
  if (isSuccessfulRepairComplete(data)) {
    openRepairCompleteModal();
  }
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
  maybeShowRepairCompleteModal(data || {});
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

function setHeaderProxyVisible(isVisible) {
  if (headerProxyChip) {
    headerProxyChip.hidden = !isVisible;
  }
  document.body.classList.toggle("has-header-proxy", isVisible);
}

function shouldShowHeaderProxy(host, port) {
  const currentInviteInput = inviteInput?.value.trim() || "";
  return Boolean(
    host &&
      port &&
      activeInviteCode &&
      currentInviteInput === activeInviteCode &&
      document.body.classList.contains("is-invite-unlocked"),
  );
}

function setProxyCopyButtonValue(button, value) {
  if (!button) {
    return;
  }
  const normalizedValue = text(value, "");
  button.dataset.copyProxyValue = normalizedValue;
  button.disabled = !normalizedValue;
}

function renderHeaderProxyConfig(host, port) {
  const normalizedHost = text(host, "");
  const normalizedPort = text(port, "");
  if (headerProxyHost) {
    headerProxyHost.textContent = text(normalizedHost);
  }
  if (headerProxyPort) {
    headerProxyPort.textContent = text(normalizedPort);
  }
  setProxyCopyButtonValue(proxyCopyButtons[0], normalizedHost);
  setProxyCopyButtonValue(proxyCopyButtons[1], normalizedPort);
  setHeaderProxyVisible(shouldShowHeaderProxy(normalizedHost, normalizedPort));
}

function renderProxyConfig(claim) {
  if (!proxyConfig) {
    return;
  }

  proxyConfig.hidden = false;
  const host = text(claim?.proxy_host, "");
  const port = text(claim?.proxy_port, "");
  activeProxyPort = port;
  if (proxyHost) {
    proxyHost.textContent = text(host);
  }
  if (proxyPort) {
    proxyPort.textContent = text(port);
  }
  renderHeaderProxyConfig(host, port);
  setCertificateLink(claim?.certificate_url);
  updateStatusDock(currentSnapshot);
}

function resetProxyConfig() {
  activeProxyPort = "";
  renderHeaderProxyConfig("", "");
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

async function createPublicInvite(channel) {
  const response = await fetch("/api/invites/public", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ channel }),
  });
  const payload = await readJson(response);

  if (!response.ok) {
    const error = new Error("public invite failed");
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
    await activateInviteClaim(inviteCode, claim, { restored });
  } catch (error) {
    expireTokenState();
    resetProxyConfig();

    if (error?.status === 400 || error?.status === 404) {
      clearCachedInviteState();
      setFeedbackKey("feedback.invalidInvite", "error");
    } else {
      setFeedbackKey("feedback.claimUnavailable", "error");
    }

    renderWaitingState("status.waitingInvite");
  } finally {
    setBusy(false);
  }
}

async function activateInviteClaim(inviteCode, claim, { restored = false } = {}) {
  if (typeof claim.status_token !== "string" || !claim.status_token) {
    throw new Error("missing status token");
  }

  saveCachedInviteState(inviteCode, claim.expires_at);
  statusToken = claim.status_token;
  activeInviteCode = inviteCode;
  unlockRepairWorkspace();
  renderProxyConfig(claim);
  startInviteCountdown(claim.expires_at);
  void loadPublicStats({ silent: true });
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
    void autoClaimPublicInvite(button.dataset.inviteAutoClaim || "free");
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

proxyCopyButtons.forEach((button) => {
  button.addEventListener("click", () => {
    void copyProxyValue(button);
  });
});

supportEntryButtons.forEach((button) => {
  button.addEventListener("click", openSupportEntry);
});

qrPreviewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    openQrPreview(button);
  });
});

qrCloseButtons.forEach((button) => {
  button.addEventListener("click", closeQrPreview);
});

publicLimitCloseButtons.forEach((button) => {
  button.addEventListener("click", closePublicLimitModal);
});

repairCompleteCloseButtons.forEach((button) => {
  button.addEventListener("click", () => {
    closeRepairCompleteModal();
  });
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
  openSupportEntryFromHash();
});

window.addEventListener("hashchange", () => {
  openSupportEntryFromHash();
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && qrPreviewModal && !qrPreviewModal.hidden) {
    closeQrPreview();
  }
  if (event.key === "Escape" && publicLimitModal && !publicLimitModal.hidden) {
    closePublicLimitModal();
  }
  if (event.key === "Escape" && repairCompleteModal && !repairCompleteModal.hidden) {
    closeRepairCompleteModal();
  }
});

applyLanguage(currentLanguage);
lockRepairWorkspace();
setActiveStep(1);
resetProxyConfig();
setFeedback("");
renderWaitingState("status.waitingInvite");
startPublicStatsRefresh();
restoreCachedInvite();
openSupportEntryFromHash();
