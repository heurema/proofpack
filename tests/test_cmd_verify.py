"""Tests for proofpack verify command — full pipeline."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.commands.verify import cmd_verify


def _make_full_proofpack(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "contract.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "run1",
        "work": {"title": "Test", "summary": "Do stuff"},
        "scope": {"allowed_paths": [], "forbidden_paths": []},
        "acceptance": {"commands": [], "artifacts": []},
    }))
    (pp / "meta.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "run1", "receipt_integrity": "full",
        "repo": {"vcs": "git", "head_sha": "abc", "base_sha": "def"},
        "runtime": {"name": "claude-code", "version": "1.0"},
        "env": {"os": "darwin", "ci": False},
    }))
    (pp / "receipts.jsonl").write_text("")


def test_verify_pass(tmp_path: Path, monkeypatch: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _make_full_proofpack(tmp_path)
    result = cmd_verify(mode="fail", json_output=False)
    assert result == 0
    assert (tmp_path / ".proofpack" / "summary.md").exists()
    summary = (tmp_path / ".proofpack" / "summary.md").read_text()
    assert "PASS" in summary


def test_verify_fail_bad_schema(tmp_path: Path, monkeypatch: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "contract.json").write_text("{bad json")
    (pp / "meta.json").write_text("{}")
    (pp / "receipts.jsonl").write_text("")
    result = cmd_verify(mode="fail", json_output=False)
    assert result == 1


def test_verify_json_output(tmp_path: Path, monkeypatch: object, capsys: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _make_full_proofpack(tmp_path)
    result = cmd_verify(mode="fail", json_output=True)
    assert result == 0
    import sys
    out = pytest.CaptureFixture  # type: ignore[attr-defined]
    # Use capsys directly
    captured = capsys  # type: ignore[assignment]
    assert hasattr(captured, "readouterr")
    readouterr = captured.readouterr()  # type: ignore[union-attr]
    data = json.loads(readouterr.out)
    assert data["verdict"] == "PASS"


def test_verify_warn_mode(tmp_path: Path, monkeypatch: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "contract.json").write_text("{bad")
    (pp / "meta.json").write_text("{}")
    (pp / "receipts.jsonl").write_text("")
    result = cmd_verify(mode="warn", json_output=False)
    assert result == 0


def test_verify_no_proofpack_dir_fails(tmp_path: Path, monkeypatch: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    result = cmd_verify(mode="fail", json_output=False)
    assert result == 1


def test_verify_partial_integrity_downgrades_severity(
    tmp_path: Path, monkeypatch: object
) -> None:
    """With receipt_integrity=partial, check 2-4 failures become WARN not FAIL."""
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    # Valid contract with required commands so acceptance check fails
    (pp / "contract.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "run1",
        "work": {"title": "Test", "summary": ""},
        "scope": {"allowed_paths": [], "forbidden_paths": []},
        "acceptance": {"commands": ["pytest"], "artifacts": []},
    }))
    (pp / "meta.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "run1", "receipt_integrity": "partial",
        "repo": {"vcs": "git", "head_sha": "abc", "base_sha": "def"},
        "runtime": {"name": "claude-code", "version": "1.0"},
        "env": {"os": "darwin", "ci": False},
    }))
    # No Bash events recorded, acceptance check would normally FAIL
    (pp / "receipts.jsonl").write_text("")
    result = cmd_verify(mode="fail", json_output=False)
    # With partial mode, FAIL -> WARN so exit code should be 0 in fail mode
    assert result == 0
    summary = (pp / "summary.md").read_text()
    assert "WARN" in summary


def test_verify_json_output_standalone(tmp_path: Path, monkeypatch: object, capsys: object) -> None:
    import pytest
    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _make_full_proofpack(tmp_path)
    result = cmd_verify(mode="fail", json_output=True)
    assert result == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    data = json.loads(out)
    assert data["verdict"] == "PASS"
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) == 5
