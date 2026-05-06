"""High-level vault operations: lock and unlock .env files."""

import os
from pathlib import Path
from envault.crypto import encrypt, decrypt

ENCRYPTED_SUFFIX = ".vault"


def lock(env_path: str | Path, passphrase: str, remove_original: bool = False) -> Path:
    """Encrypt an .env file and write a .vault file alongside it.

    Returns the path to the encrypted file.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise FileNotFoundError(f"File not found: {env_path}")

    plaintext = env_path.read_text(encoding="utf-8")
    encrypted = encrypt(plaintext, passphrase)

    vault_path = env_path.with_suffix(ENCRYPTED_SUFFIX)
    vault_path.write_text(encrypted, encoding="utf-8")

    if remove_original:
        os.remove(env_path)

    return vault_path


def unlock(vault_path: str | Path, passphrase: str, output_path: str | Path | None = None) -> Path:
    """Decrypt a .vault file and write the plaintext .env file.

    Returns the path to the decrypted file.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    encoded_payload = vault_path.read_text(encoding="utf-8")
    plaintext = decrypt(encoded_payload, passphrase)

    if output_path is None:
        output_path = vault_path.with_suffix(".env")
    else:
        output_path = Path(output_path)

    output_path.write_text(plaintext, encoding="utf-8")
    return output_path


def is_locked(base_path: str | Path) -> bool:
    """Return True if a .vault file exists for the given base path."""
    base_path = Path(base_path)
    vault_path = base_path.with_suffix(ENCRYPTED_SUFFIX)
    return vault_path.exists()
