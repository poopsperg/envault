"""CLI sub-command: envault template — generate a redacted .env template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.template import TemplateError, generate_template


def add_template_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the ``template`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "template",
        help="Generate a redacted .env template from a vault",
    )
    p.add_argument(
        "--vault",
        default=".env.vault",
        metavar="FILE",
        help="Encrypted vault file (default: .env.vault)",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Output template path (default: <vault>.template)",
    )
    p.add_argument(
        "--passphrase",
        required=True,
        metavar="PASS",
        help="Master passphrase to decrypt the vault",
    )
    p.add_argument(
        "--include-values",
        action="store_true",
        default=False,
        help="Write actual values instead of placeholders",
    )
    p.set_defaults(func=cmd_template)


def cmd_template(args: argparse.Namespace) -> int:
    """Handle the ``template`` sub-command.  Returns an exit code."""
    output = Path(args.output) if args.output else None
    try:
        dest = generate_template(
            vault_file=Path(args.vault),
            passphrase=args.passphrase,
            output_file=output,
            include_values=args.include_values,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Template written to {dest}")
    return 0
