"""Passphrase rotation: re-encrypt vault with a new master passphrase."""

from pathlib import Path

from envault.vault import lock, unlock, is_locked
from envault.audit import record_event


class RotationError(Exception):
    pass


def rotate(
    vault_path: str | Path,
    env_path: str | Path,
    old_passphrase: str,
    new_passphrase: str,
) -> None:
    """Decrypt vault with old passphrase then re-encrypt with new passphrase.

    Args:
        vault_path: Path to the encrypted .vault file.
        env_path:   Path where the plaintext .env is written temporarily.
        old_passphrase: Current master passphrase.
        new_passphrase: Replacement master passphrase.

    Raises:
        RotationError: If the vault is not locked, or decryption fails.
    """
    vault_path = Path(vault_path)
    env_path = Path(env_path)

    if not vault_path.exists():
        raise RotationError(f"Vault file not found: {vault_path}")

    if not is_locked(vault_path, env_path):
        raise RotationError(
            "Vault must be locked before rotation. Run 'envault lock' first."
        )

    # Step 1: decrypt with old passphrase -> writes env_path
    try:
        unlock(vault_path, env_path, old_passphrase)
    except Exception as exc:
        raise RotationError(f"Failed to decrypt vault with old passphrase: {exc}") from exc

    # Step 2: re-encrypt with new passphrase -> overwrites vault_path
    try:
        lock(env_path, vault_path, new_passphrase)
    except Exception as exc:
        raise RotationError(f"Failed to re-encrypt vault with new passphrase: {exc}") from exc

    record_event(
        "rotate",
        {"vault": str(vault_path), "env": str(env_path)},
    )
