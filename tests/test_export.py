"""Tests for envault.export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import ExportError, export_secrets, _parse_env_lines
from envault.vault import lock

PASSPHRASE = "hunter2"

ENV_CONTENT = """# database creds
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=s3cr3t value with spaces
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


# --- _parse_env_lines ---

def test_parse_skips_comments_and_blanks():
    result = _parse_env_lines("# comment\n\nFOO=bar")
    assert result == {"FOO": "bar"}


def test_parse_handles_equals_in_value():
    result = _parse_env_lines("TOKEN=abc=def")
    assert result == {"TOKEN": "abc=def"}


# --- export_secrets: export format ---

def test_export_format_contains_export_keyword(vault_file: Path):
    output = export_secrets(vault_file, PASSPHRASE, fmt="export")
    assert "export DB_HOST=" in output
    assert "export SECRET_KEY=" in output


def test_export_format_quotes_values_with_spaces(vault_file: Path):
    output = export_secrets(vault_file, PASSPHRASE, fmt="export")
    assert "'s3cr3t value with spaces'" in output or '"s3cr3t value with spaces"' in output


# --- export_secrets: dotenv format ---

def test_dotenv_format_no_export_keyword(vault_file: Path):
    output = export_secrets(vault_file, PASSPHRASE, fmt="dotenv")
    assert "export" not in output
    assert "DB_HOST=localhost" in output


# --- export_secrets: json format ---

def test_json_format_is_valid_json(vault_file: Path):
    output = export_secrets(vault_file, PASSPHRASE, fmt="json")
    data = json.loads(output)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"


# --- error cases ---

def test_wrong_passphrase_raises_export_error(vault_file: Path):
    with pytest.raises(ExportError, match="Failed to decrypt"):
        export_secrets(vault_file, "wrong-pass", fmt="export")


def test_unknown_format_raises_export_error(vault_file: Path):
    with pytest.raises(ExportError, match="Unknown format"):
        export_secrets(vault_file, PASSPHRASE, fmt="xml")  # type: ignore[arg-type]
