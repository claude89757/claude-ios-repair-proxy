const loginPanel = document.querySelector("#login-panel");
const workspace = document.querySelector("#admin-workspace");
const loginForm = document.querySelector("#login-form");
const createForm = document.querySelector("#create-form");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-button");
const loginFeedback = document.querySelector("#login-feedback");
const createFeedback = document.querySelector("#create-feedback");
const inviteTable = document.querySelector("#invite-table");
const passwordInput = document.querySelector("#admin-password");
const passwordToggle = document.querySelector("#password-toggle");

const visibleProxyPasswords = new Map();
const adminActionPaths = {
  disable: (inviteId) => `/api/admin/invites/${inviteId}/disable`,
  "reset-password": (inviteId) => `/api/admin/invites/${inviteId}/reset-password`,
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
  visibleProxyPasswords.clear();
  createForm?.reset();
  renderTableMessage("登录后加载邀请码");
  setFeedback(loginFeedback, message, message ? "error" : "");
  setFeedback(createFeedback, "");
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
  span.className = `admin-status ${status === "active" ? "active" : "disabled"}`;
  span.textContent = status === "active" ? "有效" : "停用";
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
  td.colSpan = 8;
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

function renderInvites(invites) {
  const rows = invites.map((invite) => {
    const tr = document.createElement("tr");
    const actions = document.createElement("div");
    actions.className = "admin-actions";
    actions.append(
      actionButton("重置密码", "reset-password", invite.id),
      actionButton("停用", "disable", invite.id, invite.status !== "active"),
    );

    tr.append(
      cell(invite.invite_code),
      cell(statusBadge(invite.status)),
      cell(invite.note),
      cell(invite.proxy_username),
      cell(visibleProxyPasswords.get(invite.id)),
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

async function loadInvites() {
  const invites = await adminFetch("/api/admin/invites");
  renderInvites(Array.isArray(invites) ? invites : []);
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
  setBusy(loginForm, true);
  setFeedback(loginFeedback, "正在登录...", "info");

  try {
    const data = new FormData(loginForm);
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
  setBusy(createForm, true);
  setFeedback(createFeedback, "正在创建邀请码...", "info");

  try {
    const data = new FormData(createForm);
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
    if (invite?.id && invite?.proxy_password) {
      visibleProxyPasswords.set(invite.id, invite.proxy_password);
    }
    createForm.reset();
    setFeedback(createFeedback, "邀请码已创建，代理密码已临时显示在列表中。", "success");
    await loadInvites();
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
    if (action === "reset-password" && invite?.proxy_password) {
      visibleProxyPasswords.set(invite.id, invite.proxy_password);
      setFeedback(createFeedback, "代理密码已重置，并临时显示在列表中。", "success");
    } else {
      setFeedback(createFeedback, "邀请码已停用。", "success");
    }
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
inviteTable?.addEventListener("click", (event) => {
  void handleInviteAction(event);
});

void bootstrap();
