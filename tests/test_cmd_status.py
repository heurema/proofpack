"""Tests for proofpack status command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proofpack.commands.status import cmd_status


def test_cmd_status_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    rc = cmd_status()
    assert rc == 0
    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "No proofpack session found" in captured.out


def test_cmd_status_initialized_no_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    contract = {
        "schema_version": 1,
        "work": {"title": "Test Work", "summary": ""},
        "scope": {"allowed_paths": ["src/"], "forbidden_paths": []},
    }
    (pp_dir / "contract.json").write_text(json.dumps(contract))

    rc = cmd_status()
    assert rc == 0
    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "initialized" in captured.out
    assert "Test Work" in captured.out
    assert "src/" in captured.out


def test_cmd_status_active_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    contract = {
        "schema_version": 1,
        "work": {"title": "Active Work", "summary": ""},
        "scope": {"allowed_paths": [], "forbidden_paths": []},
    }
    (pp_dir / "contract.json").write_text(json.dumps(contract))

    meta = {
        "schema_version": 1,
        "run_id": "test-run-001",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc123", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    rc = cmd_status()
    assert rc == 0
    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "active" in captured.out
    assert "test-run-001" in captured.out


def test_cmd_status_finalized_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    (pp_dir / "contract.json").write_text(json.dumps({
        "schema_version": 1,
        "work": {"title": "", "summary": ""},
        "scope": {"allowed_paths": [], "forbidden_paths": []},
    }))

    meta = {
        "schema_version": 1,
        "run_id": "final-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc", "head_sha": "def456"},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    rc = cmd_status()
    assert rc == 0
    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "finalized" in captured.out
    assert "final-run" in captured.out
    assert "def456" in captured.out
