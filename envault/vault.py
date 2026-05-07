"""Vault operations: lock (encrypt) and unlock (decrypt) .env files."""

import os
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault import audit

LOCKED_SUFFIX = ".vault"


def lock(env_file: str, passphrase: str, log_path: str = audit.DEFAULT_AUDIT_LOG) -> str:
    """Encrypt *env_file* and write <env_file>.vault. Returns vault path."""
    env_path = Path(env_file)
    if not env_path.exists():
        audit.record_event("lock", env_file, success=False, log_path=log_path)
        raise FileNotFoundError(f"{env_file} not found")

    plaintext = env_path.read_text(encoding="utf-8")
    token = encrypt(plaintext, passphrase)

    vault_path = env_path.with_suffix(env_path.suffix + LOCKED_SUFFIX)
    vault_path.write_text(token, encoding="utf-8")

    audit.record_event("lock", env_file, success=True, log_path=log_path)
    return str(vault_path)


def unlock(vault_file: str, passphrase: str, log_path: str = audit.DEFAULT_AUDIT_LOG) -> str:
    """Decrypt *vault_file* and write the original .env. Returns env path."""
    vault_path = Path(vault_file)
    if not vault_path.exists():
        audit.record_event("unlock", vault_file, success=False, log_path=log_path)
        raise FileNotFoundError(f"{vault_file} not found")

    token = vault_path.read_text(encoding="utf-8")
    try:
        plaintext = decrypt(token, passphrase)
    except Exception:
        audit.record_event("unlock", vault_file, success=False, log_path=log_path)
        raise

    # Strip .vault suffix to recover original name
    env_path = Path(str(vault_path).removesuffix(LOCKED_SUFFIX))
    env_path.write_text(plaintext, encoding="utf-8")

    audit.record_event("unlock", vault_file, success=True, log_path=log_path)
    return str(env_path)


def is_locked(env_file: str) -> bool:
    """Return True when the .vault counterpart exists (and .env may be absent)."""
    vault_path = Path(env_file).with_suffix(
        Path(env_file).suffix + LOCKED_SUFFIX
    )
    return vault_path.exists()
