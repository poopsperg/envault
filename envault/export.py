"""Export decrypted secrets to shell-friendly formats."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Literal

from envault.vault import unlock

ExportFormat = Literal["export", "dotenv", "json"]


class ExportError(Exception):
    pass


def _parse_env_lines(plaintext: str) -> dict[str, str]:
    """Parse KEY=VALUE lines, ignoring comments and blanks."""
    result: dict[str, str] = {}
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def export_secrets(
    vault_file: Path,
    passphrase: str,
    fmt: ExportFormat = "export",
) -> str:
    """Decrypt *vault_file* and return secrets rendered in *fmt*.

    Raises ExportError on decryption failure.
    """
    try:
        plaintext = unlock(vault_file, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise ExportError(f"Failed to decrypt vault: {exc}") from exc

    secrets = _parse_env_lines(plaintext)

    if fmt == "export":
        lines = [f"export {k}={shlex.quote(v)}" for k, v in secrets.items()]
        return "\n".join(lines)

    if fmt == "dotenv":
        lines = [f"{k}={v}" for k, v in secrets.items()]
        return "\n".join(lines)

    if fmt == "json":
        import json
        return json.dumps(secrets, indent=2)

    raise ExportError(f"Unknown format: {fmt!r}")
