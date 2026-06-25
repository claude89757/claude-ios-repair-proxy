from pathlib import Path


DEPLOY = Path("repair_site/deploy")


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


def test_nginx_serves_mitmproxy_certificate_without_spa_fallback():
    nginx = read_deploy_file("nginx.conf")

    assert "location = /certs/mitmproxy-ca-cert.cer" in nginx
    assert "alias /opt/claude-ios-repair/mitmproxy/mitmproxy-ca-cert.cer;" in nginx
    assert "default_type application/x-x509-ca-cert;" in nginx
    assert "location /certs/" in nginx
    assert "return 404;" in nginx
