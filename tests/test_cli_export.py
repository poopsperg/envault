"""Tests for the export CLI sub-command."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_export import add_export_parser, cmd_export
from envault.vault import lock

PASSPHRASE = "correct-horse"
ENV_CONTENT = "API_KEY=abc123\nDEBUG=true\n"


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_export_parser(sub)
    return parser


def _args(arg_str: str) -> argparse.Namespace:
    return _make_parser().parse_args(arg_str.split())


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


# --- parser ---

def test_parser_export_default_format():
    ns = _args("export")
    assert ns.fmt == "export"
    assert ns.vault == ".env.vault"


def test_parser_export_json_format():
    ns = _args("export --format json")
    assert ns.fmt == "json"


def test_parser_export_custom_vault():
    ns = _args("export --vault secrets.vault")
    assert ns.vault == "secrets.vault"


# --- cmd_export ---

def test_cmd_export_missing_vault(tmp_path: Path, capsys):
    ns = argparse.Namespace(vault=str(tmp_path / "missing.vault"), fmt="export")
    rc = cmd_export(ns)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_cmd_export_success(vault_file: Path, capsys):
    ns = argparse.Namespace(vault=str(vault_file), fmt="export")
    with patch("envault.cli_export.getpass.getpass", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "export API_KEY=" in out


def test_cmd_export_json_format(vault_file: Path, capsys):
    ns = argparse.Namespace(vault=str(vault_file), fmt="json")
    with patch("envault.cli_export.getpass.getpass", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert data["API_KEY"] == "abc123"


def test_cmd_export_wrong_passphrase(vault_file: Path, capsys):
    ns = argparse.Namespace(vault=str(vault_file), fmt="export")
    with patch("envault.cli_export.getpass.getpass", return_value="wrong"):
        rc = cmd_export(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err
