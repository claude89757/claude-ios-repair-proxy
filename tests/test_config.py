from repair_site.status_app.config import (
    Settings,
    _b64encode,
    _urlsafe_digest,
    derive_proxy_password,
    load_settings,
    new_invite_code,
    new_proxy_username,
    pbkdf2_password_hash,
    require_configured,
    sign_status_token,
    verify_status_token,
    verify_admin_password,
)


def signed_payload(payload_json: str) -> str:
    payload = _b64encode(payload_json.encode("utf-8"))
    signature = _urlsafe_digest(payload, "status-secret", length=32)
    return payload + "." + signature


def test_derive_proxy_password_is_repeatable_and_secret_dependent():
    first = derive_proxy_password("repair_abcd", version=1, secret="secret-a")
    second = derive_proxy_password("repair_abcd", version=1, secret="secret-a")
    third = derive_proxy_password("repair_abcd", version=1, secret="secret-b")

    assert first == second
    assert first != third
    assert len(first) >= 24


def test_derive_proxy_password_rejects_empty_secret():
    try:
        derive_proxy_password("repair_abcd", version=1, secret="")
    except ValueError as exc:
        assert "secret" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_status_token_round_trip_and_tamper_rejection():
    token = sign_status_token("session-123", secret="status-secret")

    assert verify_status_token(token, secret="status-secret") == "session-123"
    assert verify_status_token(token + "x", secret="status-secret") is None


def test_status_token_rejects_empty_secret():
    try:
        sign_status_token("session-123", secret="")
    except ValueError as exc:
        assert "secret" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert verify_status_token("payload.signature", secret="") is None


def test_status_token_rejects_malformed_and_expired_tokens():
    expired = sign_status_token("session-123", secret="status-secret", ttl_seconds=-1)

    assert verify_status_token("not-a-token", secret="status-secret") is None
    assert verify_status_token("payload.signature.extra", secret="status-secret") is None
    assert verify_status_token(expired, secret="status-secret") is None


def test_status_token_rejects_signed_malformed_payloads():
    assert verify_status_token(
        signed_payload('{"purpose":"admin","session_id":"session-123","exp":9999999999}'),
        secret="status-secret",
    ) is None
    assert verify_status_token(
        signed_payload('{"purpose":"status","exp":9999999999}'),
        secret="status-secret",
    ) is None
    assert verify_status_token(
        signed_payload('{"purpose":"status","session_id":123,"exp":9999999999}'),
        secret="status-secret",
    ) is None
    assert verify_status_token(
        signed_payload('{"purpose":"status","session_id":"session-123","exp":"bad"}'),
        secret="status-secret",
    ) is None
    assert verify_status_token(signed_payload("[]"), secret="status-secret") is None
    assert verify_status_token(signed_payload('"x"'), secret="status-secret") is None


def test_generated_invite_code_and_proxy_username_have_fixed_lengths(monkeypatch):
    values = iter([
        "____________",
        "----------",
        "abcDEFghiJKL",
        "123456789abc",
        "____________",
        "----------",
        "abcDEFghiJ",
    ])
    monkeypatch.setattr("repair_site.status_app.config.secrets.token_urlsafe", lambda size: next(values))

    assert new_invite_code() == "INV-ABCDEFGHIJKL"
    assert len(new_invite_code()) == len("INV-ABCDEFGHIJKL")
    assert len(new_proxy_username()) == len("repair_abcdefghij")


def test_admin_password_hash_verification():
    settings = Settings(
        admin_username="admin",
        admin_password_hash="sha256:2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )

    assert verify_admin_password("secret", settings) is True
    assert verify_admin_password("wrong", settings) is False


def test_pbkdf2_admin_password_hash_verification():
    settings = Settings(
        admin_username="admin",
        admin_password_hash=pbkdf2_password_hash("secret", salt=b"salt", iterations=1000),
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )

    assert verify_admin_password("secret", settings) is True
    assert verify_admin_password("wrong", settings) is False


def test_require_configured_enforces_required_settings():
    settings = Settings(
        admin_username="admin",
        admin_password_hash="",
        invite_secret="invite-secret",
        status_token_secret="",
        internal_api_secret="internal-secret",
        database_path=":memory:",
    )

    try:
        require_configured(settings)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert "ADMIN_PASSWORD_HASH" in message
    assert "STATUS_TOKEN_SECRET" in message


def test_public_free_invite_ttl_defaults_to_30_minutes(monkeypatch):
    monkeypatch.delenv("PUBLIC_FREE_INVITE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("PUBLIC_INVITE_TTL_SECONDS", raising=False)

    settings = load_settings()

    assert settings.public_free_invite_ttl_seconds == 1800
    assert settings.public_invite_ttl_seconds == 3600
