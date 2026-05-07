"""Tests for the envault CLI."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.cli import build_parser, cmd_lock, cmd_unlock, cmd_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(command, file):
    ns = MagicMock()
    ns.command = command
    ns.file = file
    return ns


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_lock_default_file():
    parser = build_parser()
    args = parser.parse_args(["lock"])
    assert args.file == ".env"


def test_parser_unlock_default_file():
    parser = build_parser()
    args = parser.parse_args(["unlock"])
    assert args.file == ".env.vault"


def test_parser_status_custom_file():
    parser = build_parser()
    args = parser.parse_args(["status", "secrets.env"])
    assert args.file == "secrets.env"


# ---------------------------------------------------------------------------
# cmd_lock
# ---------------------------------------------------------------------------

def test_cmd_lock_missing_file(tmp_path):
    rc = cmd_lock(_args("lock", str(tmp_path / "missing.env")))
    assert rc == 1


def test_cmd_lock_already_locked(tmp_path):
    vault = tmp_path / ".env.vault"
    vault.write_text("data")
    with patch("envault.cli.is_locked", return_value=True):
        rc = cmd_lock(_args("lock", str(vault)))
    assert rc == 0


def test_cmd_lock_passphrase_mismatch(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SECRET=abc")
    with patch("envault.cli.is_locked", return_value=False), \
         patch("getpass.getpass", side_effect=["pass1", "pass2"]):
        rc = cmd_lock(_args("lock", str(env)))
    assert rc == 1


def test_cmd_lock_success(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SECRET=abc")
    vault = tmp_path / ".env.vault"
    with patch("envault.cli.is_locked", return_value=False), \
         patch("getpass.getpass", side_effect=["mypass", "mypass"]), \
         patch("envault.cli.lock", return_value=vault) as mock_lock:
        rc = cmd_lock(_args("lock", str(env)))
    assert rc == 0
    mock_lock.assert_called_once_with(env, "mypass")


# ---------------------------------------------------------------------------
# cmd_unlock
# ---------------------------------------------------------------------------

def test_cmd_unlock_missing_file(tmp_path):
    rc = cmd_unlock(_args("unlock", str(tmp_path / "missing.vault")))
    assert rc == 1


def test_cmd_unlock_not_a_vault(tmp_path):
    f = tmp_path / "plain.env"
    f.write_text("data")
    with patch("envault.cli.is_locked", return_value=False):
        rc = cmd_unlock(_args("unlock", str(f)))
    assert rc == 1


def test_cmd_unlock_wrong_passphrase(tmp_path):
    vault = tmp_path / ".env.vault"
    vault.write_text("encrypted")
    with patch("envault.cli.is_locked", return_value=True), \
         patch("getpass.getpass", return_value="wrong"), \
         patch("envault.cli.unlock", side_effect=ValueError("bad passphrase")):
        rc = cmd_unlock(_args("unlock", str(vault)))
    assert rc == 1


def test_cmd_unlock_success(tmp_path):
    vault = tmp_path / ".env.vault"
    vault.write_text("encrypted")
    env = tmp_path / ".env"
    with patch("envault.cli.is_locked", return_value=True), \
         patch("getpass.getpass", return_value="mypass"), \
         patch("envault.cli.unlock", return_value=env) as mock_unlock:
        rc = cmd_unlock(_args("unlock", str(vault)))
    assert rc == 0
    mock_unlock.assert_called_once_with(vault, "mypass")


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------

def test_cmd_status_missing_file(tmp_path):
    rc = cmd_status(_args("status", str(tmp_path / "nope.env")))
    assert rc == 1


def test_cmd_status_locked(tmp_path, capsys):
    f = tmp_path / ".env.vault"
    f.write_text("x")
    with patch("envault.cli.is_locked", return_value=True):
        rc = cmd_status(_args("status", str(f)))
    assert rc == 0
    assert "locked" in capsys.readouterr().out


def test_cmd_status_unlocked(tmp_path, capsys):
    f = tmp_path / ".env"
    f.write_text("SECRET=1")
    with patch("envault.cli.is_locked", return_value=False):
        rc = cmd_status(_args("status", str(f)))
    assert rc == 0
    assert "unlocked" in capsys.readouterr().out
