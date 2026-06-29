---
name: claude-ios-repair-ops
description: Operate and maintain the Claude iOS repair proxy production service. Use when Codex is asked to deploy this project, restart or inspect remote services, debug production website/API/admin/invite/proxy-port behavior, manage Nginx or Let's Encrypt certificates, verify domain access, update Cloudflare DNS for claude89757.cc, or run production health checks for this repository.
---

# Claude iOS Repair Ops

Use this skill for production operations for this repository. Treat it as the runbook for server, program, certificate, domain, and Cloudflare work.

## First Rules

- Read `references/production-ops.md` before touching the production server, Cloudflare DNS, Nginx, certificates, systemd services, Docker containers, or live proxy ports.
- Never print secrets from `_private/sg_proxy.txt`, `_private/production_app.env`, cookies, session keys, routing hints, Cloudflare tokens, or admin credentials. Use them only through command substitution or private environment variables.
- Keep Cloudflare DNS records for `claude89757.cc` and `sg2.claude89757.cc` DNS-only unless the user explicitly accepts losing custom repair proxy ports. Cloudflare proxy mode does not support the `100xx` repair ports.
- Prefer read-only inspection before mutation. For live changes, collect current state, make the smallest change, then verify from both the server and public internet.
- Treat GitHub Actions as the canonical production release path. A release is not complete until the `Deploy production` workflow run is `completed/success`, all deploy verification steps succeeded, and `/opt/claude-ios-repair/REVISION` matches the workflow commit SHA.
- Use the GitHub plugin/app for structured workflow, job, and step status when available; use `gh run` for watching runs and fetching logs. Do not replace the GitHub Actions path with direct SSH deployment unless Actions is unavailable/failing for infrastructure reasons or the user explicitly asks for fallback.
- When changing Cloudflare, use the Cloudflare plugin/API tools. Search the API spec first when the endpoint or payload is not already known.
- When committing repo changes, beware that this workspace can have local Git object issues; use a clean temp clone when `git status`, `git diff`, or `git show` hangs.

## Common Workflows

### Deploy or Upgrade

1. Inspect the requested scope and current repo changes.
2. Run relevant tests locally before packaging. At minimum use focused tests for touched code; use full `pytest -q` when backend/deploy behavior changes.
3. Commit and push to `main`, or trigger `.github/workflows/deploy-production.yml` with `workflow_dispatch` when redeploying an existing commit.
4. Watch the `Deploy production` GitHub Actions run to completion and inspect the `Test and deploy production` job steps. If any step fails, diagnose that run before touching production manually.
5. After workflow success, verify `/opt/claude-ios-repair/REVISION` equals the workflow `headSha`, then verify Nginx, HTTPS domains, API health, service state, and active ports from both the server and public internet.
6. Use the fallback SSH/tar deploy sequence in `references/production-ops.md` only when GitHub Actions cannot complete for an infrastructure reason or the user explicitly requests bypassing automation.
7. Report commit SHA, workflow run ID/result, deployed revision, service status, test results, and any skipped checks.

### Debug Production

1. Classify the problem: website, admin, invite API, status API, certificate download, repair proxy port, Claude/Anthropic traffic, Cloudflare DNS, or TLS certificate.
2. Gather sanitized evidence first: HTTP status, recent systemd logs, container names, listening ports, cert SAN/dates, relevant DNS records.
3. Do not expose raw request bodies, cookies, session keys, proxy passwords, device identifiers, or full user IPs in the final answer.
4. Apply the narrowest fix, then run the matching post-check from the reference.

### Domain, DNS, and Certificates

1. Use Cloudflare API to inspect zone `claude89757.cc` and A records for `claude89757.cc` and `sg2.claude89757.cc`.
2. Keep both records pointed at the production server IP and DNS-only unless explicitly changing architecture.
3. Keep Nginx `server_name` and the Let's Encrypt certificate SAN aligned for both hostnames.
4. Use webroot ACME renewal, not standalone, so Nginx can remain online during renewal.
5. Always run `certbot renew --dry-run --no-random-sleep-on-renew` after certificate or renewal changes.

## Reference

- `references/production-ops.md`: topology, paths, safe SSH pattern, deploy sequence, Cloudflare DNS operations, certificate renewal, and verification commands.
