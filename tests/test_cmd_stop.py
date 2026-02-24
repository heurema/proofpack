"""Tests for proofpack stop command."""
import json
from pathlib import Path

from proofpack.commands.stop import cmd_stop


def _setup_session(tmp_path: Path, run_id: str = "run1") -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    meta = {
        "schema_version": 1,
        "run_id": run_id,
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "head_sha": "", "base_sha": "aaa"},
        "runtime": {"name": "claude-code", "version": "1.0"},
        "env": {"os": "darwin", "ci": False},
    }
    (pp / "meta.json").write_text(json.dumps(meta))
    (pp / "receipts.jsonl").write_text("")
    (pp / "contract.json").write_text(json.dumps({"schema_version": 1, "run_id": run_id}))


def test_stop_finalizes_meta(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _setup_session(tmp_path)
    result = cmd_stop()
    assert result == 0
    meta = json.loads((tmp_path / ".proofpack" / "meta.json").read_text())
    assert meta["repo"]["head_sha"] != ""


def test_stop_no_meta(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    result = cmd_stop()
    assert result == 1
