"""Tests for envault.template and envault.cli_template."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.vault import lock
from envault.template import TemplateError, generate_template
from envault.cli_template import add_template_parser, cmd_template

PASSPHRASE = "hunter2"
ENV_CONTENT = "# comment\nDB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\nDEBUG=true\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT, encoding="utf-8")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_template_parser(sub)
    return p


def _args(parser: argparse.ArgumentParser, *argv: str) -> argparse.Namespace:
    return parser.parse_args(argv)


# --- generate_template unit tests ---

def test_generate_template_creates_file(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.template"
    path = generate_template(vault_file, PASSPHRASE, output_file=out)
    assert path == out
    assert out.exists()


def test_generate_template_redacts_values(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.template"
    generate_template(vault_file, PASSPHRASE, output_file=out)
    content = out.read_text(encoding="utf-8")
    assert "postgres://localhost/mydb" not in content
    assert "supersecret" not in content
    assert "<secret" in content


def test_generate_template_preserves_keys(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.template"
    generate_template(vault_file, PASSPHRASE, output_file=out)
    content = out.read_text(encoding="utf-8")
    assert "DB_URL=" in content
    assert "SECRET_KEY=" in content
    assert "DEBUG=" in content


def test_generate_template_preserves_comments(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.template"
    generate_template(vault_file, PASSPHRASE, output_file=out)
    content = out.read_text(encoding="utf-8")
    assert "# comment" in content


def test_generate_template_include_values(vault_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.template"
    generate_template(vault_file, PASSPHRASE, output_file=out, include_values=True)
    content = out.read_text(encoding="utf-8")
    assert "postgres://localhost/mydb" in content


def test_generate_template_default_output_path(vault_file: Path) -> None:
    path = generate_template(vault_file, PASSPHRASE)
    assert path.name == ".env.template"
    assert path.parent == vault_file.parent


def test_generate_template_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(TemplateError, match="not found"):
        generate_template(tmp_path / "ghost.vault", PASSPHRASE)


def test_generate_template_wrong_passphrase(vault_file: Path) -> None:
    with pytest.raises(TemplateError, match="Failed to decrypt"):
        generate_template(vault_file, "wrongpass")


# --- CLI tests ---

def test_parser_template_defaults(vault_file: Path) -> None:
    p = _make_parser()
    ns = _args(p, "template", "--passphrase", "x")
    assert ns.vault == ".env.vault"
    assert ns.output is None
    assert ns.include_values is False


def test_cmd_template_success(vault_file: Path, tmp_path: Path) -> None:
    p = _make_parser()
    out = tmp_path / "out.template"
    ns = _args(p, "template", "--vault", str(vault_file), "--passphrase", PASSPHRASE, "--output", str(out))
    rc = cmd_template(ns)
    assert rc == 0
    assert out.exists()


def test_cmd_template_missing_vault_returns_1(tmp_path: Path) -> None:
    p = _make_parser()
    ns = _args(p, "template", "--vault", str(tmp_path / "nope.vault"), "--passphrase", PASSPHRASE)
    rc = cmd_template(ns)
    assert rc == 1
