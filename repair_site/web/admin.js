const loginPanel = document.querySelector("#login-panel");
const workspace = document.querySelector("#admin-workspace");
const loginForm = document.querySelector("#login-form");
const createForm = document.querySelector("#create-form");
const filterForm = document.querySelector("#invite-filters");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-button");
const loginFeedback = document.querySelector("#login-feedback");
const createFeedback = document.querySelector("#create-feedback");
const inviteTable = document.querySelector("#invite-table");
const invitePagination = document.querySelector("#invite-pagination");
const inviteQuery = document.querySelector("#invite-query");
const inviteStatusFilter = document.querySelector("#invite-status-filter");
const inviteRepairFilter = document.querySelector("#invite-repair-filter");
const invitePageSize = document.querySelector("#invite-page-size");
const passwordInput = document.querySelector("#admin-password");
const passwordToggle = document.querySelector("#password-toggle");

const adminActionPaths = {
  disable: (inviteId) => `/api/admin/invites/${inviteId}/disable`,
};

const inviteListState = {
  page: 1,
  pageSize: 20,
  query: "",
  status: "all",
  repairStatus: "all",
  total: 0,
  totalPages: 1,
};

function text(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function setFeedback(node, message = "", tone = "") {
  if (!node) {
    return;
  }
  node.textContent = message;
  node.dataset.tone = tone;
  node.hidden = !message;
}

function setBusy(form, isBusy) {
  if (!form) {
    return;
  }
  form.classList.toggle("is-busy", isBusy);
  Array.from(form.elements).forEach((element) => {
    element.disabled = isBusy;
  });
}

function setPasswordVisible(isVisible) {
  if (!passwordInput || !passwordToggle) {
    return;
  }
  if (isVisible) {
    passwordInput.type = "text";
  } else {
    passwordInput.type = "password";
  }
  passwordToggle.classList.toggle("is-visible", isVisible);
  passwordToggle.setAttribute("aria-pressed", String(isVisible));
  passwordToggle.setAttribute("aria-label", isVisible ? "隐藏密码" : "显示密码");
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

async function adminFetch(path, options = {}) {
  const { headers = {}, ...fetchOptions } = options;
  const response = await fetch(path, {
    ...fetchOptions,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(fetchOptions.body ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
  });
  const payload = await readJson(response);

  if (!response.ok) {
    const error = new Error("admin request failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

function showLoggedOut(message = "") {
  if (loginPanel) {
    loginPanel.hidden = false;
  }
  if (workspace) {
    workspace.hidden = true;
  }
  if (logoutButton) {
    logoutButton.hidden = true;
  }
  createForm?.reset();
  renderTableMessage("登录后加载邀请码");
  setFeedback(loginFeedback, message, message ? "error" : "");
  setFeedback(createFeedback, "");
  renderPagination();
}

function showLoggedIn() {
  if (loginPanel) {
    loginPanel.hidden = true;
  }
  if (workspace) {
    workspace.hidden = false;
  }
  if (logoutButton) {
    logoutButton.hidden = false;
  }
  setFeedback(loginFeedback, "");
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return text(value);
  }
  return parsed.toLocaleString("zh-CN", { hour12: false });
}

function statusBadge(status) {
  const span = document.createElement("span");
  span.className = `admin-status ${status || "disabled"}`;
  if (status === "active") {
    span.textContent = "有效";
  } else if (status === "expired") {
    span.textContent = "过期";
  } else {
    span.textContent = "停用";
  }
  return span;
}

function repairBadge(invite) {
  const span = document.createElement("span");
  const completed = invite.repair_completed === true || Boolean(invite.repair_completed_at);
  span.className = `admin-status ${completed ? "completed" : "pending"}`;
  span.textContent = completed ? "已完成" : "未完成";
  return span;
}

function cell(content) {
  const td = document.createElement("td");
  if (content instanceof Node) {
    td.appendChild(content);
  } else {
    td.textContent = text(content);
  }
  return td;
}

function renderTableMessage(message) {
  const tr = document.createElement("tr");
  const td = document.createElement("td");
  td.colSpan = 9;
  td.textContent = message;
  tr.appendChild(td);
  inviteTable.replaceChildren(tr);
}

function actionButton(label, action, inviteId, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "table-action";
  button.dataset.action = action;
  button.dataset.inviteId = String(inviteId);
  button.disabled = disabled;
  button.textContent = label;
  return button;
}

function sourceText(invite) {
  const sourceIp = text(invite.source_ip);
  const sourceGeo = text(invite.source_geo);
  if (sourceIp === "-" && sourceGeo === "-") {
    return "-";
  }
  if (sourceGeo === "-") {
    return sourceIp;
  }
  if (sourceIp === "-") {
    return sourceGeo;
  }
  return `${sourceIp} / ${sourceGeo}`;
}

function renderInvites(invites) {
  const rows = invites.map((invite) => {
    const tr = document.createElement("tr");
    const actions = document.createElement("div");
    actions.className = "admin-actions";
    actions.append(
      actionButton("停用", "disable", invite.id, invite.status !== "active"),
    );

    tr.append(
      cell(invite.invite_code),
      cell(statusBadge(invite.status)),
      cell(invite.note),
      cell(sourceText(invite)),
      cell(repairBadge(invite)),
      cell(invite.proxy_port),
      cell(formatDate(invite.expires_at)),
      cell(formatDate(invite.last_used_at)),
      cell(actions),
    );
    return tr;
  });

  if (!rows.length) {
    renderTableMessage("暂无邀请码");
    return;
  }

  inviteTable.replaceChildren(...rows);
}

function normalizeInviteListPayload(payload) {
  if (Array.isArray(payload)) {
    return {
      items: payload,
      page: 1,
      page_size: payload.length || inviteListState.pageSize,
      total: payload.length,
      total_pages: 1,
    };
  }
  return {
    items: Array.isArray(payload?.items) ? payload.items : [],
    page: Number(payload?.page) || 1,
    page_size: Number(payload?.page_size) || inviteListState.pageSize,
    total: Number(payload?.total) || 0,
    total_pages: Number(payload?.total_pages) || 1,
  };
}

function syncFilterStateFromForm() {
  inviteListState.query = text(inviteQuery?.value, "").trim();
  inviteListState.status = text(inviteStatusFilter?.value, "all");
  inviteListState.repairStatus = text(inviteRepairFilter?.value, "all");
  inviteListState.pageSize = Number(invitePageSize?.value) || 20;
}

function inviteListSearchParams() {
  const params = new URLSearchParams();
  params.set("page", String(inviteListState.page));
  params.set("page_size", String(inviteListState.pageSize));
  if (inviteListState.query) {
    params.set("q", inviteListState.query);
  }
  if (inviteListState.status !== "all") {
    params.set("status", inviteListState.status);
  }
  if (inviteListState.repairStatus !== "all") {
    params.set("repair_status", inviteListState.repairStatus);
  }
  return params;
}

function renderPagination(payload = null) {
  if (!invitePagination) {
    return;
  }
  if (!payload) {
    invitePagination.replaceChildren();
    return;
  }
  const info = document.createElement("span");
  info.className = "admin-pagination-info";
  info.textContent = `共 ${payload.total} 条，第 ${payload.page} / ${payload.total_pages} 页`;

  const previous = document.createElement("button");
  previous.type = "button";
  previous.className = "table-action";
  previous.dataset.page = String(Math.max(payload.page - 1, 1));
  previous.disabled = payload.page <= 1;
  previous.textContent = "上一页";

  const next = document.createElement("button");
  next.type = "button";
  next.className = "table-action";
  next.dataset.page = String(Math.min(payload.page + 1, payload.total_pages));
  next.disabled = payload.page >= payload.total_pages;
  next.textContent = "下一页";

  invitePagination.replaceChildren(info, previous, next);
}

async function loadInvites({ page = inviteListState.page } = {}) {
  inviteListState.page = page;
  const payload = normalizeInviteListPayload(
    await adminFetch(`/api/admin/invites?${inviteListSearchParams().toString()}`),
  );
  inviteListState.page = payload.page;
  inviteListState.pageSize = payload.page_size;
  inviteListState.total = payload.total;
  inviteListState.totalPages = payload.total_pages;
  renderInvites(payload.items);
  renderPagination(payload);
}

function expiresAtFromInput(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toISOString();
}

async function handleLogin(event) {
  event.preventDefault();
  const data = new FormData(loginForm);

  try {
    setBusy(loginForm, true);
    setFeedback(loginFeedback, "正在登录...", "info");
    await adminFetch("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({
        username: text(data.get("username"), ""),
        password: text(data.get("password"), ""),
      }),
    });
    loginForm.reset();
    showLoggedIn();
    await loadInvites();
  } catch (error) {
    if (error?.status === 401) {
      setFeedback(loginFeedback, "管理员账号或密码不正确。", "error");
    } else {
      setFeedback(loginFeedback, "暂时无法登录后台。", "error");
    }
  } finally {
    setBusy(loginForm, false);
  }
}

async function handleCreate(event) {
  event.preventDefault();
  const data = new FormData(createForm);

  try {
    setBusy(createForm, true);
    setFeedback(createFeedback, "正在创建邀请码...", "info");
    const payload = {
      note: text(data.get("note"), "").trim(),
    };
    const expiresAt = expiresAtFromInput(text(data.get("expires_at"), ""));
    if (expiresAt) {
      payload.expires_at = expiresAt;
    }

    const invite = await adminFetch("/api/admin/invites", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    createForm.reset();
    setFeedback(createFeedback, "邀请码已创建，代理端口已分配。", "success");
    await loadInvites({ page: 1 });
  } catch (error) {
    if (error?.status === 401) {
      showLoggedOut("登录状态已失效，请重新登录。");
    } else {
      setFeedback(createFeedback, "创建失败，请检查备注或过期时间。", "error");
    }
  } finally {
    setBusy(createForm, false);
  }
}

async function handleInviteAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const inviteId = button.dataset.inviteId;
  const action = button.dataset.action;
  if (!inviteId || !action) {
    return;
  }

  const actionPath = adminActionPaths[action]?.(inviteId);
  if (!actionPath) {
    return;
  }

  button.disabled = true;
  setFeedback(createFeedback, "正在更新邀请码...", "info");

  try {
    const invite = await adminFetch(actionPath, {
      method: "POST",
    });
    setFeedback(createFeedback, "邀请码已停用。", "success");
    await loadInvites();
  } catch (error) {
    if (error?.status === 401) {
      showLoggedOut("登录状态已失效，请重新登录。");
    } else {
      setFeedback(createFeedback, "操作失败，请刷新后重试。", "error");
    }
  } finally {
    button.disabled = false;
  }
}

async function handleLogout() {
  try {
    await adminFetch("/api/admin/logout", { method: "POST" });
  } catch (_error) {
    // The local UI can still clear its session state when logout returns no JSON.
  }
  showLoggedOut();
}

async function bootstrap() {
  try {
    await loadInvites();
    showLoggedIn();
  } catch (error) {
    if (error?.status === 401) {
      showLoggedOut();
    } else {
      showLoggedOut("暂时无法连接后台接口。");
    }
  }
}

loginForm?.addEventListener("submit", handleLogin);
passwordToggle?.addEventListener("click", () => {
  setPasswordVisible(passwordInput?.type === "password");
});
createForm?.addEventListener("submit", handleCreate);
logoutButton?.addEventListener("click", () => {
  void handleLogout();
});
refreshButton?.addEventListener("click", () => {
  void loadInvites();
});
filterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  syncFilterStateFromForm();
  void loadInvites({ page: 1 });
});
inviteStatusFilter?.addEventListener("change", () => {
  syncFilterStateFromForm();
  void loadInvites({ page: 1 });
});
inviteRepairFilter?.addEventListener("change", () => {
  syncFilterStateFromForm();
  void loadInvites({ page: 1 });
});
invitePageSize?.addEventListener("change", () => {
  syncFilterStateFromForm();
  void loadInvites({ page: 1 });
});
invitePagination?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-page]");
  if (!button) {
    return;
  }
  void loadInvites({ page: Number(button.dataset.page) || 1 });
});
inviteTable?.addEventListener("click", (event) => {
  void handleInviteAction(event);
});

void bootstrap();
