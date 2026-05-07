"""Tests for envault.audit module."""

import json
import os
import pytest
from pathlib import Path

from envault import audit


@pytest.fixture()
def log_file(tmp_path):
    return str(tmp_path / "audit_test.json")


def test_record_event_creates_file(log_file):
    audit.record_event("lock", ".env", success=True, log_path=log_file)
    assert Path(log_file).exists()


def test_record_event_structure(log_file):
    entry = audit.record_event("unlock", ".env.vault", success=False, log_path=log_file)
    assert entry["action"] == "unlock"
    assert entry["success"] is False
    assert "timestamp" in entry
    assert "vault_file" in entry


def test_multiple_events_appended(log_file):
    audit.record_event("lock", ".env", success=True, log_path=log_file)
    audit.record_event("unlock", ".env.vault", success=True, log_path=log_file)
    events = audit.get_events(log_path=log_file)
    assert len(events) == 2


def test_get_events_empty_when_no_log(log_file):
    events = audit.get_events(log_path=log_file)
    assert events == []


def test_get_last_event_returns_most_recent(log_file):
    audit.record_event("lock", ".env", success=True, log_path=log_file)
    audit.record_event("unlock", ".env.vault", success=True, log_path=log_file)
    last = audit.get_last_event(log_path=log_file)
    assert last["action"] == "unlock"


def test_get_last_event_filtered_by_vault_file(tmp_path, log_file):
    env_a = str(tmp_path / "a.env")
    env_b = str(tmp_path / "b.env")
    audit.record_event("lock", env_a, success=True, log_path=log_file)
    audit.record_event("lock", env_b, success=True, log_path=log_file)
    last = audit.get_last_event(vault_file=env_a, log_path=log_file)
    assert last["vault_file"] == str(Path(env_a).resolve())


def test_get_last_event_none_when_empty(log_file):
    assert audit.get_last_event(log_path=log_file) is None


def test_clear_log_removes_file(log_file):
    audit.record_event("lock", ".env", success=True, log_path=log_file)
    audit.clear_log(log_path=log_file)
    assert not Path(log_file).exists()


def test_clear_log_noop_when_missing(log_file):
    # Should not raise
    audit.clear_log(log_path=log_file)


def test_corrupt_log_returns_empty(log_file):
    Path(log_file).write_text("not json", encoding="utf-8")
    events = audit.get_events(log_path=log_file)
    assert events == []
