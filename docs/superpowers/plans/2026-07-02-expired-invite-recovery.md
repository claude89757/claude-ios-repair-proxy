# Expired Invite Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users recover from an expired verified invite by using the header button to return to the existing invite choice page.

**Architecture:** Keep all behavior in the current static frontend. Add a small header submit-button mode helper in `repair_site/web/app.js`, expose the initial mode in `repair_site/web/index.html`, and style the verified/get-new states in `repair_site/web/styles.css`.

**Tech Stack:** Static HTML/CSS/JavaScript, pytest static assertions.

---

### Task 1: Add Regression Coverage

**Files:**
- Modify: `tests/test_static_site.py`

- [ ] **Step 1: Write the failing test**

Add `test_public_site_reuses_invite_submit_for_expired_recovery()` near the existing sticky header invite form test:

```python
def test_public_site_reuses_invite_submit_for_expired_recovery():
    html = (WEB / "index.html").read_text()
    js = (WEB / "app.js").read_text()
    css = (WEB / "styles.css").read_text()
    header = re.search(r"<header class=\"topbar\">.*?</header>", html, re.S)

    assert header is not None
    assert 'data-invite-action="verify"' in header.group(0)
    assert "const inviteSubmitButton" in js
    assert 'let inviteActionMode = "verify";' in js
    assert "function syncInviteActionButton" in js
    assert "function setInviteActionMode" in js
    assert "function returnToInviteChoicesFromExpired" in js
    assert '"entry.verified": "已验证"' in js
    assert '"entry.getNewInvite": "重新获取"' in js
    assert '"feedback.inviteExpired": "邀请码已过期，请重新选择一种方式获取新的邀请码。"' in js
    assert '"entry.verified": "Verified"' in js
    assert '"entry.getNewInvite": "Get new"' in js
    assert '"feedback.inviteExpired": "This invite expired. Choose a repair entry to get a new invite."' in js
    assert 'setInviteActionMode("get-new");' in js[js.index("function updateInviteCountdown"):js.index("function stopInviteCountdown")]
    assert 'setInviteActionMode("verified");' in js[js.index("async function activateInviteClaim"):js.index("inviteForm?.addEventListener")]
    submit_block = js[js.index('inviteForm?.addEventListener("submit"'):js.index("autoClaimButtons.forEach")]
    assert 'inviteActionMode === "get-new"' in submit_block
    assert "returnToInviteChoicesFromExpired();" in submit_block
    assert 'inviteActionMode === "verified"' in submit_block
    assert 'inviteInput?.addEventListener("input"' in js
    assert '.header-invite-form button[data-invite-action="verified"]' in css
    assert '.header-invite-form button[data-invite-action="get-new"]' in css
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --with-requirements requirements.txt pytest tests/test_static_site.py::test_public_site_reuses_invite_submit_for_expired_recovery -q
```

Expected: FAIL because the new header action mode does not exist yet.

### Task 2: Implement Header Action Modes

**Files:**
- Modify: `repair_site/web/index.html`
- Modify: `repair_site/web/app.js`
- Modify: `repair_site/web/styles.css`

- [ ] **Step 1: Add the initial button mode**

Change the invite submit button to:

```html
<button type="submit" data-invite-action="verify" data-i18n="entry.submit">验证</button>
```

- [ ] **Step 2: Add translations and button helpers**

Add `entry.verified`, `entry.getNewInvite`, and `feedback.inviteExpired` to both language dictionaries. Add helpers that update button label, `data-invite-action`, busy state, and disabled state.

- [ ] **Step 3: Wire the lifecycle**

Set mode to `verified` after successful invite claim. Set mode to `get-new` when the countdown expires. Clicking `get-new` calls `returnToInviteChoicesFromExpired()`, which clears local session state and returns to the existing invite choice page. Editing the input resets the mode to `verify`.

- [ ] **Step 4: Style the states**

Style `verified` as quiet success and `get-new` as a clear recovery action without changing the header layout.

### Task 3: Verify, Commit, Deploy, Release

**Files:**
- No new source files beyond Task 2.

- [ ] **Step 1: Run focused test**

```bash
uv run --with-requirements requirements.txt pytest tests/test_static_site.py::test_public_site_reuses_invite_submit_for_expired_recovery -q
```

- [ ] **Step 2: Run broader tests**

```bash
uv run --with-requirements requirements.txt pytest -q
```

- [ ] **Step 3: Run frontend sensitive-string scan**

```bash
rg -in "stack|traceback|Authorization: Bearer|sessionKey=sk-|routingHint=sk-" repair_site/web -S
```

Expected: no output.

- [ ] **Step 4: Commit and push**

Commit a focused change and push `main`.

- [ ] **Step 5: Deploy and release**

Watch the `Deploy production` workflow, verify `/opt/claude-ios-repair/REVISION`, then publish the next SemVer patch release after production is confirmed deployed.
