"""Compare a decrypted vault against the current .env file to show drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from envault.export import _parse_env_lines
from envault.vault import unlock


class DiffError(Exception):
    """Raised when the diff operation cannot be completed."""


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)      # keys in vault, missing from .env
    removed: List[str] = field(default_factory=list)    # keys in .env, missing from vault
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, env_val, vault_val)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_vault(
    env_path: str,
    vault_path: str,
    passphrase: str,
) -> DiffResult:
    """Return a DiffResult comparing *env_path* against the locked *vault_path*."""
    try:
        with open(env_path, "r") as fh:
            env_lines = fh.readlines()
    except FileNotFoundError:
        raise DiffError(f".env file not found: {env_path}")

    try:
        vault_plaintext = unlock(vault_path, passphrase)
    except FileNotFoundError:
        raise DiffError(f"Vault file not found: {vault_path}")
    except Exception as exc:
        raise DiffError(f"Could not unlock vault: {exc}") from exc

    env_pairs = _parse_env_lines(env_lines)
    vault_pairs = _parse_env_lines(vault_plaintext.splitlines(keepends=True))

    env_map = dict(env_pairs)
    vault_map = dict(vault_pairs)

    result = DiffResult()
    all_keys = set(env_map) | set(vault_map)

    for key in sorted(all_keys):
        in_env = key in env_map
        in_vault = key in vault_map
        if in_vault and not in_env:
            result.added.append(key)
        elif in_env and not in_vault:
            result.removed.append(key)
        elif env_map[key] != vault_map[key]:
            result.changed.append((key, env_map[key], vault_map[key]))
        else:
            result.unchanged.append(key)

    return result
