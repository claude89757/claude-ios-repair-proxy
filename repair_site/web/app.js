const forms = [
  document.querySelector("#session-form"),
  document.querySelector("#hero-session-form"),
].filter(Boolean);
const inputs = [
  document.querySelector("#session-id"),
  document.querySelector("#hero-session-id"),
].filter(Boolean);
const summary = document.querySelector("#device-summary");
const checklist = document.querySelector("#checklist");
const eventTable = document.querySelector("#event-table");

let source = null;

const checks = [
  ["proxy", "代理已连接"],
  ["cert", "证书已信任并可解密 Claude 请求"],
  ["account", "已观察到 /api/account"],
  ["rewrite", "已执行 session_expired rewrite"],
  ["cookies", "已发送 Cookie 删除 Header"],
];

function text(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
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

function renderChecklist(data) {
  const events = Array.isArray(data?.events) ? data.events : [];
  const state = {
    proxy: data?.connection_status === "connected",
    cert: data?.certificate_status === "trusted",
    account: events.some((event) => event.path === "/api/account"),
    rewrite: events.some((event) => event.rewrite_applied === true),
    cookies: events.some((event) => event.cookie_deletion_headers_sent === true),
  };

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

function renderEvents(data) {
  const rows = (Array.isArray(data?.events) ? data.events : []).slice(-20).reverse();
  const elements = rows.map((event) => {
    const tr = document.createElement("tr");
    [
      text(event.timestamp),
      text(event.path),
      text(event.response_status),
      event.rewrite_applied ? "yes" : "no",
      cookieSummary(event),
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
    td.textContent = "等待 Claude iOS 请求事件";
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

async function loadSnapshot(sessionId) {
  const response = await fetch(`/api/status/${encodeURIComponent(sessionId)}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`status ${response.status}`);
  }
  return response.json();
}

async function connect(sessionId) {
  if (source) {
    source.close();
  }

  inputs.forEach((input) => {
    input.value = sessionId;
  });

  try {
    render(await loadSnapshot(sessionId));
  } catch (error) {
    render({
      connection_status: "snapshot unavailable",
      certificate_status: "unknown",
      events: [{ path: "/api/status", response_status: error.message }],
    });
  }

  source = new EventSource(`/api/status/${encodeURIComponent(sessionId)}/events`);
  source.addEventListener("snapshot", (event) => {
    render(JSON.parse(event.data));
  });
  source.addEventListener("update", async () => {
    render(await loadSnapshot(sessionId));
  });
  source.onerror = () => {
    render({
      connection_status: "sse reconnecting",
      certificate_status: "unknown",
      events: [],
    });
  };
}

forms.forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const formInput = form.querySelector("input");
    const sessionId = formInput?.value.trim();
    if (sessionId) {
      connect(sessionId);
      document.querySelector("#status")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

render({
  connection_status: "waiting for session",
  certificate_status: "unknown",
  events: [],
});
