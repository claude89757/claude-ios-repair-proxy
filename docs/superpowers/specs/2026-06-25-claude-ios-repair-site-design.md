# Claude iOS Repair Site Design

Date: 2026-06-25

## Goal

Build a modern HTTPS website at `https://sg2.claude89757.cc` that helps users fix the Claude iOS app loop where the app opens to `Something went wrong` and never returns to the login screen.

The site explains the issue, gives iPhone proxy and certificate setup steps, and provides a downloadable MITM root certificate. It does not publish proxy usernames, passwords, or private operational details. Users must contact the administrator to get proxy credentials.

The service must not attempt to unban or recover a banned Claude account. Its only intended behavior is to clear a stuck local iOS session so the app can show the login screen again.

The site should also include a real-time repair status page. After an iPhone connects to the repair proxy, the page can show whether the proxy connection is active, whether the certificate is working, and whether Claude-related repair requests have been observed and rewritten. This dashboard must use sanitized metadata only.

## Confirmed Constraints

- `sg2.claude89757.cc:443` becomes the public website.
- The current HTTPS proxy on `443` will be moved, removed, or replaced by the website listener.
- Existing WARP proxy behavior can remain available on a non-website port, currently `8443`.
- Public pages must not display proxy account credentials.
- The site may expose the MITM root certificate download, with clear trust and removal warnings.
- The repair proxy should only apply the Claude session-cleaning behavior to the minimum required Claude endpoint.
- The service should not log user cookies, session tokens, request bodies, or other sensitive traffic.
- The real-time status page must not display raw cookies, full headers, full bodies, authorization values, or full unique device identifiers.

## Recommended Architecture

Use three separate concerns:

1. Public website on `443`
   - Nginx serves a static site over HTTPS using the existing Let's Encrypt certificate for the domain.
   - The homepage is `https://sg2.claude89757.cc`.
   - The site includes documentation, warnings, and certificate download.

2. Existing WARP proxy on `8443`
   - Keep as the general Claude/Anthropic proxy path.
   - Do not publish credentials on the website.

3. New repair MITM proxy on a separate port, for example `9443`
   - Runs mitmproxy or an equivalent explicit HTTP(S) proxy.
   - Uses its own generated root CA, exposed by the website for download.
   - Requires administrator-provided credentials or equivalent access control.
   - Applies a narrow response rewrite for `https://claude.ai/api/account`.
   - Emits sanitized repair events to the website backend for the live status page.

This avoids trying to multiplex website traffic and proxy traffic on the same `443` listener. It also keeps the repair proxy operationally separate from the normal WARP proxy.

4. Lightweight status backend
   - Receives sanitized events from the repair proxy over localhost or a Unix socket.
   - Stores short-lived in-memory session state keyed by a repair code or temporary proxy credential identity.
   - Serves a status API and Server-Sent Events stream to the website.
   - Does not persist raw traffic.

## Repair Proxy Behavior

When a user opts in by installing the certificate and configuring the repair proxy, the service should target only:

```text
https://claude.ai/api/account
```

For matching responses, apply the same logic validated through Charles:

1. Change the response status to:

```text
401 Unauthorized
```

2. Replace the response body with:

```json
{"type":"error","error":{"type":"authentication_error","message":"session_expired","details":{"error_code":"session_expired"}}}
```

3. Add response headers to clear stale Claude cookies:

```text
Set-Cookie: sessionKey=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Secure; HttpOnly; SameSite=None
Set-Cookie: sessionKey=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Domain=claude.ai; Secure; HttpOnly; SameSite=None
Set-Cookie: routingHint=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Secure; SameSite=None
Set-Cookie: routingHint=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; Domain=claude.ai; Secure; SameSite=None
```

All other traffic should pass through unchanged. If this selective behavior is difficult to enforce safely, the proxy should fail closed rather than broadly rewriting Claude or non-Claude traffic.

## Live Repair Status Dashboard

The website should provide a status page for an active repair session. It helps the user and administrator confirm that each setup step worked without exposing sensitive traffic.

### Session Pairing

Each temporary proxy credential should map to a short repair session ID. The public site can expose a page such as:

```text
/status/<repair-session-id>
```

The repair session ID should be separate from the proxy password. It should be safe to share with the user for viewing status, but not sufficient to use the proxy.

### Displayed Device Information

Show only basic, non-secret device metadata:

- Connection status: `not connected`, `connected`, `recently active`, or `expired`.
- First seen and last seen timestamps.
- Client IP masked or truncated.
- iOS app User-Agent summary, for example `Claude iOS / CFNetwork / Darwin`.
- Claude app version and build if present in request headers.
- iOS version if present in `anthropic-client-os-version`.
- A hashed or truncated device identifier if `anthropic-device-id` appears. Do not display the raw identifier.

### Displayed Setup State

Show setup progress as a checklist:

1. Proxy connected.
2. HTTPS interception working.
3. Certificate trusted by iOS.
4. Claude `/api/account` request observed.
5. Session cleanup rewrite applied.
6. Cookie deletion headers sent.
7. Login screen likely available.

Certificate state is inferred:

- If the proxy only sees CONNECT/TLS failures, show `certificate not trusted or SSL interception failed`.
- If the proxy can read decrypted `https://claude.ai/api/account`, show `certificate trusted`.

### Displayed Claude Request Metadata

Show a small live table of Claude-related events. Each row should include:

- Timestamp.
- Method.
- Host.
- Path, such as `/api/account` or `/api/legal`.
- Response status.
- Whether rewrite was applied.
- Detected error code after sanitization, for example `session_expired`.
- Whether stale cookies were present, displayed only as booleans:
  - `sessionKey present: yes/no`
  - `routingHint present: yes/no`
- Whether cookie deletion headers were sent.

Do not show:

- Raw Cookie header.
- Raw `sessionKey` or `routingHint`.
- Authorization headers.
- Request body.
- Response body beyond a sanitized error code.
- Full query strings unless they are known to be non-sensitive.

### Real-Time Transport

Use Server-Sent Events for the live dashboard:

```text
GET /api/status/<repair-session-id>/events
```

Use a normal JSON endpoint for initial state:

```text
GET /api/status/<repair-session-id>
```

SSE is sufficient because the browser only needs to receive status updates. It is simpler than WebSockets and works well behind Nginx.

## Website Content

The site should be a practical guide, not a marketing landing page. First screen content:

- Title: `Claude iOS 登录卡死修复指南`
- Short problem statement: Claude iOS app stuck at `Something went wrong`.
- Three-step overview:
  1. Configure the temporary repair proxy on iPhone.
  2. Install and trust the certificate.
  3. Open Claude once to clear the old session, then remove the proxy.
- Prominent note: proxy credentials are provided by the administrator.

Main sections:

- Problem: symptoms and when this guide applies.
- How it works: stale `sessionKey` / `routingHint` cookies can keep iOS in a broken session loop.
- iPhone setup:
  - Open Wi-Fi settings.
  - Configure HTTP proxy manually.
  - Enter server, port, username, and password provided by the administrator.
  - Download and install the root certificate.
  - Trust the certificate under iOS certificate trust settings.
- Repair flow:
  - Force quit Claude.
  - Open Claude once through the repair proxy.
  - Wait for the login screen.
  - Disable proxy and remove trust when done.
- Certificate download:
  - Download button for the MITM root CA.
  - SHA-256 fingerprint display if available.
  - Warning that trusting this certificate allows HTTPS inspection while enabled.
- Live status:
  - Input or link for a repair session ID.
  - Real-time setup checklist.
  - Device summary with masked values.
  - Claude request event table with sanitized metadata.
- Safety:
  - Do not keep the proxy enabled after repair.
  - Do not share cookies or session values.
  - This does not unban accounts.
  - Remove the certificate trust after use.
- Contact:
  - A short contact block for obtaining temporary proxy credentials.

## Visual Direction

The site should feel like a polished technical help tool:

- Clean single-page layout with anchored sections.
- Practical first screen, not a large marketing hero.
- Modern but restrained palette: off-white/charcoal base, blue and green accents for action and verified steps.
- Step cards with icons, status tags, and concise copy.
- iPhone-oriented setup checklist with clear ordering.
- No nested decorative cards or heavy gradient backgrounds.
- Responsive layout that remains readable on iPhone Safari.

## Security and Privacy Requirements

- Do not publish proxy username or password in HTML, JavaScript, static files, or docs served by the site.
- Do not store or display user session cookies.
- Disable or minimize proxy access logs. If operational logs are necessary, avoid request headers, query strings, and bodies.
- Status events must be short-lived and should expire automatically after the repair session, for example after 30 to 60 minutes of inactivity.
- The status backend must sanitize data before it reaches browser-visible APIs.
- The dashboard should show a privacy notice explaining that only repair metadata is displayed and raw session values are not shown.
- Make certificate trust risk explicit before the download link.
- Provide cleanup instructions:
  - Turn off the iPhone proxy.
  - Delete the installed profile if desired.
  - Disable full trust for the certificate after repair.
- Keep the repair proxy port separate from the website port.

## Deployment Shape

Expected server layout:

- Static website files under a predictable directory, for example `/var/www/claude-ios-repair`.
- Nginx terminates HTTPS on `443`.
- Nginx reverse proxies dashboard API paths to a local status backend.
- Existing GOST WARP proxy remains on `8443`.
- New mitmproxy repair service runs on `9443`.
- Repair proxy emits sanitized events to the status backend.
- A systemd service supervises the repair proxy.
- A systemd service supervises the status backend.
- Certificate material for the website and MITM CA are stored separately.

The implementation should not overwrite existing proxy services until their port changes are explicit and reversible.

## Testing

Local website tests:

- Static files build or lint without errors.
- Page renders on desktop and mobile widths.
- Links and anchors work.
- Certificate download link returns the expected file.
- No proxy credentials appear in generated files.
- Dashboard renders empty, active, success, and failure states.
- Dashboard does not render raw Cookie, `sessionKey`, `routingHint`, Authorization, or raw device identifier values.

Server tests:

- `https://sg2.claude89757.cc` serves the website on port `443`.
- Existing WARP proxy still works on its non-website port.
- Repair proxy requires administrator-provided access.
- Status page only shows sessions by repair session ID and does not expose a global list of users.
- Through the repair proxy, `claude.ai/api/account` gets the intended `401 session_expired` response and cookie deletion headers.
- Status backend receives a sanitized event for the rewritten `/api/account` response.
- Non-target traffic is not modified.

Manual iPhone smoke test:

1. Configure the repair proxy.
2. Install and trust the root certificate.
3. Open the live status page for the repair session.
4. Confirm the dashboard shows proxy connection and certificate trust.
5. Open Claude iOS with a known stuck old session.
6. Confirm the dashboard shows `/api/account` rewrite and cookie deletion headers.
7. Confirm the login screen appears.
8. Disable the proxy and certificate trust.
9. Log in with a valid new account.

## Implementation Defaults

- Website server: Nginx.
- Website port: `443`.
- General WARP proxy port: `8443`.
- Repair MITM proxy port: `9443`.
- Status backend: local service behind Nginx, using JSON plus Server-Sent Events.
- Public credential policy: do not display credentials; the site only says `联系管理员获取临时代理配置`.
- Contact method text: use a generic administrator contact block unless the implementation request provides a specific Telegram, email, WeChat, or other contact method.
