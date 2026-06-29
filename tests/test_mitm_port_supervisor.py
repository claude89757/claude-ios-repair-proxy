import sqlite3

from repair_site.mitm.port_supervisor import (
    ProxyTarget,
    build_child_env,
    build_mitmdump_command,
    reconcile_processes,
    run_supervisor_iteration,
)


class FakeProcess:
    def __init__(self, returncode=None):
        self.returncode = returncode
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True


def test_build_mitmdump_command_listens_on_invite_port():
    command = build_mitmdump_command(10001)

    assert command[:1] == ["mitmdump"]
    assert "--listen-port" in command
    assert command[command.index("--listen-port") + 1] == "10001"
    assert "--mode" in command
    assert "regular" in command


def test_child_env_sets_repair_session_for_port_target():
    env = build_child_env({"KEEP": "yes"}, ProxyTarget(proxy_port=10001, session_id="sess_a"))

    assert env["KEEP"] == "yes"
    assert env["REPAIR_SESSION_ID"] == "sess_a"
    assert env["PYTHONPATH"] == "/opt/claude-ios-repair"


def test_reconcile_processes_starts_and_stops_by_proxy_port():
    created = []

    def popen_factory(command, env):
        process = FakeProcess()
        created.append((command, env, process))
        return process

    old_process = FakeProcess()
    stale_process = FakeProcess()
    processes = {
        10001: old_process,
        10002: stale_process,
    }
    targets = [
        ProxyTarget(proxy_port=10001, session_id="sess_a"),
        ProxyTarget(proxy_port=10003, session_id="sess_c"),
    ]

    reconcile_processes(
        targets,
        processes,
        base_env={"BASE": "1"},
        popen_factory=popen_factory,
    )

    assert old_process.terminated is False
    assert stale_process.terminated is True
    assert 10002 not in processes
    assert 10003 in processes
    assert created[0][0][created[0][0].index("--listen-port") + 1] == "10003"
    assert created[0][1]["REPAIR_SESSION_ID"] == "sess_c"


def test_supervisor_iteration_keeps_existing_processes_on_database_lock():
    process = FakeProcess()
    processes = {10001: process}

    def locked_loader(_settings):
        raise sqlite3.OperationalError("database is locked")

    ran = run_supervisor_iteration(
        object(),
        processes,
        target_loader=locked_loader,
        base_env={},
        popen_factory=lambda _command, _env: FakeProcess(),
    )

    assert ran is False
    assert processes == {10001: process}
    assert process.terminated is False
