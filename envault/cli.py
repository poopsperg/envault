"""CLI entry-point for envault."""

import argparse
import getpass
import sys

from envault import vault, audit

DEFAULT_ENV = ".env"
DEFAULT_VAULT = ".env.vault"


def cmd_lock(args) -> int:
    passphrase = getpass.getpass("Master passphrase: ")
    try:
        out = vault.lock(args.file, passphrase, log_path=args.audit_log)
        print(f"Locked → {out}")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_unlock(args) -> int:
    passphrase = getpass.getpass("Master passphrase: ")
    try:
        out = vault.unlock(args.file, passphrase, log_path=args.audit_log)
        print(f"Unlocked → {out}")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("Error: decryption failed — wrong passphrase or corrupt vault.", file=sys.stderr)
        return 1


def cmd_status(args) -> int:
    locked = vault.is_locked(args.file)
    state = "locked" if locked else "unlocked"
    print(f"{args.file}: {state}")
    return 0


def cmd_audit(args) -> int:
    events = audit.get_events(log_path=args.audit_log)
    if not events:
        print("No audit events recorded.")
        return 0
    for e in events[-args.tail:]:
        status = "OK" if e["success"] else "FAIL"
        print(f"[{e['timestamp']}] {e['action'].upper():6s} {status}  {e['vault_file']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault", description="Lightweight local secrets manager")
    parser.add_argument("--audit-log", default=audit.DEFAULT_AUDIT_LOG, metavar="FILE",
                        help="path to audit log (default: %(default)s)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="encrypt .env → .env.vault")
    p_lock.add_argument("file", nargs="?", default=DEFAULT_ENV)
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = sub.add_parser("unlock", help="decrypt .env.vault → .env")
    p_unlock.add_argument("file", nargs="?", default=DEFAULT_VAULT)
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = sub.add_parser("status", help="show lock state")
    p_status.add_argument("file", nargs="?", default=DEFAULT_ENV)
    p_status.set_defaults(func=cmd_status)

    p_audit = sub.add_parser("audit", help="show recent audit events")
    p_audit.add_argument("--tail", type=int, default=20, metavar="N",
                         help="show last N events (default: %(default)s)")
    p_audit.set_defaults(func=cmd_audit)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
