"""CLI sub-command: envault diff — show drift between .env and vault."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.diff import DiffError, diff_vault


def add_diff_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("diff", help="Show drift between .env and vault")
    p.add_argument("--env", default=".env", metavar="FILE", help="Path to .env file")
    p.add_argument(
        "--vault", default=".env.vault", metavar="FILE", help="Path to vault file"
    )
    p.set_defaults(func=cmd_diff)


def cmd_diff(args: argparse.Namespace) -> int:
    passphrase = getpass.getpass("Master passphrase: ")

    try:
        result = diff_vault(args.env, args.vault, passphrase)
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.has_drift:
        print("No drift detected — .env matches vault.")
        return 0

    if result.added:
        print("Keys in vault but MISSING from .env:")
        for key in result.added:
            print(f"  + {key}")

    if result.removed:
        print("Keys in .env but MISSING from vault:")
        for key in result.removed:
            print(f"  - {key}")

    if result.changed:
        print("Keys with DIFFERENT values:")
        for key, env_val, vault_val in result.changed:
            print(f"  ~ {key}")
            print(f"      .env  : {env_val!r}")
            print(f"      vault : {vault_val!r}")

    return 1  # non-zero signals drift to callers / CI
