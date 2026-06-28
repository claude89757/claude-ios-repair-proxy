from pathlib import Path


DEPLOY = Path("repair_site/deploy")
ACTIONS = Path(".github/workflows")


def read_deploy_file(name: str) -> str:
    return (DEPLOY / name).read_text()


def test_status_service_uses_app_env_and_persistent_invite_database_volume():
    service = read_deploy_file("claude-repair-status.service")

    assert "EnvironmentFile=-/etc/claude-repair/app.env" in service
    assert "ExecStartPre=/usr/bin/mkdir -p /opt/claude-ios-repair/data" in service
    assert "--env-file /etc/claude-repair/app.env" in service
    assert "-v /opt/claude-ios-repair/data:/opt/claude-ios-repair/data" in service


def test_mitm_service_runs_port_supervisor_and_uses_invite_data_volume():
    service = read_deploy_file("claude-repair-mitm.service")

    assert "EnvironmentFile=-/etc/claude-repair/app.env" in service
    assert "python -m repair_site.mitm.port_supervisor" in service
    assert "-v /opt/claude-ios-repair/data:/opt/claude-ios-repair/data" in service
    assert "--env-file /etc/claude-repair/app.env" in service
    assert "REPAIR_STATUS_URL" in service
    assert "REPAIR_AUTH_URL" not in service
    assert "--listen-port 9443" not in service
    assert "--proxyauth" not in service
    assert "REPAIR_PROXY_AUTH" not in service
    assert "REPAIR_SESSION_ID" not in service
    assert "default" not in service


def test_dockerfile_declares_persistent_invite_data_volume():
    dockerfile = read_deploy_file("Dockerfile")

    assert "RUN mkdir -p /opt/claude-ios-repair/data" in dockerfile
    assert 'VOLUME ["/opt/claude-ios-repair/data"]' in dockerfile


def test_nginx_serves_admin_page_without_falling_back_to_public_index():
    nginx = read_deploy_file("nginx.conf")

    assert "root /opt/claude-ios-repair/repair_site/web;" in nginx
    assert "location = /admin" in nginx
    assert "try_files /admin.html =404;" in nginx


def test_nginx_supports_apex_and_sg2_domains_with_acme_webroot():
    nginx = read_deploy_file("nginx.conf")

    assert "server_name sg2.claude89757.cc claude89757.cc;" in nginx
    assert "listen 80;" in nginx
    assert "listen [::]:80;" in nginx
    assert "location ^~ /.well-known/acme-challenge/" in nginx
    assert "root /var/www/letsencrypt;" in nginx
    assert "return 301 https://$host$request_uri;" in nginx
    assert "/etc/letsencrypt/live/sg2.claude89757.cc/fullchain.pem" in nginx


def test_nginx_serves_mitmproxy_certificate_without_spa_fallback():
    nginx = read_deploy_file("nginx.conf")

    assert "location = /certs/mitmproxy-ca-cert.cer" in nginx
    assert "alias /opt/claude-ios-repair/mitmproxy/mitmproxy-ca-cert.cer;" in nginx
    assert "default_type application/x-x509-ca-cert;" in nginx
    assert "location /certs/" in nginx
    assert "return 404;" in nginx


def test_github_actions_deploys_production_with_hardened_ssh_and_checks():
    workflow = (ACTIONS / "deploy-production.yml").read_text()

    assert "name: Deploy production" in workflow
    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "environment: production" in workflow
    assert "concurrency:" in workflow
    assert "group: production" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow

    assert "PROD_SSH_PRIVATE_KEY" in workflow
    assert "PROD_SSH_KNOWN_HOSTS" in workflow
    assert "StrictHostKeyChecking=yes" in workflow
    assert "ssh-keyscan" not in workflow
    assert "sshpass" not in workflow

    assert "pytest" in workflow
    assert "requirements.txt repair_site" in workflow
    assert "release-${GITHUB_SHA}" in workflow
    assert "claude-ios-repair:${GITHUB_SHA}" in workflow
    assert "docker tag claude-ios-repair:${GITHUB_SHA} claude-ios-repair:latest" in workflow
    assert "/opt/claude-ios-repair/REVISION" in workflow
    assert "nginx -t" in workflow
    assert "systemctl restart claude-repair-status.service" in workflow
    assert "systemctl restart claude-repair-mitm.service" in workflow
    assert "https://sg2.claude89757.cc/api/health" in workflow
    assert "https://claude89757.cc/api/health" in workflow
    assert "https://sg2.claude89757.cc/certs/mitmproxy-ca-cert.cer" in workflow


def test_github_actions_ci_runs_tests_without_deploying_on_pull_requests():
    workflow = (ACTIONS / "ci.yml").read_text()

    assert "name: CI" in workflow
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "python -m pytest" in workflow
    assert "environment: production" not in workflow
    assert "PROD_SSH_PRIVATE_KEY" not in workflow
    assert "scp" not in workflow
    assert "systemctl restart" not in workflow
