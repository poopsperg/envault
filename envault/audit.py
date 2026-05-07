"""Audit log for vault operations — tracks lock/unlock events with timestamps."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_AUDIT_LOG = ".envault_audit.json"


def _load_log(log_path: str) -> list:
    """Load existing audit log entries or return empty list."""
    path = Path(log_path)
    if not path.exists():
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_log(entries: list, log_path: str) -> None:
    """Persist audit log entries to disk."""
    with open(log_path, "w") as f:
        json.dump(entries, f, indent=2)


def record_event(action: str, vault_file: str, success: bool, log_path: str = DEFAULT_AUDIT_LOG) -> dict:
    """Record a vault action event and return the entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "vault_file": str(Path(vault_file).resolve()),
        "success": success,
    }
    entries = _load_log(log_path)
    entries.append(entry)
    _save_log(entries, log_path)
    return entry


def get_events(log_path: str = DEFAULT_AUDIT_LOG) -> list:
    """Return all recorded audit events."""
    return _load_log(log_path)


def get_last_event(vault_file: str = None, log_path: str = DEFAULT_AUDIT_LOG) -> dict | None:
    """Return the most recent event, optionally filtered by vault file."""
    events = _load_log(log_path)
    if vault_file:
        resolved = str(Path(vault_file).resolve())
        events = [e for e in events if e.get("vault_file") == resolved]
    return events[-1] if events else None


def clear_log(log_path: str = DEFAULT_AUDIT_LOG) -> None:
    """Wipe the audit log."""
    path = Path(log_path)
    if path.exists():
        os.remove(path)
