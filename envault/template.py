"""Template generation: produce a redacted .env.template from a vault."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.vault import unlock
from envault.crypto import decrypt


class TemplateError(Exception):
    """Raised when template generation fails."""


def _redact_value(value: str) -> str:
    """Return a placeholder string that hints at the value's length."""
    length = len(value)
    if length <= 4:
        return "<secret>"
    return f"<secret:{length}>"


def generate_template(
    vault_file: Path,
    passphrase: str,
    output_file: Optional[Path] = None,
    *,
    include_values: bool = False,
) -> Path:
    """Decrypt *vault_file* and write a redacted template.

    Parameters
    ----------
    vault_file:
        Path to the encrypted ``.env.vault`` file.
    passphrase:
        Master passphrase used to decrypt the vault.
    output_file:
        Destination path.  Defaults to ``<vault_file_stem>.env.template``
        placed next to *vault_file*.
    include_values:
        When *True* the actual values are written (useful for local dev
        bootstrapping).  Defaults to *False*.

    Returns
    -------
    Path
        The path of the written template file.
    """
    vault_path = Path(vault_file)
    if not vault_path.exists():
        raise TemplateError(f"Vault file not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise TemplateError(f"Failed to decrypt vault: {exc}") from exc

    lines: list[str] = []
    for raw_line in plaintext.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            lines.append(raw_line)
            continue
        if "=" not in line:
            lines.append(raw_line)
            continue
        key, _, value = line.partition("=")
        placeholder = value if include_values else _redact_value(value)
        lines.append(f"{key}={placeholder}")

    if output_file is None:
        stem = vault_path.stem  # e.g. ".env" from ".env.vault"
        output_file = vault_path.parent / f"{stem}.template"

    output_path = Path(output_file)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
