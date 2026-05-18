"""Snapshot support: capture a point-in-time copy of a vault file."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = Path(".envault_snapshots")


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(snapshot_dir: Path) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def create_snapshot(
    vault_file: Path | str = Path(".env.vault"),
    snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR,
    label: str | None = None,
) -> Path:
    """Copy *vault_file* into *snapshot_dir* and return the snapshot path.

    The snapshot filename is ``<stem>_<timestamp>[_<label>].vault``.
    Raises :class:`SnapshotError` if *vault_file* does not exist.
    """
    vault_file = Path(vault_file)
    snapshot_dir = Path(snapshot_dir)

    if not vault_file.exists():
        raise SnapshotError(f"Vault file not found: {vault_file}")

    ts = int(time.time())
    stem = vault_file.stem
    suffix = f"_{label}" if label else ""
    dest_name = f"{stem}_{ts}{suffix}.vault"
    dest = _snapshot_dir(snapshot_dir) / dest_name

    shutil.copy2(vault_file, dest)
    return dest


def list_snapshots(
    snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR,
) -> list[Path]:
    """Return snapshot paths sorted oldest-first."""
    snapshot_dir = Path(snapshot_dir)
    if not snapshot_dir.exists():
        return []
    return sorted(snapshot_dir.glob("*.vault"))


def restore_snapshot(
    snapshot: Path | str,
    vault_file: Path | str = Path(".env.vault"),
) -> None:
    """Overwrite *vault_file* with the contents of *snapshot*.

    Raises :class:`SnapshotError` if *snapshot* does not exist.
    """
    snapshot = Path(snapshot)
    vault_file = Path(vault_file)

    if not snapshot.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot}")

    shutil.copy2(snapshot, vault_file)
