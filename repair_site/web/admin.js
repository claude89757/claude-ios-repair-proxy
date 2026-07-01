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
const inviteSummary = document.querySelector("#invite-summary");
const inviteSummaryButtons = Array.from(document.querySelectorAll("[data-quick-filter]"));
const inviteSummaryCounts = Array.from(document.querySelectorAll("[data-summary-count]"));
const activeFilterChips = document.querySelector("#active-filter-chips");
const inviteListFeedback = document.querySelector("#invite-list-feedback");
const inviteCardList = document.querySelector("#invite-card-list");
const inviteQuery = document.querySelector("#invite-query");
const inviteStatusFilter = document.querySelector("#invite-status-filter");
const inviteRepairFilter = document.querySelector("#invite-repair-filter");
const invitePageSize = document.querySelector("#invite-page-size");
const passwordInput = document.querySelector("#admin-password");
const passwordToggle = document.querySelector("#password-toggle");
const disableConfirmModal = document.querySelector("#disable-confirm-modal");
const disableConfirmCode = document.querySelector("#disable-confirm-code");
const disableConfirmButton = document.querySelector("[data-disable-confirm]");
const disableCancelButtons = Array.from(document.querySelectorAll("[data-disable-cancel]"));

const adminActionPaths = {
  disable: (inviteId) => `/api/admin/invites/${inviteId}/disable`,
};

const inviteListState = {
  page: 1,
  pageSize: 20,
  query: "",
  status: "all",
  repairStatus: "all",
  quickFilter: "all",
  total: 0,
  totalPages: 1,
};

let pendingDisableAction = null;

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

function setListFeedback(message = "", tone = "") {
  setFeedback(inviteListFeedback, message, tone);
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

function formatDuration(milliseconds) {
  const totalMinutes = Math.max(0, Math.round(Math.abs(milliseconds) / 60000));
  if (totalMinutes < 1) {
    return "刚刚";
  }
  if (totalMinutes < 60) {
    return `${totalMinutes} 分钟`;
  }
  const hours = Math.round(totalMinutes / 60);
  if (hours < 24) {
    return `${hours} 小时`;
  }
  return `${Math.round(hours / 24)} 天`;
}

function formatRelativeTime(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  const diff = parsed.getTime() - Date.now();
  if (Math.abs(diff) < 60000) {
    return "刚刚";
  }
  return diff > 0 ? `剩余 ${formatDuration(diff)}` : `${formatDuration(diff)}前`;
}

function timeLines(value, { empty = "-" } = {}) {
  const wrap = document.createElement("span");
  wrap.className = "time-lines";
  const absolute = document.createElement("span");
  absolute.textContent = formatDate(value);
  wrap.appendChild(absolute);

  const relativeText = formatRelativeTime(value);
  if (relativeText) {
    const relative = document.createElement("small");
    relative.className = "time-relative";
    relative.textContent = relativeText;
    wrap.appendChild(relative);
  } else if (!value) {
    absolute.textContent = empty;
  }
  return wrap;
}

function isRepairCompleted(invite) {
  return invite.repair_completed === true || Boolean(invite.repair_completed_at);
}

function isExpiringSoon(invite) {
  if (invite.status !== "active" || isRepairCompleted(invite) || !invite.expires_at) {
    return false;
  }
  const expiresAt = new Date(invite.expires_at).getTime();
  if (Number.isNaN(expiresAt)) {
    return false;
  }
  const remaining = expiresAt - Date.now();
  return remaining > 0 && remaining <= 30 * 60 * 1000;
}

function statusBadge(status) {
  const span = document.createElement("span");
  span.className = `admin-status ${status || "disabled"}`;
  if (status === "active") {
    span.textContent = "有效";
  } else if (status === "expired") {
    span.textContent = "已过期";
  } else {
    span.textContent = "已停用";
  }
  return span;
}

function repairBadge(invite) {
  const span = document.createElement("span");
  const completed = isRepairCompleted(invite);
  span.className = `admin-status ${completed ? "completed" : "pending"}`;
  span.textContent = completed ? "已完成" : "未完成";
  return span;
}

function sourceLabel(invite) {
  const note = text(invite.note, "").toLowerCase();
  if (note.startsWith("public temporary invite: free")) {
    return "免费";
  }
  if (note.startsWith("public temporary invite: alipay")) {
    return "打赏";
  }
  return "售后";
}

function sourceDetail(invite) {
  const sourceIp = text(invite.source_ip);
  const sourceGeo = text(invite.source_geo);
  if (sourceIp === "-" && sourceGeo === "-") {
    return "管理员创建";
  }
  if (sourceGeo === "-") {
    return sourceIp;
  }
  if (sourceIp === "-") {
    return sourceGeo;
  }
  return `${sourceIp} / ${sourceGeo}`;
}

function displayNote(invite) {
  const note = text(invite.note);
  const normalizedNote = note.toLowerCase();
  if (normalizedNote.startsWith("public temporary invite: free")) {
    return "免费自助邀请码";
  }
  if (normalizedNote.startsWith("public temporary invite: alipay")) {
    return "打赏临时邀请码";
  }
  return note;
}

function linesCell(primary, secondary = "") {
  const wrap = document.createElement("span");
  wrap.className = "cell-lines";
  const strong = document.createElement("strong");
  strong.textContent = text(primary);
  wrap.appendChild(strong);
  if (secondary) {
    const small = document.createElement("small");
    small.textContent = secondary;
    wrap.appendChild(small);
  }
  return wrap;
}

function sourceNode(invite) {
  const wrap = document.createElement("span");
  wrap.className = "source-lines";
  const label = document.createElement("span");
  label.className = `source-label ${sourceLabel(invite) === "售后" ? "manual" : "public"}`;
  label.textContent = sourceLabel(invite);
  const detail = document.createElement("small");
  detail.textContent = sourceDetail(invite);
  wrap.append(label, detail);
  return wrap;
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
  if (inviteCardList) {
    const empty = document.createElement("p");
    empty.className = "invite-card-empty";
    empty.textContent = message;
    inviteCardList.replaceChildren(empty);
  }
}

function actionButton(label, action, invite, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "table-action";
  button.dataset.action = action;
  button.dataset.inviteId = String(invite.id);
  button.dataset.inviteCode = String(invite.invite_code);
  button.disabled = disabled;
  button.setAttribute("aria-label", `${label} ${invite.invite_code}`);
  button.textContent = label;
  return button;
}

function noActionNode() {
  const span = document.createElement("span");
  span.className = "admin-no-action";
  span.textContent = "无可用操作";
  return span;
}

function inviteActionNode(invite) {
  if (invite.status !== "active") {
    return noActionNode();
  }
  return actionButton("停用邀请码", "disable", invite);
}

function renderInviteSummary(summary = {}) {
  inviteSummaryCounts.forEach((node) => {
    const key = node.dataset.summaryCount;
    node.textContent = String(Number(summary[key]) || 0);
  });
  inviteSummaryButtons.forEach((button) => {
    const isActive = inviteListState.quickFilter === button.dataset.quickFilter;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
  if (inviteSummary) {
    inviteSummary.hidden = false;
  }
}

function hasActiveFilters() {
  return Boolean(
    inviteListState.query ||
      inviteListState.status !== "all" ||
      inviteListState.repairStatus !== "all" ||
      inviteListState.quickFilter !== "all",
  );
}

function filterLabel(type, value) {
  const labels = {
    status: {
      active: "有效",
      disabled: "已停用",
      expired: "已过期",
    },
    repairStatus: {
      completed: "已完成修复",
      pending: "未完成",
    },
    quickFilter: {
      needs_followup: "待跟进",
      used_pending: "已连接未修复",
      expiring_soon: "即将过期",
      completed_today: "今日完成",
    },
  };
  return labels[type]?.[value] || value;
}

function renderActiveFilters() {
  if (!activeFilterChips) {
    return;
  }
  const chips = [];
  if (inviteListState.query) {
    chips.push(["query", `关键词：${inviteListState.query}`]);
  }
  if (inviteListState.status !== "all") {
    chips.push(["status", `状态：${filterLabel("status", inviteListState.status)}`]);
  }
  if (inviteListState.repairStatus !== "all") {
    chips.push([
      "repairStatus",
      `修复：${filterLabel("repairStatus", inviteListState.repairStatus)}`,
    ]);
  }
  if (inviteListState.quickFilter !== "all") {
    chips.push([
      "quickFilter",
      `快捷：${filterLabel("quickFilter", inviteListState.quickFilter)}`,
    ]);
  }

  if (!chips.length) {
    activeFilterChips.replaceChildren();
    activeFilterChips.hidden = true;
    return;
  }

  const nodes = chips.map(([type, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "filter-chip";
    button.dataset.clearFilter = type;
    button.textContent = `${label} ×`;
    return button;
  });
  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "filter-chip clear";
  clear.dataset.clearFilter = "all";
  clear.textContent = "清空筛选";
  activeFilterChips.replaceChildren(...nodes, clear);
  activeFilterChips.hidden = false;
}

function clearFilter(type) {
  if (type === "all" || type === "query") {
    inviteListState.query = "";
    if (inviteQuery) {
      inviteQuery.value = "";
    }
  }
  if (type === "all" || type === "status") {
    inviteListState.status = "all";
    if (inviteStatusFilter) {
      inviteStatusFilter.value = "all";
    }
  }
  if (type === "all" || type === "repairStatus") {
    inviteListState.repairStatus = "all";
    if (inviteRepairFilter) {
      inviteRepairFilter.value = "all";
    }
  }
  if (type === "all" || type === "quickFilter") {
    inviteListState.quickFilter = "all";
  }
}

function metaItem(label, value) {
  const item = document.createElement("span");
  item.className = "invite-card-meta-item";
  const name = document.createElement("small");
  name.textContent = label;
  const content = document.createElement("strong");
  if (value instanceof Node) {
    content.appendChild(value);
  } else {
    content.textContent = text(value);
  }
  item.append(name, content);
  return item;
}

function inviteCard(invite) {
  const article = document.createElement("article");
  article.className = "invite-card";
  article.classList.toggle("is-expiring-soon", isExpiringSoon(invite));

  const head = document.createElement("div");
  head.className = "invite-card-head";
  const title = document.createElement("strong");
  title.textContent = invite.invite_code;
  const badges = document.createElement("div");
  badges.className = "invite-card-badges";
  badges.append(statusBadge(invite.status), repairBadge(invite));
  head.append(title, badges);

  const note = document.createElement("p");
  note.className = "invite-card-note";
  note.textContent = displayNote(invite);

  const meta = document.createElement("div");
  meta.className = "invite-card-meta";
  meta.append(
    metaItem("来源", sourceNode(invite)),
    metaItem("端口", invite.proxy_port),
    metaItem("过期", timeLines(invite.expires_at)),
    metaItem("最后使用", timeLines(invite.last_used_at)),
  );

  const actions = document.createElement("div");
  actions.className = "invite-card-actions";
  actions.appendChild(inviteActionNode(invite));

  article.append(head, note, meta, actions);
  return article;
}

function renderMobileInvites(invites) {
  if (!inviteCardList) {
    return;
  }
  if (!invites.length) {
    const empty = document.createElement("p");
    empty.className = "invite-card-empty";
    empty.textContent = hasActiveFilters()
      ? "没有匹配的邀请码，试试清空筛选。"
      : "暂无邀请码";
    inviteCardList.replaceChildren(empty);
    return;
  }
  inviteCardList.replaceChildren(...invites.map(inviteCard));
}

function renderInvites(invites) {
  const rows = invites.map((invite) => {
    const tr = document.createElement("tr");
    tr.classList.toggle("is-expiring-soon", isExpiringSoon(invite));
    const actions = document.createElement("div");
    actions.className = "admin-actions";
    actions.append(inviteActionNode(invite));

    tr.append(
      cell(linesCell(invite.invite_code, sourceLabel(invite))),
      cell(statusBadge(invite.status)),
      cell(linesCell(displayNote(invite))),
      cell(sourceNode(invite)),
      cell(repairBadge(invite)),
      cell(invite.proxy_port),
      cell(timeLines(invite.expires_at)),
      cell(timeLines(invite.last_used_at)),
      cell(actions),
    );
    return tr;
  });

  if (!rows.length) {
    renderTableMessage(hasActiveFilters() ? "没有匹配的邀请码，试试清空筛选。" : "暂无邀请码");
    return;
  }

  inviteTable.replaceChildren(...rows);
  renderMobileInvites(invites);
}

function normalizeInviteListPayload(payload) {
  if (Array.isArray(payload)) {
    return {
      items: payload,
      page: 1,
      page_size: payload.length || inviteListState.pageSize,
      total: payload.length,
      total_pages: 1,
      quick_filter: inviteListState.quickFilter,
      summary: {
        total: payload.length,
        active: 0,
        needs_followup: 0,
        used_pending: 0,
        expiring_soon: 0,
        completed_today: 0,
      },
    };
  }
  return {
    items: Array.isArray(payload?.items) ? payload.items : [],
    page: Number(payload?.page) || 1,
    page_size: Number(payload?.page_size) || inviteListState.pageSize,
    total: Number(payload?.total) || 0,
    total_pages: Number(payload?.total_pages) || 1,
    quick_filter: text(payload?.quick_filter, inviteListState.quickFilter),
    summary: {
      total: Number(payload?.summary?.total) || 0,
      active: Number(payload?.summary?.active) || 0,
      needs_followup: Number(payload?.summary?.needs_followup) || 0,
      used_pending: Number(payload?.summary?.used_pending) || 0,
      expiring_soon: Number(payload?.summary?.expiring_soon) || 0,
      completed_today: Number(payload?.summary?.completed_today) || 0,
    },
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
  if (inviteListState.quickFilter !== "all") {
    params.set("quick_filter", inviteListState.quickFilter);
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
  inviteListState.quickFilter = payload.quick_filter || inviteListState.quickFilter;
  renderInviteSummary(payload.summary);
  renderActiveFilters();
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

    await adminFetch("/api/admin/invites", {
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

function openDisableConfirm(button) {
  if (!disableConfirmModal || !button) {
    return;
  }
  pendingDisableAction = {
    inviteId: button.dataset.inviteId,
    inviteCode: button.dataset.inviteCode,
    trigger: button,
  };
  if (disableConfirmCode) {
    disableConfirmCode.textContent = pendingDisableAction.inviteCode || "";
  }
  disableConfirmModal.hidden = false;
  document.body.classList.add("has-admin-modal");
  disableConfirmButton?.focus();
}

function closeDisableConfirm({ restoreFocus = true } = {}) {
  if (!disableConfirmModal) {
    return;
  }
  const trigger = pendingDisableAction?.trigger;
  disableConfirmModal.hidden = true;
  document.body.classList.remove("has-admin-modal");
  pendingDisableAction = null;
  if (restoreFocus && trigger instanceof HTMLElement) {
    trigger.focus();
  }
}

async function confirmDisableInvite() {
  if (!pendingDisableAction?.inviteId) {
    closeDisableConfirm({ restoreFocus: false });
    return;
  }
  const { inviteId } = pendingDisableAction;
  const actionPath = adminActionPaths.disable(inviteId);

  if (disableConfirmButton) {
    disableConfirmButton.disabled = true;
  }
  setListFeedback("正在停用邀请码...", "info");

  try {
    await adminFetch(actionPath, {
      method: "POST",
    });
    closeDisableConfirm({ restoreFocus: false });
    setListFeedback("邀请码已停用，端口已释放。", "success");
    await loadInvites();
  } catch (error) {
    if (error?.status === 401) {
      closeDisableConfirm({ restoreFocus: false });
      showLoggedOut("登录状态已失效，请重新登录。");
    } else {
      setListFeedback("停用失败，请刷新后重试。", "error");
    }
  } finally {
    if (disableConfirmButton) {
      disableConfirmButton.disabled = false;
    }
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

  if (action === "disable") {
    openDisableConfirm(button);
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
inviteSummary?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-quick-filter]");
  if (!button) {
    return;
  }
  const nextFilter = button.dataset.quickFilter || "all";
  inviteListState.quickFilter =
    inviteListState.quickFilter === nextFilter ? "all" : nextFilter;
  void loadInvites({ page: 1 });
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
activeFilterChips?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-clear-filter]");
  if (!button) {
    return;
  }
  clearFilter(button.dataset.clearFilter || "all");
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
  handleInviteAction(event);
});
inviteCardList?.addEventListener("click", (event) => {
  handleInviteAction(event);
});
disableConfirmButton?.addEventListener("click", () => {
  void confirmDisableInvite();
});
disableCancelButtons.forEach((button) => {
  button.addEventListener("click", () => {
    closeDisableConfirm();
  });
});
disableConfirmModal?.addEventListener("click", (event) => {
  if (event.target === disableConfirmModal) {
    closeDisableConfirm();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !disableConfirmModal?.hidden) {
    closeDisableConfirm();
  }
});

void bootstrap();
