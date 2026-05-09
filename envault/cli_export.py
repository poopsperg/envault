"""CLI wiring for the `envault export` sub-command."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.export import ExportError, export_secrets


def add_export_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "export",
        help="Print decrypted secrets to stdout in a chosen format.",
    )
    p.add_argument(
        "--vault",
        default=".env.vault",
        metavar="FILE",
        help="Encrypted vault file (default: .env.vault)",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["export", "dotenv", "json"],
        default="export",
        help="Output format (default: export)",
    )
    p.set_defaults(func=cmd_export)


def cmd_export(args: argparse.Namespace) -> int:
    vault_file = Path(args.vault)

    if not vault_file.exists():
        print(f"error: vault file not found: {vault_file}", file=sys.stderr)
        return 1

    try:
        passphrase = getpass.getpass("Master passphrase: ")
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.", file=sys.stderr)
        return 1

    try:
        output = export_secrets(vault_file, passphrase, fmt=args.fmt)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0
