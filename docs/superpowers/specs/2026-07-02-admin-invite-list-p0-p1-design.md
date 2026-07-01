# Admin Invite List P0/P1 Design

## Goal

Improve the admin invite list so operators can quickly see which invites need follow-up, use it on mobile, and safely disable invites without confusing state/action labels.

## Scope

This spec implements the P0 and P1 recommendations from `output/admin-invite-list-audit-2026-07-02/notes.md`.

In scope:

- Mobile invite list card layout.
- Disable confirmation modal.
- Invite-list scoped action feedback.
- Clear status and action wording.
- Summary metrics for operational triage.
- Quick filters for common follow-up states.
- Active filter chips and reset.
- Source display cleanup.
- Relative time and expiring-soon indicators.

Out of scope:

- Row detail drawer.
- CSV export.
- Batch actions.
- Sorting.
- Full event timeline per invite.

## User Goal

An admin should be able to answer these questions without scanning every table column:

- Which invites need follow-up now?
- Which users connected but have not completed repair?
- Which active invites are about to expire?
- Which repairs completed today?
- Can I safely disable this invite?

## Data Model

The API keeps the existing `/api/admin/invites` endpoint and extends it with:

- Query parameter `quick_filter`, one of `all`, `needs_followup`, `used_pending`, `expiring_soon`, `completed_today`.
- Response field `summary`, with counts:
  - `total`
  - `active`
  - `needs_followup`
  - `used_pending`
  - `expiring_soon`
  - `completed_today`
- Response field `quick_filter`, echoing the normalized filter.

Definitions:

- `needs_followup`: active, not repair-completed.
- `used_pending`: active, `last_used_at` exists, not repair-completed.
- `expiring_soon`: active, not repair-completed, expires within 30 minutes.
- `completed_today`: `repair_completed_at` is today in UTC server time.

Existing status, repair status, pagination, and text query filters continue to work. Summary counts are computed against the same base filters except pagination.

## UI Design

### Summary

Above the filters, show four quiet metric buttons:

- 待跟进
- 已连接未修复
- 即将过期
- 今日完成

Each metric is clickable and applies the matching quick filter. The active one is visually selected.

### Filters

Keep the existing keyword/status/repair/page-size controls. Add:

- Active filter chips below the form.
- A clear button when any filter is active.
- Empty result copy that explains whether filters are active.

### List Rows

Desktop remains a table, but rows are made easier to scan:

- Invite code as primary text.
- Status labels use explicit wording: `有效`, `已停用`, `已过期`.
- Action button uses `停用邀请码`.
- Inactive rows show `无可用操作`.
- Public invite notes are normalized:
  - `public temporary invite: free ...` -> source label `免费`
  - `public temporary invite: alipay ...` -> source label `打赏`
  - Manual/admin-created invites -> source label `售后`
- IP/geo source is secondary text, not duplicated in the primary note.
- Time cells show absolute time plus relative text, such as `10 分钟前` or `剩余 23 分钟`.
- Expiring-soon active rows get a warning style.

### Mobile

Under 680px, hide the wide table and render invite cards:

- Header: invite code, status, repair status.
- Body: note, source, port, expires, last used.
- Footer: `停用邀请码` action or `无可用操作`.

Cards avoid horizontal scrolling and expose the same operational fields as the table.

### Disable Confirmation

Clicking `停用邀请码` opens a confirmation dialog:

- Title: `确认停用邀请码？`
- Copy: explains that the port is released and the user can no longer use the invite.
- Actions: `取消` and `确认停用`.

After success, list-level feedback says `邀请码已停用，端口已释放。`

## Accessibility

- Disable buttons include invite code in `aria-label`.
- The list feedback region uses `aria-live="polite"`.
- The confirmation dialog uses `role="dialog"`, `aria-modal="true"`, and focus returns to the triggering button when possible.
- Summary metric buttons use `aria-pressed`.
- Active filter chips are text buttons or inert chips with clear labels.

## Acceptance Criteria

- API supports `quick_filter` and returns summary counts.
- Static tests prove the admin page contains summary cards, active filter chips, mobile card container, and confirmation modal.
- Client JS sends `quick_filter`, renders summary cards, filter chips, mobile cards, relative time, source labels, and list-scoped feedback.
- Client JS no longer routes disable feedback through `createFeedback`.
- Desktop browser screenshot shows summary cards, cleaned source display, and clearer action labels.
- Mobile browser screenshot shows cards instead of an unusable horizontal table.
- Full test suite passes.
- Production deploy succeeds and live static assets include the new admin list UI.
