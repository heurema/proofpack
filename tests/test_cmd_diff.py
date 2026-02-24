"""Tests for proofpack diff command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proofpack.commands.diff import cmd_diff


def test_cmd_diff_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "No proofpack session" in captured.err


def test_cmd_diff_no_meta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "meta.json" in captured.err


def test_cmd_diff_unknown_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

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


def _make_mock_git_run(captured_args: list[list[str]] | None = None):
    """Create a mock subprocess.run that captures args and returns fake git output."""

    def _mock(args: list[str], **kwargs: object) -> object:
        class Result:
            def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
                self.stdout = stdout
                self.stderr = stderr
                self.returncode = returncode

        if captured_args is not None:
            captured_args.append(list(args))
        if args[:2] == ["git", "diff"]:
            return Result(stdout=" file1.py | 10 +++\n 1 file changed\n")
        return Result(returncode=1)

    return _mock


def test_cmd_diff_active_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "active-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc1234", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    captured_args: list[list[str]] = []
    import proofpack.commands.diff as diff_mod
    monkeypatch.setattr(diff_mod.subprocess, "run", _make_mock_git_run(captured_args))

    rc = cmd_diff()
    assert rc == 0
    captured = capsys.readouterr()
    assert "file1.py" in captured.out
    # Active run: should diff base_sha..HEAD
    assert captured_args[0][-1] == "HEAD"
    assert "abc1234" in captured_args[0]


def test_cmd_diff_finalized_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "final-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc1234", "head_sha": "def4567"},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    captured_args: list[list[str]] = []
    import proofpack.commands.diff as diff_mod
    monkeypatch.setattr(diff_mod.subprocess, "run", _make_mock_git_run(captured_args))

    rc = cmd_diff()
    assert rc == 0
    captured = capsys.readouterr()
    assert "file1.py" in captured.out
    # Finalized run: should diff base_sha..head_sha
    assert captured_args[0][-1] == "def4567"
    assert "abc1234" in captured_args[0]


def test_cmd_diff_full_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "full-run",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc1234", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    captured_args: list[list[str]] = []
    import proofpack.commands.diff as diff_mod
    monkeypatch.setattr(diff_mod.subprocess, "run", _make_mock_git_run(captured_args))

    rc = cmd_diff(full=True)
    assert rc == 0
    assert len(captured_args) == 1
    git_cmd = captured_args[0]
    assert "--stat" not in git_cmd
    assert git_cmd[-1] == "HEAD"


def test_cmd_diff_invalid_base_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """SHA validation rejects non-hex strings (e.g. git flag injection)."""
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "bad-sha",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "--malicious", "head_sha": ""},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    rc = cmd_diff()
    assert rc == 1
    captured = capsys.readouterr()
    assert "not a valid hex SHA" in captured.err


def test_cmd_diff_unknown_head_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """head_sha='unknown' is treated as empty (diff against HEAD)."""
    monkeypatch.chdir(tmp_path)

    pp_dir = tmp_path / ".proofpack"
    pp_dir.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": "unknown-head",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "base_sha": "abc1234", "head_sha": "unknown"},
    }
    (pp_dir / "meta.json").write_text(json.dumps(meta))

    captured_args: list[list[str]] = []
    import proofpack.commands.diff as diff_mod
    monkeypatch.setattr(diff_mod.subprocess, "run", _make_mock_git_run(captured_args))

    rc = cmd_diff()
    assert rc == 0
    # unknown head_sha should fall back to HEAD
    assert captured_args[0][-1] == "HEAD"
