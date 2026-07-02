# Expired Invite Recovery Design

## Goal

When a verified invite expires while the user is still on the repair page, the header action should help them recover instead of leaving them in a dead end.

## User Experience

- Default state: header button says "验证" / "Verify" and validates the typed invite.
- Active verified state: after a successful invite claim, the same button says "已验证" / "Verified" and is visually quiet.
- Expired state: when the invite countdown reaches zero, the same button says "重新获取" / "Get new".
- Clicking "重新获取" clears the expired local state and returns to the existing invite choice page.
- The click does not auto-create another invite. The user reselects "售后协助" or "自助获取".
- If the user edits the invite input after verified or expired state, the button returns to validate mode.

## Copy

- zh: "邀请码已过期，请重新选择一种方式获取新的邀请码。"
- en: "This invite expired. Choose a repair entry to get a new invite."

## Constraints

- Reuse the current invite gate screen and public invite creation buttons.
- Do not add a new backend endpoint.
- Keep the header layout stable on mobile.
