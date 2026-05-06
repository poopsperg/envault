"""Tests for envault crypto and vault modules."""

import pytest
from pathlib import Path
from envault.crypto import encrypt, decrypt
from envault.vault import lock, unlock, is_locked


SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"
PASSPHRASE = "my-strong-passphrase"
WRONG_PASSPHRASE = "wrong-passphrase"


# --- crypto tests ---

def test_encrypt_returns_string():
    token = encrypt(SAMPLE_ENV, PASSPHRASE)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_produces_different_ciphertexts():
    token1 = encrypt(SAMPLE_ENV, PASSPHRASE)
    token2 = encrypt(SAMPLE_ENV, PASSPHRASE)
    assert token1 != token2  # random salt/nonce each time


def test_decrypt_roundtrip():
    token = encrypt(SAMPLE_ENV, PASSPHRASE)
    result = decrypt(token, PASSPHRASE)
    assert result == SAMPLE_ENV


def test_decrypt_wrong_passphrase_raises():
    token = encrypt(SAMPLE_ENV, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, WRONG_PASSPHRASE)


def test_decrypt_bad_payload_raises():
    with pytest.raises(ValueError):
        decrypt("not-valid-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSPHRASE)


# --- vault tests ---

def test_lock_creates_vault_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")

    vault_file = lock(env_file, PASSPHRASE)

    assert vault_file.exists()
    assert vault_file.suffix == ".vault"


def test_lock_unlock_roundtrip(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")

    vault_file = lock(env_file, PASSPHRASE)
    recovered = unlock(vault_file, PASSPHRASE, output_path=tmp_path / ".env.out")

    assert recovered.read_text(encoding="utf-8") == SAMPLE_ENV


def test_lock_remove_original(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")

    lock(env_file, PASSPHRASE, remove_original=True)

    assert not env_file.exists()


def test_lock_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        lock(tmp_path / "nonexistent.env", PASSPHRASE)


def test_unlock_wrong_passphrase_raises(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")
    vault_file = lock(env_file, PASSPHRASE)

    with pytest.raises(ValueError):
        unlock(vault_file, WRONG_PASSPHRASE)


def test_is_locked(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")

    assert not is_locked(env_file)
    lock(env_file, PASSPHRASE)
    assert is_locked(env_file)
