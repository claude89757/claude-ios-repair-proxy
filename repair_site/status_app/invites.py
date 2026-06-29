from __future__ import annotations

import hmac
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from repair_site.status_app.config import (
    Settings,
    derive_proxy_password,
    new_invite_code,
    new_proxy_username,
    new_session_id,
)

SQLITE_BUSY_TIMEOUT_MS = 30_000
SQLITE_BUSY_TIMEOUT_SECONDS = SQLITE_BUSY_TIMEOUT_MS / 1000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InviteStore:
    def __init__(self, settings: Settings, *, initialize_schema: bool = True) -> None:
        self.settings = settings
        if settings.database_path != ":memory:":
            Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(
            settings.database_path,
            check_same_thread=False,
            timeout=SQLITE_BUSY_TIMEOUT_SECONDS,
        )
        self.conn.row_factory = sqlite3.Row
        self._configure_connection(initialize_schema=initialize_schema)
        if initialize_schema:
            self.init_schema()

    def _configure_connection(self, *, initialize_schema: bool) -> None:
        self.conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
        if initialize_schema and self.settings.database_path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")

    def init_schema(self) -> None:
        with self._lock:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_code TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL UNIQUE,
                    proxy_username TEXT NOT NULL UNIQUE,
                    proxy_password_version INTEGER NOT NULL,
                    proxy_port INTEGER UNIQUE,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_used_at TEXT,
                    disabled_at TEXT,
                    source_ip TEXT,
                    source_geo TEXT,
                    repair_completed_at TEXT,
                    note TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row["name"])
                for row in self.conn.execute("PRAGMA table_info(invites)").fetchall()
            }
            if "proxy_port" not in columns:
                self.conn.execute("ALTER TABLE invites ADD COLUMN proxy_port INTEGER")
            if "source_ip" not in columns:
                self.conn.execute("ALTER TABLE invites ADD COLUMN source_ip TEXT")
            if "source_geo" not in columns:
                self.conn.execute("ALTER TABLE invites ADD COLUMN source_geo TEXT")
            if "repair_completed_at" not in columns:
                self.conn.execute("ALTER TABLE invites ADD COLUMN repair_completed_at TEXT")
            self.conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_invites_proxy_port ON invites(proxy_port)"
            )
            self._release_inactive_proxy_ports_locked()
            self._assign_missing_proxy_ports_locked()
            self._assign_missing_expires_at_locked()
            self.conn.commit()

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def _row_to_invite(
        self,
        row: sqlite3.Row | None,
        *,
        include_password: bool,
    ) -> dict[str, Any] | None:
        if row is None:
            return None
        invite = dict(row)
        if include_password:
            invite["proxy_password"] = derive_proxy_password(
                invite["proxy_username"],
                version=int(invite["proxy_password_version"]),
                secret=self.settings.invite_secret,
            )
        invite["repair_completed"] = invite.get("repair_completed_at") is not None
        return invite

    def create_invite(
        self,
        note: str,
        expires_at: str | None = None,
        source_ip: str | None = None,
        source_geo: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            for _ in range(10):
                try:
                    cursor = self.conn.execute(
                        """
                        INSERT INTO invites (
                            invite_code,
                            session_id,
                            proxy_username,
                            proxy_password_version,
                            proxy_port,
                            status,
                            created_at,
                            expires_at,
                            source_ip,
                            source_geo,
                            note
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_invite_code(),
                            new_session_id(),
                            new_proxy_username(),
                            1,
                            self._next_proxy_port_locked(),
                            "active",
                            now_iso(),
                            expires_at or self._default_expires_at_locked(),
                            source_ip,
                            source_geo,
                            note,
                        ),
                    )
                    self.conn.commit()
                    invite = self.get_invite_by_id(
                        int(cursor.lastrowid),
                        include_password=True,
                    )
                    if invite is None:
                        raise RuntimeError("created invite could not be read")
                    return invite
                except sqlite3.IntegrityError:
                    continue
        raise RuntimeError("could not create unique invite")

    def create_temporary_invite(
        self,
        *,
        note: str,
        ttl_seconds: int,
        source_ip: str | None = None,
        source_geo: str | None = None,
    ) -> dict[str, Any]:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        with self._lock:
            expires_at = self._expires_at_for_ttl_locked(ttl_seconds)
        return self.create_invite(
            note=note,
            expires_at=expires_at,
            source_ip=source_ip,
            source_geo=source_geo,
        )

    def ensure_invite(
        self,
        *,
        invite_code: str,
        note: str,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        normalized_code = invite_code.strip().upper()
        if not normalized_code:
            raise ValueError("invite_code must not be empty")

        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            row = self.conn.execute(
                "SELECT * FROM invites WHERE invite_code = ?",
                (normalized_code,),
            ).fetchone()
            invite = self._row_to_invite(row, include_password=True)
            if invite is not None:
                if (
                    invite.get("status") == "active"
                    and invite.get("disabled_at") is None
                    and expires_at
                    and self._is_expired(invite)
                ):
                    self.conn.execute(
                        "UPDATE invites SET expires_at = ? WHERE id = ?",
                        (expires_at, invite["id"]),
                    )
                    self.conn.commit()
                    refreshed = self.get_invite_by_id(invite["id"], include_password=True)
                    if refreshed is None:
                        raise RuntimeError("ensured invite could not be read")
                    return refreshed
                return invite

            for _ in range(10):
                try:
                    cursor = self.conn.execute(
                        """
                        INSERT INTO invites (
                            invite_code,
                            session_id,
                            proxy_username,
                            proxy_password_version,
                            proxy_port,
                            status,
                            created_at,
                            expires_at,
                            note
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            normalized_code,
                            new_session_id(),
                            new_proxy_username(),
                            1,
                            self._next_proxy_port_locked(),
                            "active",
                            now_iso(),
                            expires_at or self._default_expires_at_locked(),
                            note,
                        ),
                    )
                    self.conn.commit()
                    invite = self.get_invite_by_id(
                        int(cursor.lastrowid),
                        include_password=True,
                    )
                    if invite is None:
                        raise RuntimeError("ensured invite could not be read")
                    return invite
                except sqlite3.IntegrityError:
                    row = self.conn.execute(
                        "SELECT * FROM invites WHERE invite_code = ?",
                        (normalized_code,),
                    ).fetchone()
                    invite = self._row_to_invite(row, include_password=True)
                    if invite is not None:
                        return invite
                    continue
        raise RuntimeError("could not ensure unique invite")

    def list_invites(self) -> list[dict[str, Any]]:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            rows = self.conn.execute("SELECT * FROM invites ORDER BY id DESC").fetchall()
            return [
                invite
                for row in rows
                if (invite := self._row_to_invite(row, include_password=False))
                is not None
            ]

    def list_invites_page(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        query: str = "",
        status: str = "all",
        repair_status: str = "all",
    ) -> dict[str, Any]:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            safe_page = max(int(page), 1)
            safe_page_size = min(max(int(page_size), 1), 100)
            where: list[str] = []
            params: list[Any] = []

            normalized_status = status.strip().lower()
            if normalized_status and normalized_status != "all":
                where.append("status = ?")
                params.append(normalized_status)

            normalized_repair_status = repair_status.strip().lower()
            if normalized_repair_status == "completed":
                where.append("repair_completed_at IS NOT NULL")
            elif normalized_repair_status == "pending":
                where.append("repair_completed_at IS NULL")

            normalized_query = query.strip().lower()
            if normalized_query:
                like = f"%{normalized_query}%"
                where.append(
                    """
                    (
                        lower(invite_code) LIKE ?
                        OR lower(note) LIKE ?
                        OR lower(coalesce(source_ip, '')) LIKE ?
                        OR lower(coalesce(source_geo, '')) LIKE ?
                        OR CAST(proxy_port AS TEXT) LIKE ?
                    )
                    """
                )
                params.extend([like, like, like, like, like])

            where_sql = f"WHERE {' AND '.join(where)}" if where else ""
            total = int(
                self.conn.execute(
                    f"SELECT COUNT(*) AS count FROM invites {where_sql}",
                    params,
                ).fetchone()["count"]
            )
            offset = (safe_page - 1) * safe_page_size
            rows = self.conn.execute(
                f"""
                SELECT *
                FROM invites
                {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, safe_page_size, offset],
            ).fetchall()
            total_pages = max((total + safe_page_size - 1) // safe_page_size, 1)
            items = [
                invite
                for row in rows
                if (invite := self._row_to_invite(row, include_password=False))
                is not None
            ]
            return {
                "items": items,
                "page": safe_page,
                "page_size": safe_page_size,
                "total": total,
                "total_pages": total_pages,
            }

    def list_active_proxy_targets(self) -> list[dict[str, Any]]:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            return self._list_active_proxy_targets_locked()

    def list_active_proxy_targets_read_only(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._list_active_proxy_targets_locked()

    def get_invite_by_id(
        self,
        invite_id: int,
        include_password: bool = False,
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM invites WHERE id = ?",
                (invite_id,),
            ).fetchone()
            return self._row_to_invite(row, include_password=include_password)

    def claim_invite(self, invite_code: str) -> dict[str, Any] | None:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            row = self.conn.execute(
                """
                SELECT * FROM invites
                WHERE invite_code = ? AND status = 'active' AND disabled_at IS NULL
                """,
                (invite_code.strip(),),
            ).fetchone()
            invite = self._row_to_invite(row, include_password=True)
            if invite is None or self._is_expired(invite):
                return None
            self.conn.execute(
                "UPDATE invites SET last_used_at = ? WHERE id = ?",
                (now_iso(), invite["id"]),
            )
            self.conn.commit()
            return self.get_invite_by_id(invite["id"], include_password=True)

    def disable_invite(self, invite_id: int) -> dict[str, Any] | None:
        with self._lock:
            self.conn.execute(
                """
                UPDATE invites
                SET status = 'disabled', disabled_at = ?, proxy_port = NULL
                WHERE id = ?
                """,
                (now_iso(), invite_id),
            )
            self.conn.commit()
            return self.get_invite_by_id(invite_id)

    def reset_proxy_password(self, invite_id: int) -> dict[str, Any] | None:
        with self._lock:
            invite = self.get_invite_by_id(invite_id)
            if invite is None:
                return None
            self.conn.execute(
                """
                UPDATE invites
                SET proxy_password_version = proxy_password_version + 1
                WHERE id = ?
                """,
                (invite_id,),
            )
            self.conn.commit()
            return self.get_invite_by_id(invite_id, include_password=True)

    def mark_repair_completed_by_session(
        self,
        session_id: str,
        *,
        timestamp: str | None = None,
    ) -> bool:
        normalized_session_id = session_id.strip()
        if not normalized_session_id:
            return False
        with self._lock:
            cursor = self.conn.execute(
                """
                UPDATE invites
                SET repair_completed_at = COALESCE(repair_completed_at, ?)
                WHERE session_id = ?
                """,
                (timestamp or now_iso(), normalized_session_id),
            )
            self.conn.commit()
            return bool(cursor.rowcount)

    def verify_proxy_auth(
        self,
        proxy_username: str,
        proxy_password: str,
    ) -> dict[str, Any] | None:
        with self._lock:
            self._release_inactive_proxy_ports_locked()
            self._reclaim_expired_invites_locked()
            row = self.conn.execute(
                """
                SELECT * FROM invites
                WHERE proxy_username = ? AND status = 'active' AND disabled_at IS NULL
                """,
                (proxy_username,),
            ).fetchone()
            invite = self._row_to_invite(row, include_password=False)
            if invite is None or self._is_expired(invite):
                return None
            expected_password = derive_proxy_password(
                invite["proxy_username"],
                version=int(invite["proxy_password_version"]),
                secret=self.settings.invite_secret,
            )
            if not hmac.compare_digest(expected_password, proxy_password):
                return None
            return invite

    def _is_expired(self, invite: dict[str, Any]) -> bool:
        expires_at = invite.get("expires_at")
        if not expires_at:
            return False
        expires_at_dt = self._parse_iso_utc(expires_at)
        return expires_at_dt < datetime.now(timezone.utc)

    def _parse_iso_utc(self, value: str) -> datetime:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _default_expires_at_locked(self, created_at: str | None = None) -> str | None:
        ttl_seconds = self.settings.invite_default_ttl_seconds
        if ttl_seconds <= 0:
            return None
        if created_at:
            try:
                base = self._parse_iso_utc(created_at)
            except ValueError:
                base = datetime.now(timezone.utc)
        else:
            base = datetime.now(timezone.utc)
        return (base + timedelta(seconds=ttl_seconds)).isoformat()

    def _expires_at_for_ttl_locked(self, ttl_seconds: int) -> str:
        return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()

    def _reclaim_expired_invites_locked(self) -> int:
        rows = self.conn.execute(
            """
            SELECT *
            FROM invites
            WHERE status = 'active'
              AND disabled_at IS NULL
              AND proxy_port IS NOT NULL
            """
        ).fetchall()
        expired_ids = [
            int(row["id"])
            for row in rows
            if self._is_expired(dict(row))
        ]
        if not expired_ids:
            return 0
        self.conn.executemany(
            "UPDATE invites SET status = 'expired', proxy_port = NULL WHERE id = ?",
            [(invite_id,) for invite_id in expired_ids],
        )
        self.conn.commit()
        return len(expired_ids)

    def _list_active_proxy_targets_locked(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT session_id, proxy_port, expires_at
            FROM invites
            WHERE status = 'active'
              AND disabled_at IS NULL
              AND proxy_port IS NOT NULL
            ORDER BY proxy_port ASC
            """
        ).fetchall()
        targets: list[dict[str, Any]] = []
        for row in rows:
            invite = dict(row)
            if self._is_expired(invite):
                continue
            targets.append(
                {
                    "session_id": str(invite["session_id"]),
                    "proxy_port": int(invite["proxy_port"]),
                }
            )
        return targets

    def _release_inactive_proxy_ports_locked(self) -> int:
        cursor = self.conn.execute(
            """
            UPDATE invites
            SET proxy_port = NULL
            WHERE proxy_port IS NOT NULL
              AND (
                status != 'active'
                OR disabled_at IS NOT NULL
              )
            """
        )
        released = int(cursor.rowcount if cursor.rowcount is not None else 0)
        if released:
            self.conn.commit()
        return released

    def _assign_missing_expires_at_locked(self) -> None:
        rows = self.conn.execute(
            """
            SELECT id, created_at
            FROM invites
            WHERE expires_at IS NULL
              AND status = 'active'
              AND disabled_at IS NULL
            ORDER BY id ASC
            """
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "UPDATE invites SET expires_at = ? WHERE id = ?",
                (
                    self._default_expires_at_locked(str(row["created_at"])),
                    int(row["id"]),
                ),
            )

    def _assign_missing_proxy_ports_locked(self) -> None:
        self._release_inactive_proxy_ports_locked()
        self._reclaim_expired_invites_locked()
        rows = self.conn.execute(
            """
            SELECT id
            FROM invites
            WHERE proxy_port IS NULL
              AND status = 'active'
              AND disabled_at IS NULL
            ORDER BY id ASC
            """
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "UPDATE invites SET proxy_port = ? WHERE id = ?",
                (self._next_proxy_port_locked(), int(row["id"])),
            )

    def _next_proxy_port_locked(self) -> int:
        if self.settings.proxy_port_start > self.settings.proxy_port_end:
            raise RuntimeError("proxy port range is invalid")
        self._release_inactive_proxy_ports_locked()
        self._reclaim_expired_invites_locked()
        rows = self.conn.execute(
            """
            SELECT proxy_port
            FROM invites
            WHERE proxy_port IS NOT NULL
              AND status = 'active'
              AND disabled_at IS NULL
            """
        ).fetchall()
        used_ports = {int(row["proxy_port"]) for row in rows}
        for port in range(self.settings.proxy_port_start, self.settings.proxy_port_end + 1):
            if port not in used_ports:
                return port
        raise RuntimeError("proxy port range exhausted")
