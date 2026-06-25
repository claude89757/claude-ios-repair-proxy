# Invite Admin and Internal Session Design

Date: 2026-06-25

## Goal

Upgrade the Claude iOS repair site from a shared `default` status session to an invite-based multi-user flow.

Users should not see or enter a repair session ID. A user enters an invite code, then the site shows that user's repair proxy configuration and live status automatically.

Administrators should have a password-protected page to create and manage invite codes.

## Core Decision

Do not allocate one proxy port per user.

Use one repair proxy port:

```text
sg2.claude89757.cc:9443
```

Create separate proxy credentials per invite:

```text
invite code -> proxy username -> internal session_id -> status events
```

This keeps iPhone setup simple, avoids port sprawl, avoids firewall changes for every user, and still gives clean per-user status isolation.

## User Flow

1. User opens the public site.
2. User enters an invite code.
3. Backend validates the invite.
4. Site shows:
   - proxy host: `sg2.claude89757.cc`
   - proxy port: `9443`
   - proxy username generated for that invite
   - proxy password generated for that invite
   - CA certificate download link
   - live status for that invite
5. User configures iPhone Wi-Fi HTTP proxy.
6. User installs and trusts the CA certificate.
7. User opens Claude iOS once.
8. Live status updates automatically.
9. User disables proxy and certificate trust after seeing the login entry.

The user-facing page should use the label `邀请码`, not `repair session ID`.

## Admin Flow

Admin opens:

```text
/admin
```

Admin logs in with administrator credentials.

After login, admin can:

- Create invite codes.
- View invite list.
- View generated proxy username and password for each invite.
- View status per invite.
- Disable an invite.
- Optionally delete or expire old invites.

Admin credentials must not be hard-coded into public frontend files. They should be provided through server-side environment variables or a private config file.

## Data Model

Use SQLite for persistence.

Table: `invites`

```text
id
invite_code
session_id
proxy_username
proxy_password_version
status
created_at
expires_at
last_used_at
disabled_at
note
```

Recommended simplification for first version:

- Do not store plaintext proxy passwords in SQLite.
- Derive the proxy password from a server-side secret plus invite data.
- Store only metadata needed to rotate or invalidate credentials.
- Show the derived password to admin and to the invite holder after invite validation.

This gives the user a repeatable password display without placing all proxy passwords directly in the database. Rotating the server-side derivation secret invalidates generated passwords, so use a version field to support future rotation.

Table: `events`

The current implementation stores events in memory. For the invite upgrade, keep status events in memory initially, keyed by `session_id`.

Persisting event history is optional and not required for first version. If event persistence is added later, only sanitized events may be stored.

## Session Model

`session_id` still exists, but it is internal.

Users never type it.

The mapping is:

```text
invite_code -> session_id
proxy_username -> session_id
```

The site uses a short-lived browser token after invite validation:

```text
POST /api/invites/claim
invite_code -> returns proxy config + status_token
```

The browser then calls:

```text
GET /api/invites/me/status
GET /api/invites/me/events
```

The backend maps the `status_token` to `session_id`.

This prevents users from guessing another invite's status endpoint by changing a visible ID.

## Proxy Authentication and Event Attribution

The repair proxy continues to listen on `9443`.

Each invite gets unique proxy credentials:

```text
username: repair_<random>
password: random high-entropy value
```

The existing single `--proxyauth` mechanism should be removed for the repair proxy because it only represents one shared credential. The MITM addon should validate proxy Basic authentication itself:

1. Read `Proxy-Authorization` on CONNECT/request.
2. Decode username and password.
3. Ask the local status backend whether the credential is valid.
4. Return `407 Proxy Authentication Required` if missing, invalid, disabled, or expired.
5. Store the resolved `session_id` on the flow or client metadata.

After authentication, the MITM addon resolves:

```text
proxy_username -> session_id
```

Then every sanitized event is emitted with that `session_id`.

If the proxy cannot identify the proxy username for a request, the addon should emit to a reserved internal session such as `unknown` or drop the event. It should not write unidentified traffic into a public shared `default` session.

## API Design

Public invite APIs:

```text
POST /api/invites/claim
GET /api/invites/me/status
GET /api/invites/me/events
```

Admin APIs:

```text
POST /api/admin/login
POST /api/admin/logout
GET /api/admin/invites
POST /api/admin/invites
POST /api/admin/invites/{invite_id}/disable
POST /api/admin/invites/{invite_id}/reset-password
```

Internal proxy API:

```text
POST /api/internal/proxy-auth/verify
POST /api/internal/events
```

`POST /api/internal/proxy-auth/verify` receives proxy username and password over localhost and returns the internal `session_id` only if the invite is active and not expired.

The internal endpoints should only be reachable from localhost and should also be protected by an internal secret header.

## Frontend Changes

Public page:

- Replace `Repair session ID` input with `邀请码`.
- After successful invite validation, show proxy configuration.
- Automatically connect the live status dashboard.
- Hide proxy configuration until invite code is accepted.
- Keep existing safety copy about disabling proxy and certificate trust after repair.

Admin page:

- Login form.
- Invite creation form.
- Invite table with:
  - invite code
  - proxy username
  - proxy password
  - status
  - created time
  - expires time
  - last activity
  - action buttons
- Status preview for selected invite.

## Security and Privacy

Public site must not show global proxy credentials.

Invite codes are bearer secrets. Anyone with an invite code can view that invite's proxy configuration and status.

Mitigations:

- Generate high-entropy invite codes.
- Support expiration.
- Support disabling invites.
- Store only sanitized events.
- Do not store raw Cookie, Authorization, request bodies, response bodies, raw `sessionKey`, raw `routingHint`, or raw device IDs.
- Internal status should continue to mask IPs and hash device IDs.

Admin login should use:

- Server-side password verification.
- HttpOnly session cookie.
- `Secure` cookie on production HTTPS.
- SameSite=Lax.

## Deployment Impact

No new public proxy ports are needed.

Current port layout remains:

```text
443   public website
8080  existing direct HTTP proxy
8443  existing WARP HTTPS proxy
9443  Claude iOS repair proxy
9000  local status backend only
```

The existing `default` session should be removed from the UI and no longer used for normal events.

During migration:

1. Deploy invite database and admin credentials.
2. Create first invite.
3. Validate invite user page.
4. Update MITM addon to attribute events by proxy username.
5. Restart status and MITM services.
6. Confirm old `default` status no longer accumulates normal events.

## Testing

Unit tests:

- Invite creation creates unique invite code, proxy username, proxy password, and internal session ID.
- Invite claim rejects invalid, disabled, and expired invites.
- Invite claim returns only that invite's proxy config.
- Admin endpoints require login.
- Status APIs map browser token to internal session ID.
- MITM addon maps proxy username to session ID.
- Unknown proxy users do not write into `default`.
- Sanitization still prevents raw cookie/token leakage.

Integration tests:

- Claim invite, open SSE stream, post internal event for its session, verify dashboard update.
- Create two invites, emit events for both, verify isolation.
- Disable invite, verify user can no longer claim it.

Deployment smoke tests:

- `/admin` loads.
- Admin can create invite.
- `/api/invites/claim` returns proxy config for valid invite.
- `9443` with generated proxy credentials triggers a status event for that invite.
- Public site source does not contain proxy passwords or admin credentials.
