"""Tests for envault.diff."""

from __future__ import annotations

import pytest

from envault.diff import DiffError, DiffResult, diff_vault
from envault.vault import lock


PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path):
    """Return a factory that writes a vault from given plaintext."""
    def _make(plaintext: str) -> str:
        env_src = tmp_path / "src.env"
        vault = tmp_path / "src.env.vault"
        env_src.write_text(plaintext)
        lock(str(env_src), str(vault), PASSPHRASE)
        return str(vault)

    return _make


def test_identical_env_and_vault(tmp_path, vault_file):
    content = "DB_HOST=localhost\nDB_PORT=5432\n"
    env = tmp_path / ".env"
    env.write_text(content)
    vault = vault_file(content)

    result = diff_vault(str(env), vault, PASSPHRASE)
    assert not result.has_drift
    assert set(result.unchanged) == {"DB_HOST", "DB_PORT"}


def test_key_added_in_vault(tmp_path, vault_file):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\n")
    vault = vault_file("DB_HOST=localhost\nSECRET_KEY=abc\n")

    result = diff_vault(str(env), vault, PASSPHRASE)
    assert result.has_drift
    assert "SECRET_KEY" in result.added


def test_key_removed_from_vault(tmp_path, vault_file):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nOLD_KEY=old\n")
    vault = vault_file("DB_HOST=localhost\n")

    result = diff_vault(str(env), vault, PASSPHRASE)
    assert "OLD_KEY" in result.removed


def test_value_changed(tmp_path, vault_file):
    env = tmp_path / ".env"
    env.write_text("API_URL=http://old.example.com\n")
    vault = vault_file("API_URL=http://new.example.com\n")

    result = diff_vault(str(env), vault, PASSPHRASE)
    assert result.has_drift
    assert result.changed[0][0] == "API_URL"
    assert result.changed[0][1] == "http://old.example.com"
    assert result.changed[0][2] == "http://new.example.com"


def test_missing_env_file_raises(tmp_path, vault_file):
    vault = vault_file("KEY=val\n")
    with pytest.raises(DiffError, match=".env file not found"):
        diff_vault(str(tmp_path / "nonexistent.env"), vault, PASSPHRASE)


def test_missing_vault_file_raises(tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=val\n")
    with pytest.raises(DiffError, match="Vault file not found"):
        diff_vault(str(env), str(tmp_path / "missing.vault"), PASSPHRASE)


def test_wrong_passphrase_raises(tmp_path, vault_file):
    env = tmp_path / ".env"
    env.write_text("KEY=val\n")
    vault = vault_file("KEY=val\n")
    with pytest.raises(DiffError, match="Could not unlock vault"):
        diff_vault(str(env), vault, "wrongpassphrase")
