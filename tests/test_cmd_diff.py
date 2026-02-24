"""Tests for proofpack diff command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proofpack.commands.diff import cmd_diff


def test_cmd_diff_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "No proofpack session" in captured.err


def test_cmd_diff_no_meta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "meta.json" in captured.err


def test_cmd_diff_unknown_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "test-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "unknown", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "base_sha" in captured.err


def _mock_git_run(args: list[str], **kwargs: object) -> object:
    class Result:
        def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    if args[:2] == ["git", "diff"]:
        return Result(stdout=" file1.py | 10 +++\n 1 file changed\n")
    return Result(returncode=1)


def test_cmd_diff_active_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "active-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc123", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    import proofpack.commands.diff as diff_mod
    mp.setattr(diff_mod.subprocess, "run", _mock_git_run)

    rc = cmd_diff()
    assert rc == 0
    captured = capsys.readouterr()
    assert "file1.py" in captured.out


def test_cmd_diff_finalized_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "final-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc123", "head_sha": "def456"},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    import proofpack.commands.diff as diff_mod
    mp.setattr(diff_mod.subprocess, "run", _mock_git_run)

    rc = cmd_diff()
    assert rc == 0
    captured = capsys.readouterr()
    assert "file1.py" in captured.out


def test_cmd_diff_full_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mp = monkeypatch if isinstance(monkeypatch, pytest.MonkeyPatch) else pytest.MonkeyPatch()
    mp.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "full-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc123", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    captured_args: list[list[str]] = []

    def _mock_full_run(args: list[str], **kwargs: object) -> object:
        class Result:
            def __init__(self) -> None:
                self.stdout = " file1.py | 10 +++\n"
                self.stderr = ""
                self.returncode = 0

        captured_args.append(args)
        return Result()

    import proofpack.commands.diff as diff_mod
    mp.setattr(diff_mod.subprocess, "run", _mock_full_run)

    rc = cmd_diff(full=True)
    assert rc == 0
    assert len(captured_args) == 1
    git_cmd = captured_args[0]
    assert "--stat" not in git_cmd
