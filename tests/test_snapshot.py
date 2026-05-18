"""Tests for envault.snapshot."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / ".env.vault"
    vf.write_text("encrypted-content-abc")
    return vf


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


def test_create_snapshot_returns_path(vault_file, snap_dir):
    result = create_snapshot(vault_file, snap_dir)
    assert result.exists()
    assert result.suffix == ".vault"


def test_create_snapshot_content_matches(vault_file, snap_dir):
    result = create_snapshot(vault_file, snap_dir)
    assert result.read_text() == vault_file.read_text()


def test_create_snapshot_with_label(vault_file, snap_dir):
    result = create_snapshot(vault_file, snap_dir, label="before-rotate")
    assert "before-rotate" in result.name


def test_create_snapshot_missing_vault_raises(tmp_path, snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        create_snapshot(tmp_path / "nonexistent.vault", snap_dir)


def test_create_snapshot_creates_dir(vault_file, snap_dir):
    assert not snap_dir.exists()
    create_snapshot(vault_file, snap_dir)
    assert snap_dir.is_dir()


def test_list_snapshots_empty_when_no_dir(snap_dir):
    assert list_snapshots(snap_dir) == []


def test_list_snapshots_returns_sorted(vault_file, snap_dir):
    s1 = create_snapshot(vault_file, snap_dir, label="first")
    time.sleep(0.01)
    s2 = create_snapshot(vault_file, snap_dir, label="second")
    snaps = list_snapshots(snap_dir)
    assert snaps == sorted(snaps)
    assert len(snaps) == 2


def test_restore_snapshot_overwrites_vault(vault_file, snap_dir, tmp_path):
    snap = create_snapshot(vault_file, snap_dir)
    # mutate vault
    vault_file.write_text("changed-content")
    restore_snapshot(snap, vault_file)
    assert vault_file.read_text() == "encrypted-content-abc"


def test_restore_snapshot_missing_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(Path("/no/such/snapshot.vault"), vault_file)
