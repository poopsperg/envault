"""Tests for the 'audit' subcommand added to the CLI."""

import pytest
from unittest.mock import patch

from envault.cli import build_parser, cmd_audit, cmd_lock, cmd_status
from envault import audit


def _args(extra, audit_log):
    parser = build_parser()
    return parser.parse_args(["--audit-log", audit_log] + extra)


def test_parser_audit_default_tail(tmp_path):
    log = str(tmp_path / "a.json")
    args = _args(["audit"], log)
    assert args.tail == 20
    assert args.audit_log == log


def test_parser_audit_custom_tail(tmp_path):
    log = str(tmp_path / "a.json")
    args = _args(["audit", "--tail", "5"], log)
    assert args.tail == 5


def test_cmd_audit_empty_log(tmp_path, capsys):
    log = str(tmp_path / "a.json")
    args = _args(["audit"], log)
    rc = cmd_audit(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit events" in out


def test_cmd_audit_shows_events(tmp_path, capsys):
    log = str(tmp_path / "a.json")
    audit.record_event("lock", ".env", success=True, log_path=log)
    audit.record_event("unlock", ".env.vault", success=False, log_path=log)
    args = _args(["audit"], log)
    rc = cmd_audit(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "LOCK" in out
    assert "UNLOCK" in out
    assert "FAIL" in out


def test_cmd_audit_tail_limits_output(tmp_path, capsys):
    log = str(tmp_path / "a.json")
    for i in range(10):
        audit.record_event("lock", f".env{i}", success=True, log_path=log)
    args = _args(["audit", "--tail", "3"], log)
    cmd_audit(args)
    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 3


def test_lock_writes_audit_event(tmp_path):
    log = str(tmp_path / "audit.json")
    env = tmp_path / ".env"
    env.write_text("SECRET=hello", encoding="utf-8")
    args = _args(["lock", str(env)], log)
    with patch("getpass.getpass", return_value="passphrase123"):
        cmd_lock(args)
    events = audit.get_events(log_path=log)
    assert len(events) == 1
    assert events[0]["action"] == "lock"
    assert events[0]["success"] is True
