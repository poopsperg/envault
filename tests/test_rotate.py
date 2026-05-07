"""Tests for envault.rotate passphrase rotation."""

import pytest
from pathlib import Path

from envault.rotate import rotate, RotationError
from envault.vault import lock, is_locked


ENV_CONTENT = "DB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\n"
OLD_PASS = "old-master-pass"
NEW_PASS = "new-master-pass"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return p


@pytest.fixture()
def vault_file(tmp_path: Path, env_file: Path) -> Path:
    v = tmp_path / ".env.vault"
    lock(env_file, v, OLD_PASS)
    return v


def test_rotate_produces_locked_vault(vault_file, env_file):
    rotate(vault_file, env_file, OLD_PASS, NEW_PASS)
    assert vault_file.exists()
    assert is_locked(vault_file, env_file)


def test_rotate_new_passphrase_decrypts(vault_file, env_file, tmp_path):
    rotate(vault_file, env_file, OLD_PASS, NEW_PASS)
    out = tmp_path / ".env.out"
    from envault.vault import unlock
    unlock(vault_file, out, NEW_PASS)
    assert out.read_text() == ENV_CONTENT


def test_rotate_old_passphrase_no_longer_works(vault_file, env_file, tmp_path):
    rotate(vault_file, env_file, OLD_PASS, NEW_PASS)
    out = tmp_path / ".env.out"
    from envault.vault import unlock
    with pytest.raises(Exception):
        unlock(vault_file, out, OLD_PASS)


def test_rotate_missing_vault_raises(tmp_path, env_file):
    missing = tmp_path / "nonexistent.vault"
    with pytest.raises(RotationError, match="not found"):
        rotate(missing, env_file, OLD_PASS, NEW_PASS)


def test_rotate_wrong_old_passphrase_raises(vault_file, env_file):
    with pytest.raises(RotationError, match="old passphrase"):
        rotate(vault_file, env_file, "wrong-pass", NEW_PASS)


def test_rotate_unlocked_vault_raises(tmp_path, env_file):
    """Rotation should refuse when the .env file already exists (vault unlocked)."""
    vault_file = tmp_path / ".env.vault"
    lock(env_file, vault_file, OLD_PASS)
    # unlock so env_file is present
    from envault.vault import unlock
    unlock(vault_file, env_file, OLD_PASS)
    # Now both files exist -> not locked
    with pytest.raises(RotationError, match="must be locked"):
        rotate(vault_file, env_file, OLD_PASS, NEW_PASS)


def test_rotate_records_audit_event(vault_file, env_file, tmp_path, monkeypatch):
    recorded = []
    monkeypatch.setattr("envault.rotate.record_event", lambda *a, **k: recorded.append(a))
    rotate(vault_file, env_file, OLD_PASS, NEW_PASS)
    assert len(recorded) == 1
    assert recorded[0][0] == "rotate"
