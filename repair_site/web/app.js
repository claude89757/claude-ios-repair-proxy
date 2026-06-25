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
const INVITE_CACHE_KEY = "claudeRepairInviteCode";

let streamController = null;
let statusToken = "";
let activeInviteCode = "";

const checks = [
  ["proxy", "代理已连接"],
  ["cert", "证书已信任并可解密 Claude 请求"],
  ["account", "已观察到 /api/account"],
  ["rewrite", "已执行 session_expired rewrite"],
  ["cookies", "已发送 Cookie 删除 Header"],
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
  setFeedback("正在恢复上次的邀请码...", "info");
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

function setFeedback(message = "", tone = "") {
  feedbacks.forEach((node) => {
    node.textContent = message;
    node.dataset.tone = tone;
    node.hidden = !message;
  });
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

function renderSummary(data) {
  const latest = latestEvent(data);
  const fields = [
    ["连接状态", data?.connection_status || "not connected"],
    ["证书状态", data?.certificate_status || "unknown"],
    ["首次看到", data?.first_seen_at],
    ["最后活动", data?.last_seen_at],
    ["客户端 IP", latest.client_ip],
    ["App 版本", latest.claude_app_version],
    ["iOS 版本", latest.ios_version],
    ["设备标识", latest.device_id_hash],
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

  const items = checks.map(([key, label]) => {
    const li = document.createElement("li");
    const labelSpan = document.createElement("span");
    const stateSpan = document.createElement("span");
    labelSpan.textContent = label;
    stateSpan.className = `check-state ${state[key] ? "yes" : "no"}`;
    stateSpan.textContent = state[key] ? "完成" : "等待";
    li.append(labelSpan, stateSpan);
    return li;
  });

  replaceChildren(checklist, items);
}

function cookieSummary(event) {
  const session = event?.session_key_present ? "sessionKey yes" : "sessionKey no";
  const routing = event?.routing_hint_present ? "routingHint yes" : "routingHint no";
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
    return "TLS 未解密";
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
    td.textContent = "尚未观察到 Claude/Anthropic 请求；当前只看到代理连接或其他系统流量。";
    tr.appendChild(td);
    elements.push(tr);
  }

  replaceChildren(eventTable, elements);
}

function render(data) {
  renderSummary(data || {});
  renderChecklist(data || {});
  renderEvents(data || {});
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
  if (proxyHost) {
    proxyHost.textContent = text(claim?.proxy_host);
  }
  if (proxyPort) {
    proxyPort.textContent = text(claim?.proxy_port);
  }
  setCertificateLink(claim?.certificate_url);
}

function resetProxyConfig() {
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
}

function closeStream() {
  if (streamController) {
    streamController.abort();
    streamController = null;
  }
}

function renderWaitingState(label) {
  render({
    connection_status: label,
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
  closeStream();
}

async function refreshSnapshot({ silent = false } = {}) {
  try {
    render(await loadSnapshot());
    return true;
  } catch (error) {
    if (error?.status === 401) {
      expireTokenState();
      setFeedback("状态凭证已失效，请重新输入邀请码。", "error");
    } else if (!silent) {
      setFeedback("代理配置已显示，但实时状态暂时不可用。", "info");
    }

    renderWaitingState("状态暂时不可用");
    return false;
  }
}

async function refreshStatusManually() {
  if (!statusToken) {
    setFeedback("请先验证邀请码，再刷新实时状态。", "error");
    renderWaitingState("等待邀请码验证");
    return;
  }

  setRefreshBusy(true);
  setFeedback("正在刷新实时状态...", "info");
  try {
    const refreshed = await refreshSnapshot();
    if (refreshed && statusToken) {
      setFeedback("实时状态已刷新。", "success");
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
      renderWaitingState("状态数据处理中");
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
        setFeedback("状态凭证已失效，请重新输入邀请码。", "error");
      } else {
        renderWaitingState("正在重新连接状态流");
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
      renderWaitingState("正在重新连接状态流");
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
    setFeedback("该邀请码的临时代理配置已加载。", "success");
    await refreshSnapshot();
    startEventStream();
    return;
  }

  resetRepairProgress();
  setBusy(true);
  setFeedback(restored ? "正在恢复上次的邀请码..." : "正在验证邀请码...", "info");

  try {
    const claim = await claimInvite(inviteCode);
    if (typeof claim.status_token !== "string" || !claim.status_token) {
      throw new Error("missing status token");
    }

    saveCachedInviteCode(inviteCode);
    statusToken = claim.status_token;
    activeInviteCode = inviteCode;
    renderProxyConfig(claim);

    const snapshotLoaded = await refreshSnapshot({ silent: true });
    if (snapshotLoaded) {
      setFeedback("邀请码验证成功，已显示临时代理配置。", "success");
    } else if (statusToken) {
      setFeedback("邀请码验证成功，临时代理配置已显示。", "success");
    }

    startEventStream();
  } catch (error) {
    expireTokenState();
    resetProxyConfig();

    if (error?.status === 400 || error?.status === 404) {
      clearCachedInviteCode();
      setFeedback("邀请码无效或已失效。", "error");
    } else {
      setFeedback("暂时无法验证邀请码，请稍后重试。", "error");
    }

    renderWaitingState("等待邀请码验证");
  } finally {
    setBusy(false);
  }
}

inviteForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const inviteCode = inviteInput?.value.trim();

  if (!inviteCode) {
    setFeedback("请输入邀请码。", "error");
    return;
  }

  void activateInvite(inviteCode);
  document.querySelector("#status")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

statusRefreshButton?.addEventListener("click", () => {
  void refreshStatusManually();
});

resetProxyConfig();
setFeedback("");
renderWaitingState("等待邀请码验证");
restoreCachedInvite();
