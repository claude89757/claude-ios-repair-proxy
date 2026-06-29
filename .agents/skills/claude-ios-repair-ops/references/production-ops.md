# Production Ops Reference

## Topology

- Repository: `/Users/claude89757/Desktop/cc`
- GitHub remote: `claude89757/claude-ios-repair-proxy`
- Production host: `43.160.213.247`
- Public hostnames: `sg2.claude89757.cc`, `claude89757.cc`
- Cloudflare zone: `claude89757.cc`, zone id `741a41032993004661579d76e63668bf`
- Production app path: `/opt/claude-ios-repair`
- Production env file: `/etc/claude-repair/app.env`
- Persistent data: `/opt/claude-ios-repair/data`
- mitmproxy CA/state: `/opt/claude-ios-repair/mitmproxy`
- Nginx site: `/etc/nginx/conf.d/claude-ios-repair.conf`
- Let's Encrypt cert: `/etc/letsencrypt/live/sg2.claude89757.cc/fullchain.pem`
- Renewal timer: `certbot-renew.timer`
- Primary deployment path: GitHub Actions workflow `.github/workflows/deploy-production.yml`
- Fallback deployment path: local tar/scp sequence in this runbook

## Ports and Services

- `80`: Nginx ACME challenge and HTTP-to-HTTPS redirect.
- `443`: Nginx web app and API reverse proxy.
- `9000`: local FastAPI backend, bound to `127.0.0.1`.
- `10001-10999`: per-invite repair proxy ports.
- `8080`: regular HTTP proxy container.
- `8443`: regular HTTPS proxy through WARP.
- `40000`: local WARP SOCKS endpoint.

Systemd and containers:

- `nginx`
- `claude-repair-status.service` -> Docker container `claude-repair-status`
- `claude-repair-mitm.service` -> Docker container `claude-repair-mitm`
- `gost`
- `gost-warp`

## Secret Handling

Use `_private/sg_proxy.txt` only as a local secret source. Do not print it.

Safe SSH pattern:

```bash
export SSHPASS="$(python3 - <<'PY'
from pathlib import Path
import re
text = Path('_private/sg_proxy.txt').read_text()
match = re.search(r'SSH 密码[：:]\s*(\S+)', text)
if not match:
    raise SystemExit('missing ssh password')
print(match.group(1))
PY
)"
sshpass -e ssh -o StrictHostKeyChecking=no root@43.160.213.247 'hostname'
```

When showing command output to the user, mask or omit passwords, cookies, tokens, session keys, routing hints, request bodies, and full device IDs.

## Production Preflight

Run this before changing live state:

```bash
sshpass -e ssh -o StrictHostKeyChecking=no root@43.160.213.247 'set -euo pipefail
  echo "--- services"
  systemctl is-active nginx || true
  systemctl is-active claude-repair-status.service || true
  systemctl is-active claude-repair-mitm.service || true
  echo "--- containers"
  docker ps --format "{{.Names}} {{.Status}}"
  echo "--- listeners"
  ss -ltnp | awk "/:(80|443|9000|8080|8443|100[0-9][0-9])\\b/ {print \$1,\$4,\$7}"
  echo "--- certificate"
  openssl x509 -in /etc/letsencrypt/live/sg2.claude89757.cc/fullchain.pem -noout -dates -ext subjectAltName
  echo "--- cert renewal"
  systemctl is-enabled certbot-renew.timer || true
  systemctl is-active certbot-renew.timer || true
'
```

## GitHub Actions Deployment

The default production deploy path is GitHub Actions:

- Repository environment: `production`
- Trigger: push to `main`, with `workflow_dispatch` for manual redeploys
- Workflow file: `.github/workflows/deploy-production.yml`
- Concurrency group: `production`
- Job name: `Test and deploy production`
- Workflow name: `Deploy production`

Required GitHub environment variables:

- `PROD_SSH_HOST`: `43.160.213.247`
- `PROD_SSH_USER`: `root`
- `PROD_SSH_PORT`: `22`

Required GitHub environment secrets:

- `PROD_SSH_PRIVATE_KEY`: dedicated deploy SSH private key
- `PROD_SSH_KNOWN_HOSTS`: pinned SSH host key line for the production host

The workflow runs tests, packages only `requirements.txt` and `repair_site`, uploads
the package to `/tmp/claude-ios-repair-deploy`, builds
`claude-ios-repair:<commit_sha>` on the server, tags it as
`claude-ios-repair:latest`, updates `/opt/claude-ios-repair`, and writes the
deployed commit to `/opt/claude-ios-repair/REVISION`.

Do not store `/etc/claude-repair/app.env`, SQLite data, mitmproxy CA/state, SSH
passwords, Cloudflare tokens, cookies, or request payloads in GitHub.

Release completion criteria:

1. `origin/main` points at the intended commit.
2. The matching `Deploy production` workflow run is `completed` with conclusion `success`.
3. The `Test and deploy production` job steps `Run tests`, `Package release`, `Upload release`, `Deploy on server`, and `Verify public endpoints` are all `success`.
4. `/opt/claude-ios-repair/REVISION` on the server exactly matches the workflow `headSha`.
5. Independent post-deploy checks from this runbook pass after the workflow finishes.

Use the GitHub plugin/app for structured workflow, job, and step status when it is available. Use `gh` for watching a run, fetching logs, and workflow dispatch operations:

```bash
gh run list \
  --repo claude89757/claude-ios-repair-proxy \
  --workflow "Deploy production" \
  --branch main \
  --limit 5 \
  --json databaseId,status,conclusion,event,headSha,displayTitle,createdAt,updatedAt,url

gh run watch <run_id> \
  --repo claude89757/claude-ios-repair-proxy \
  --exit-status

gh run view <run_id> \
  --repo claude89757/claude-ios-repair-proxy \
  --json databaseId,status,conclusion,event,workflowName,headSha,createdAt,updatedAt,displayTitle,url,jobs
```

For a manual redeploy of the current `main` commit without new code changes:

```bash
gh workflow run "Deploy production" \
  --repo claude89757/claude-ios-repair-proxy \
  --ref main
```

Initial setup checklist:

```bash
# Generate locally; never commit either key file.
ssh-keygen -t ed25519 -C claude-ios-repair-github-actions -f /tmp/claude-ios-repair-deploy-key -N ''

# Add /tmp/claude-ios-repair-deploy-key.pub to root@43.160.213.247:~/.ssh/authorized_keys.
# Add /tmp/claude-ios-repair-deploy-key as GitHub environment secret PROD_SSH_PRIVATE_KEY.
# Add a verified host-key line as GitHub environment secret PROD_SSH_KNOWN_HOSTS.
```

Post-deploy checks are built into the workflow:

```bash
systemctl is-active claude-repair-status.service
systemctl is-active claude-repair-mitm.service
curl -fsS https://sg2.claude89757.cc/api/health
curl -fsS https://claude89757.cc/api/health
curl -fsSI https://sg2.claude89757.cc/certs/mitmproxy-ca-cert.cer
```

Always run an independent revision and service check after the workflow succeeds:

```bash
sshpass -e ssh -o StrictHostKeyChecking=no root@43.160.213.247 'set -euo pipefail
  printf "revision="; cat /opt/claude-ios-repair/REVISION
  echo
  systemctl is-active nginx
  systemctl is-active claude-repair-status.service
  systemctl is-active claude-repair-mitm.service
  docker ps --format "{{.Names}} {{.Status}}"
'
```

## Fallback Deploy Sequence

Use this only when GitHub Actions cannot complete for an infrastructure reason or the user explicitly requests bypassing the automation. Prefer fixing the workflow failure when the failure is caused by code, tests, packaging, server deploy commands, or public verification checks.

Use a clean temp clone if local Git commands hang or the worktree is dirty with unrelated changes.

Package and deploy only `requirements.txt` and `repair_site`:

```bash
ARCHIVE=/tmp/claude-ios-repair-deploy.tgz
tar -C /path/to/clean/clone -czf "$ARCHIVE" requirements.txt repair_site
sshpass -e ssh -o StrictHostKeyChecking=no root@43.160.213.247 'mkdir -p /opt/claude-ios-repair /tmp/claude-ios-repair-deploy'
sshpass -e scp -o StrictHostKeyChecking=no "$ARCHIVE" root@43.160.213.247:/tmp/claude-ios-repair-deploy/app.tgz
sshpass -e ssh -o StrictHostKeyChecking=no root@43.160.213.247 'set -euo pipefail
  cd /opt/claude-ios-repair
  tar -xzf /tmp/claude-ios-repair-deploy/app.tgz
  docker build -f repair_site/deploy/Dockerfile -t claude-ios-repair:latest .
  install -D -m 0644 repair_site/deploy/claude-repair-status.service /etc/systemd/system/claude-repair-status.service
  install -D -m 0644 repair_site/deploy/claude-repair-mitm.service /etc/systemd/system/claude-repair-mitm.service
  install -D -m 0644 repair_site/deploy/nginx.conf /etc/nginx/conf.d/claude-ios-repair.conf
  mkdir -p /var/www/letsencrypt/.well-known/acme-challenge
  systemctl daemon-reload
  nginx -t
  systemctl reload nginx
  systemctl restart claude-repair-status.service
  sleep 2
  systemctl restart claude-repair-mitm.service
  sleep 2
  systemctl is-active claude-repair-status.service
  systemctl is-active claude-repair-mitm.service
'
```

Post-deploy public checks:

```bash
python3 - <<'PY'
import urllib.request
for host in ["sg2.claude89757.cc", "claude89757.cc"]:
    with urllib.request.urlopen(f"https://{host}/zh", timeout=15) as resp:
        print(host, resp.status, resp.headers.get("content-type"))
    with urllib.request.urlopen(f"http://{host}/.well-known/acme-challenge/probe", timeout=15) as resp:
        print(host, "acme", resp.status, resp.read().decode().strip())
PY
```

## Cloudflare DNS

Use the Cloudflare API tools, not manual browser changes, when possible.

Expected records:

- `A claude89757.cc -> 43.160.213.247`, `proxied: false`, `ttl: 1`
- `A sg2.claude89757.cc -> 43.160.213.247`, `proxied: false`, `ttl: 1`

Keep DNS-only because users configure iPhone HTTP proxy ports such as `10003`, `10005`, etc. Cloudflare orange-cloud proxying only supports selected HTTP(S) ports and would break those repair ports.

Cloudflare inspection template:

```js
async () => {
  const zones = await cloudflare.request({ method: "GET", path: "/zones", query: { name: "claude89757.cc", per_page: 50 } });
  const zone = zones.result[0];
  const records = await cloudflare.request({ method: "GET", path: `/zones/${zone.id}/dns_records`, query: { per_page: 100 } });
  return (records.result || [])
    .filter(r => ["claude89757.cc", "sg2.claude89757.cc"].includes(r.name))
    .map(r => ({ type: r.type, name: r.name, content: r.content, proxied: r.proxied, ttl: r.ttl }));
}
```

Update apex A record only if it no longer points to the production IP:

```js
async () => cloudflare.request({
  method: "PATCH",
  path: `/zones/741a41032993004661579d76e63668bf/dns_records/<record_id>`,
  body: {
    type: "A",
    name: "claude89757.cc",
    content: "43.160.213.247",
    ttl: 1,
    proxied: false,
    comment: "Route apex web app to sg2 repair server; DNS-only keeps custom repair proxy ports usable."
  }
})
```

## Certificates

Nginx must serve `/.well-known/acme-challenge/` from `/var/www/letsencrypt` on port 80. Do not use standalone renewal while Nginx owns port 80.

Current certificate must include both hostnames:

```bash
openssl x509 -in /etc/letsencrypt/live/sg2.claude89757.cc/fullchain.pem -noout -dates -ext subjectAltName
```

Renew or expand certificate:

```bash
certbot certonly --webroot -w /var/www/letsencrypt \
  --cert-name sg2.claude89757.cc \
  -d sg2.claude89757.cc -d claude89757.cc \
  --expand --non-interactive --agree-tos \
  --deploy-hook "systemctl reload nginx"
```

Validate renewal:

```bash
certbot renew --dry-run --no-random-sleep-on-renew --quiet
```

If the system lacks `certbot.timer`, use the project-managed timer:

```ini
[Unit]
Description=Daily Lets Encrypt certificate renewal check

[Timer]
OnCalendar=*-*-* 03:17:00
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

Service:

```ini
[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet
```

Always keep `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` executable and reloading Nginx after real renewals.

## Debugging Guide

Website or admin page:

- Check `curl -I https://claude89757.cc/zh` and `https://sg2.claude89757.cc/zh`.
- Check Nginx active status and `/etc/nginx/conf.d/claude-ios-repair.conf`.
- Check Docker status backend container if `/api/` fails.

Invite/admin/API issue:

- Inspect `journalctl -u claude-repair-status.service -n 120 --no-pager`.
- Inspect `/opt/claude-ios-repair/data` only for schema and metadata; do not dump user-sensitive rows into chat.
- Verify `/etc/claude-repair/app.env` exists but do not print it.

Repair proxy port issue:

- Check the invite's assigned port in admin/status API, then verify `ss -ltnp`.
- Inspect `journalctl -u claude-repair-mitm.service -n 160 --no-pager`.
- If Claude traffic is absent, ask user to disable other VPN/proxy/tunneling apps and keep iPhone proxy auth off.
- If only CONNECT events appear and certificate remains unknown, confirm mitmproxy CA is installed and fully trusted on iPhone.

Certificate download issue:

- Check `https://<host>/certs/mitmproxy-ca-cert.cer`.
- Check file path `/opt/claude-ios-repair/mitmproxy/mitmproxy-ca-cert.cer`.
- Confirm Nginx `alias` and `Content-Disposition` lines are present.

Cloudflare/DNS issue:

- Verify A records with Cloudflare API and local DNS resolution.
- Keep records DNS-only unless the architecture changes away from direct custom repair ports.

## Final Response Checklist

Report:

- What changed.
- Which tests ran and exact pass/fail result.
- Production service status.
- Public URL checks.
- Certificate expiry date and SAN when certs changed.
- Cloudflare DNS state when DNS changed.
- Any known unrelated local test failures or dirty worktree caveats.

Do not report:

- SSH password, admin password, Cloudflare token, cookies, session keys, routing hints, full device IDs, or request bodies.
