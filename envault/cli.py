"""Command-line interface for envault."""

import sys
import getpass
import argparse
from pathlib import Path

from envault.vault import lock, unlock, is_locked


def cmd_lock(args: argparse.Namespace) -> int:
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"error: '{env_path}' not found", file=sys.stderr)
        return 1

    if is_locked(env_path):
        print(f"'{env_path}' is already locked")
        return 0

    passphrase = getpass.getpass("Master passphrase: ")
    confirm = getpass.getpass("Confirm passphrase: ")
    if passphrase != confirm:
        print("error: passphrases do not match", file=sys.stderr)
        return 1

    vault_path = lock(env_path, passphrase)
    print(f"Locked → {vault_path}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    vault_path = Path(args.file)
    if not vault_path.exists():
        print(f"error: '{vault_path}' not found", file=sys.stderr)
        return 1

    if not is_locked(vault_path):
        print(f"'{vault_path}' does not appear to be a locked vault", file=sys.stderr)
        return 1

    passphrase = getpass.getpass("Master passphrase: ")
    try:
        env_path = unlock(vault_path, passphrase)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Unlocked → {env_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: '{path}' not found", file=sys.stderr)
        return 1
    state = "locked" if is_locked(path) else "unlocked"
    print(f"{path}: {state}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Lightweight local secrets manager for .env files",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd in ("lock", "unlock", "status"):
        p = sub.add_parser(cmd, help=f"{cmd} a vault file")
        p.add_argument(
            "file",
            nargs="?",
            default=".env" if cmd != "unlock" else ".env.vault",
            help="path to the file (default: .env / .env.vault)",
        )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {"lock": cmd_lock, "unlock": cmd_unlock, "status": cmd_status}
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
