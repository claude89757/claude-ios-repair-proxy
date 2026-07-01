# Admin Invite List P0/P1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the P0/P1 admin invite list improvements described in the design spec.

**Architecture:** Extend the existing FastAPI/SQLite invite listing endpoint with one normalized quick filter and summary counts. Keep the frontend in the existing static `admin.html`, `admin.js`, and shared `styles.css`, using progressive enhancement rather than a new framework.

**Tech Stack:** FastAPI, SQLite, vanilla JavaScript, HTML, CSS, pytest, Playwright CLI for visual verification.

---

### Task 1: Backend Summary And Quick Filters

**Files:**
- Modify: `repair_site/status_app/invites.py`
- Modify: `repair_site/status_app/main.py`
- Test: `tests/test_admin_api.py`

- [x] Write failing API tests for `quick_filter=used_pending`, `quick_filter=expiring_soon`, `quick_filter=completed_today`, invalid quick filters, and returned summary counts.
- [x] Run `pytest tests/test_admin_api.py -q` and confirm the new tests fail.
- [x] Add `quick_filter` normalization to `admin_list_invites`.
- [x] Extend `InviteStore.list_invites_page` to apply quick filters and return `summary`.
- [x] Run `pytest tests/test_admin_api.py -q` and confirm it passes.

### Task 2: Admin Static Markup

**Files:**
- Modify: `repair_site/web/admin.html`
- Test: `tests/test_static_site.py`

- [x] Write failing static tests for summary metrics, filter chips, mobile card container, list feedback, and disable confirmation modal.
- [x] Run the specific static test and confirm it fails.
- [x] Add the summary region, active filter chip container, mobile card container, list feedback, and confirmation modal to `admin.html`.
- [x] Run `pytest tests/test_static_site.py -q` and confirm it passes.

### Task 3: Admin Client Behavior

**Files:**
- Modify: `repair_site/web/admin.js`
- Test: `tests/test_static_site.py`

- [x] Add failing static tests for `quickFilter`, `renderInviteSummary`, `renderMobileInvites`, `renderActiveFilters`, `openDisableConfirm`, source labeling, relative time, and list feedback.
- [x] Run the specific static test and confirm it fails.
- [x] Implement invite summary rendering and quick filter buttons.
- [x] Implement active filter chips and clear filters.
- [x] Implement desktop row cleanup and mobile card rendering.
- [x] Implement disable confirmation and list-scoped feedback.
- [x] Run `pytest tests/test_static_site.py -q` and confirm it passes.

### Task 4: CSS And Responsive Layout

**Files:**
- Modify: `repair_site/web/styles.css`
- Test: `tests/test_static_site.py`

- [x] Add failing CSS assertions for admin summary grid, quick filters, active filter chips, list feedback, modal, source labels, relative time, and mobile card layout.
- [x] Implement CSS using existing admin visual language: restrained surfaces, 8px radius, clear status chips, no nested card clutter.
- [x] Run `pytest tests/test_static_site.py -q` and confirm it passes.

### Task 5: Review, Visual QA, Deploy

**Files:**
- No planned source additions beyond Tasks 1-4.

- [x] Run `pytest -q`.
- [x] Run `git diff --check`.
- [x] Start local dev server with temporary `/tmp` SQLite data.
- [x] Seed representative fake invite data.
- [x] Capture desktop and mobile screenshots with Playwright CLI.
- [x] Inspect screenshots for horizontal overflow, clipped text, missing actions, and modal behavior.
- [ ] Commit all source, spec, and plan changes.
- [ ] Push `main`.
- [ ] Watch `Deploy production`.
- [ ] Verify `/opt/claude-ios-repair/REVISION`, service health, public health endpoints, and live static assets.
