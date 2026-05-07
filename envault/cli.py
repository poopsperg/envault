"""CLI entry-point for envault."""

import argparse
import sys
from pathlib import Path

from envault.vault import lock, unlock, is_locked
from envault.audit import get_events
from envault.rotate import rotate, RotationError

DEFAULT_ENV = ".env"
DEFAULT_VAULT = ".env.vault"


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_lock(args: argparse.Namespace) -> int:
    env = Path(args.env)
    vault = Path(args.vault)
    if not env.exists():
        print(f"error: env file not found: {env}", file=sys.stderr)
        return 1
    lock(env, vault, args.passphrase)
    print(f"Locked {env} -> {vault}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    env = Path(args.env)
    if not vault.exists():
        print(f"error: vault file not found: {vault}", file=sys.stderr)
        return 1
    unlock(vault, env, args.passphrase)
    print(f"Unlocked {vault} -> {env}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    env = Path(args.env)
    locked = is_locked(vault, env)
    print("locked" if locked else "unlocked")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    events = get_events()
    if not events:
        print("No audit events recorded.")
        return 0
    for ev in events[-args.tail:]:
        print(f"[{ev['timestamp']}] {ev['action']} {ev.get('details', '')}")
    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    env = Path(args.env)
    try:
        rotate(vault, env, args.old_passphrase, args.new_passphrase)
        print(f"Passphrase rotated for {vault}")
        return 0
    except RotationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault", description="Local secrets manager")
    sub = parser.add_subparsers(dest="command")

    def _add_paths(p: argparse.ArgumentParser) -> None:
        p.add_argument("--env", default=DEFAULT_ENV)
        p.add_argument("--vault", default=DEFAULT_VAULT)

    # lock
    p_lock = sub.add_parser("lock")
    _add_paths(p_lock)
    p_lock.add_argument("passphrase")
    p_lock.set_defaults(func=cmd_lock)

    # unlock
    p_unlock = sub.add_parser("unlock")
    _add_paths(p_unlock)
    p_unlock.add_argument("passphrase")
    p_unlock.set_defaults(func=cmd_unlock)

    # status
    p_status = sub.add_parser("status")
    _add_paths(p_status)
    p_status.set_defaults(func=cmd_status)

    # audit
    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--tail", type=int, default=20)
    p_audit.set_defaults(func=cmd_audit)

    # rotate
    p_rotate = sub.add_parser("rotate")
    _add_paths(p_rotate)
    p_rotate.add_argument("old_passphrase")
    p_rotate.add_argument("new_passphrase")
    p_rotate.set_defaults(func=cmd_rotate)

    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
