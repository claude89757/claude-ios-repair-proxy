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


def test_mitm_service_uses_internal_invite_auth_and_no_legacy_proxy_auth():
    service = read_deploy_file("claude-repair-mitm.service")

    assert "EnvironmentFile=-/etc/claude-repair/app.env" in service
    assert (
        "Environment=REPAIR_AUTH_URL=http://127.0.0.1:9000/api/internal/proxy-auth/verify"
        in service
    )
    assert "-e REPAIR_AUTH_URL=" in service
    assert "-e INTERNAL_API_SECRET=" in service
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

    assert "location = /admin" in nginx
    assert "try_files /admin.html =404;" in nginx
