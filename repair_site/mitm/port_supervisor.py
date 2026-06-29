from __future__ import annotations

import logging
import os
import signal
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from repair_site.status_app.config import Settings, load_settings, require_configured
from repair_site.status_app.invites import InviteStore

APP_ROOT = Path("/opt/claude-ios-repair")
ADDON_PATH = APP_ROOT / "repair_site" / "mitm" / "claude_repair_addon.py"
POLL_SECONDS = 5
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProxyTarget:
    proxy_port: int
    session_id: str


class ProcessLike(Protocol):
    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...


class PopenFactory(Protocol):
    def __call__(self, command: list[str], env: dict[str, str]) -> ProcessLike: ...


class TargetLoader(Protocol):
    def __call__(self, settings: Settings) -> list[ProxyTarget]: ...


def build_mitmdump_command(proxy_port: int) -> list[str]:
    return [
        "mitmdump",
        "--listen-host",
        "0.0.0.0",
        "--listen-port",
        str(proxy_port),
        "--mode",
        "regular",
        "--set",
        "block_global=false",
        "-s",
        str(ADDON_PATH),
    ]


def build_child_env(base_env: dict[str, str], target: ProxyTarget) -> dict[str, str]:
    env = dict(base_env)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(APP_ROOT)
    env["REPAIR_SESSION_ID"] = target.session_id
    return env


def load_targets(settings: Settings) -> list[ProxyTarget]:
    store = InviteStore(settings, initialize_schema=False)
    try:
        return [
            ProxyTarget(
                proxy_port=int(target["proxy_port"]),
                session_id=str(target["session_id"]),
            )
            for target in store.list_active_proxy_targets_read_only()
        ]
    finally:
        store.close()


def _default_popen(command: list[str], env: dict[str, str]) -> ProcessLike:
    return subprocess.Popen(command, env=env)


def _stop_process(process: ProcessLike) -> None:
    if process.poll() is None:
        process.terminate()


def reconcile_processes(
    targets: list[ProxyTarget],
    processes: dict[int, ProcessLike],
    *,
    base_env: dict[str, str] | None = None,
    popen_factory: PopenFactory = _default_popen,
) -> None:
    base_env = base_env or os.environ.copy()
    desired = {target.proxy_port: target for target in targets}

    for port, process in list(processes.items()):
        if port not in desired or process.poll() is not None:
            _stop_process(process)
            processes.pop(port, None)

    for port, target in desired.items():
        if port in processes:
            continue
        processes[port] = popen_factory(
            build_mitmdump_command(port),
            build_child_env(base_env, target),
        )


def _is_database_lock_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "database is locked" in message or "database table is locked" in message


def run_supervisor_iteration(
    settings: Settings,
    processes: dict[int, ProcessLike],
    *,
    target_loader: TargetLoader = load_targets,
    base_env: dict[str, str] | None = None,
    popen_factory: PopenFactory = _default_popen,
) -> bool:
    try:
        targets = target_loader(settings)
    except sqlite3.OperationalError as exc:
        if not _is_database_lock_error(exc):
            raise
        LOGGER.warning("Skipping mitm target reconciliation while invite database is locked")
        return False
    reconcile_processes(
        targets,
        processes,
        base_env=base_env,
        popen_factory=popen_factory,
    )
    return True


def main() -> None:
    settings = load_settings()
    require_configured(settings)
    processes: dict[int, ProcessLike] = {}
    stopping = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    try:
        while not stopping:
            run_supervisor_iteration(settings, processes)
            time.sleep(POLL_SECONDS)
    finally:
        for process in list(processes.values()):
            _stop_process(process)


if __name__ == "__main__":
    main()
