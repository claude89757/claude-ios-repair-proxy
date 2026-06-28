from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
import time

from repair_site.status_app.config import Settings, derive_proxy_password
from repair_site.status_app.invites import InviteStore


def settings(database_path: str = ":memory:") -> Settings:
    return Settings(
        admin_username="admin",
        admin_password_hash="sha256:unused",
        invite_secret="invite-secret",
        status_token_secret="status-secret",
        internal_api_secret="internal-secret",
        database_path=database_path,
    )


def test_create_invite_generates_unique_credentials():
    store = InviteStore(settings())

    invite = store.create_invite(note="first user")

    assert invite["invite_code"].startswith("INV-")
    assert invite["session_id"].startswith("sess_")
    assert invite["proxy_username"].startswith("repair_")
    assert invite["proxy_password"] == derive_proxy_password(
        invite["proxy_username"],
        version=invite["proxy_password_version"],
        secret="invite-secret",
    )
    assert invite["status"] == "active"


def test_create_invite_defaults_to_24_hour_expiration():
    store = InviteStore(settings())
    before = datetime.now(timezone.utc)

    invite = store.create_invite(note="temporary user")

    after = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(invite["expires_at"])
    assert before + timedelta(hours=24) <= expires_at <= after + timedelta(hours=24)


def test_ensure_invite_creates_fixed_code_once_with_explicit_expiration():
    store = InviteStore(settings())

    first = store.ensure_invite(
        invite_code="INV-VXK44LB9URXY",
        note="public invite acquisition gate",
        expires_at="2099-12-31T00:00:00+00:00",
    )
    second = store.ensure_invite(
        invite_code="INV-VXK44LB9URXY",
        note="public invite acquisition gate",
        expires_at="2099-12-31T00:00:00+00:00",
    )

    assert first["id"] == second["id"]
    assert first["proxy_port"] == second["proxy_port"]
    assert first["invite_code"] == "INV-VXK44LB9URXY"
    assert first["expires_at"] == "2099-12-31T00:00:00+00:00"
    assert len(store.list_invites()) == 1


def test_claim_invite_rejects_disabled_invite():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    store.disable_invite(invite["id"])

    assert store.claim_invite(invite["invite_code"]) is None


def test_verify_proxy_auth_maps_to_session_id():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    verified = store.verify_proxy_auth(
        invite["proxy_username"],
        invite["proxy_password"],
    )

    assert verified["session_id"] == invite["session_id"]
    assert store.verify_proxy_auth(invite["proxy_username"], "wrong") is None


def test_list_invites_omits_proxy_password():
    store = InviteStore(settings())
    store.create_invite(note="")

    invites = store.list_invites()

    assert "proxy_password" not in invites[0]


def test_verify_proxy_auth_omits_proxy_password():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    verified = store.verify_proxy_auth(
        invite["proxy_username"],
        invite["proxy_password"],
    )

    assert verified["session_id"] == invite["session_id"]
    assert "proxy_password" not in verified


def test_verify_proxy_auth_rejects_disabled_invite():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    store.disable_invite(invite["id"])

    assert store.verify_proxy_auth(
        invite["proxy_username"],
        invite["proxy_password"],
    ) is None


def test_disable_invite_omits_proxy_password():
    store = InviteStore(settings())
    invite = store.create_invite(note="")

    disabled = store.disable_invite(invite["id"])

    assert disabled["status"] == "disabled"
    assert "proxy_password" not in disabled


def test_expired_invite_claim_and_auth_rejected_with_timezone_string():
    store = InviteStore(settings())
    expires_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).astimezone(timezone(timedelta(hours=14))).isoformat()
    invite = store.create_invite(note="", expires_at=expires_at)

    assert store.claim_invite(invite["invite_code"]) is None
    assert store.verify_proxy_auth(
        invite["proxy_username"],
        invite["proxy_password"],
    ) is None


def test_reset_proxy_password_invalidates_old_password():
    store = InviteStore(settings())
    invite = store.create_invite(note="")
    old_password = invite["proxy_password"]

    reset = store.reset_proxy_password(invite["id"])

    assert reset["proxy_password"] != old_password
    assert store.verify_proxy_auth(invite["proxy_username"], old_password) is None
    assert store.verify_proxy_auth(invite["proxy_username"], reset["proxy_password"])


def test_file_backed_persistence_can_read_invite_from_second_store(tmp_path: Path):
    database_path = str(tmp_path / "invites.sqlite3")
    first_store = InviteStore(settings(database_path=database_path))
    invite = first_store.create_invite(note="persisted")

    second_store = InviteStore(settings(database_path=database_path))
    persisted = second_store.get_invite_by_id(invite["id"])

    assert Path(database_path).exists()
    assert persisted["invite_code"] == invite["invite_code"]
    assert persisted["session_id"] == invite["session_id"]
    assert "proxy_password" not in persisted


def test_legacy_active_invite_without_expiration_gets_default_on_reopen(tmp_path: Path):
    database_path = str(tmp_path / "legacy.sqlite3")
    first_store = InviteStore(settings(database_path=database_path))
    invite = first_store.create_invite(note="legacy")
    first_store.conn.execute("UPDATE invites SET expires_at = NULL WHERE id = ?", (invite["id"],))
    first_store.conn.commit()
    first_store.close()

    reopened = InviteStore(settings(database_path=database_path))
    migrated = reopened.get_invite_by_id(invite["id"])

    assert migrated["expires_at"] is not None


def test_shared_store_handles_concurrent_create_auth_and_disable(tmp_path: Path):
    store = InviteStore(settings(database_path=str(tmp_path / "concurrent.sqlite3")))
    store.conn.set_trace_callback(lambda _sql: time.sleep(0.0005))
    worker_count = 16
    iterations = 8
    start = threading.Barrier(worker_count)

    def worker(worker_id: int) -> list[int]:
        invite_ids = []
        start.wait()
        for iteration in range(iterations):
            invite = store.create_invite(note=f"{worker_id}-{iteration}")
            verified = store.verify_proxy_auth(
                invite["proxy_username"],
                invite["proxy_password"],
            )
            assert verified is not None
            assert verified["session_id"] == invite["session_id"]
            assert "proxy_password" not in verified

            disabled = store.disable_invite(invite["id"])

            assert disabled["status"] == "disabled"
            assert store.verify_proxy_auth(
                invite["proxy_username"],
                invite["proxy_password"],
            ) is None
            invite_ids.append(invite["id"])
        return invite_ids

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(worker, worker_id) for worker_id in range(worker_count)]
        invite_ids = [
            invite_id
            for future in futures
            for invite_id in future.result()
        ]

    assert len(invite_ids) == worker_count * iterations
    assert len(set(invite_ids)) == len(invite_ids)
    assert len(store.list_invites()) == len(invite_ids)
