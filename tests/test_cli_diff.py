"""Tests for envault.cli_diff."""

from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from envault.cli_diff import add_diff_parser, cmd_diff
from envault.vault import lock


PASSPHRASE = "s3cret"


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_diff_parser(sub)
    return parser


def _args(argv):
    return _make_parser().parse_args(argv)


@pytest.fixture()
def vault_file(tmp_path):
    def _make(env_text: str, vault_name: str = "test.vault") -> tuple[str, str]:
        env = tmp_path / ".env"
        env.write_text(env_text)
        vault = tmp_path / vault_name
        lock(str(env), str(vault), PASSPHRASE)
        return str(env), str(vault)

    return _make


def test_parser_diff_defaults():
    args = _args(["diff"])
    assert args.env == ".env"
    assert args.vault == ".env.vault"
    assert args.func is cmd_diff


def test_parser_diff_custom_paths():
    args = _args(["diff", "--env", "prod.env", "--vault", "prod.vault"])
    assert args.env == "prod.env"
    assert args.vault == "prod.vault"


def test_cmd_diff_no_drift(vault_file, capsys):
    content = "KEY=value\n"
    env, vault = vault_file(content)
    args = _args(["diff", "--env", env, "--vault", vault])
    with patch("envault.cli_diff.getpass.getpass", return_value=PASSPHRASE):
        rc = cmd_diff(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No drift" in captured.out


def test_cmd_diff_with_drift(vault_file, capsys):
    env, vault = vault_file("KEY=old\n")
    # overwrite .env with different value
    with open(env, "w") as fh:
        fh.write("KEY=new\n")
    args = _args(["diff", "--env", env, "--vault", vault])
    with patch("envault.cli_diff.getpass.getpass", return_value=PASSPHRASE):
        rc = cmd_diff(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "KEY" in captured.out


def test_cmd_diff_bad_passphrase_returns_1(vault_file, capsys):
    env, vault = vault_file("KEY=value\n")
    args = _args(["diff", "--env", env, "--vault", vault])
    with patch("envault.cli_diff.getpass.getpass", return_value="badpass"):
        rc = cmd_diff(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err
