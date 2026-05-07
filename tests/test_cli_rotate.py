"""CLI-level tests for the 'envault rotate' sub-command."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.cli import build_parser, cmd_rotate
from envault.rotate import RotationError


ENV_CONTENT = "API_KEY=abc123\n"
OLD_PASS = "old"
NEW_PASS = "new"


def _args(**kwargs):
    defaults = dict(
        env=".env",
        vault=".env.vault",
        old_passphrase=OLD_PASS,
        new_passphrase=NEW_PASS,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- parser tests ---

def test_parser_rotate_defaults():
    parser = build_parser()
    args = parser.parse_args(["rotate", OLD_PASS, NEW_PASS])
    assert args.command == "rotate"
    assert args.env == ".env"
    assert args.vault == ".env.vault"
    assert args.old_passphrase == OLD_PASS
    assert args.new_passphrase == NEW_PASS


def test_parser_rotate_custom_paths():
    parser = build_parser()
    args = parser.parse_args(
        ["rotate", "--env", "prod.env", "--vault", "prod.vault", OLD_PASS, NEW_PASS]
    )
    assert args.env == "prod.env"
    assert args.vault == "prod.vault"


# --- cmd_rotate unit tests ---

def test_cmd_rotate_success(tmp_path):
    from envault.vault import lock
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, OLD_PASS)

    args = _args(env=str(env), vault=str(vault))
    result = cmd_rotate(args)
    assert result == 0
    assert vault.exists()


def test_cmd_rotate_rotation_error_returns_1(capsys):
    with patch("envault.cli.rotate", side_effect=RotationError("bad pass")):
        result = cmd_rotate(_args())
    assert result == 1
    captured = capsys.readouterr()
    assert "bad pass" in captured.err


def test_cmd_rotate_prints_success_message(tmp_path, capsys):
    from envault.vault import lock
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, OLD_PASS)

    args = _args(env=str(env), vault=str(vault))
    cmd_rotate(args)
    captured = capsys.readouterr()
    assert "rotated" in captured.out
