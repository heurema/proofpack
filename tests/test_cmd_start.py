"""Tests for proofpack start command."""
import json
from pathlib import Path

from proofpack.commands.start import cmd_start


def _setup_proofpack(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    contract = {
        "schema_version": 1,
        "run_id": "",
        "work": {"title": "T", "summary": "S"},
        "scope": {"allowed_paths": [], "forbidden_paths": []},
        "acceptance": {"commands": [], "artifacts": []},
    }
    (pp / "contract.json").write_text(json.dumps(contract))


def test_start_creates_meta_and_receipts(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _setup_proofpack(tmp_path)
    result = cmd_start(run_id="test-run-1")
    assert result == 0
    pp = tmp_path / ".proofpack"
    assert (pp / "meta.json").exists()
    assert (pp / "receipts.jsonl").exists()
    meta = json.loads((pp / "meta.json").read_text())
    assert meta["run_id"] == "test-run-1"
    assert meta["receipt_integrity"] == "full"
    contract = json.loads((pp / "contract.json").read_text())
    assert contract["run_id"] == "test-run-1"


def test_start_auto_run_id(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _setup_proofpack(tmp_path)
    result = cmd_start(run_id="")
    assert result == 0
    meta = json.loads((tmp_path / ".proofpack" / "meta.json").read_text())
    assert meta["run_id"] != ""


def test_start_no_proofpack_dir(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    result = cmd_start(run_id="x")
    assert result == 1


def test_start_warns_on_existing_session(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    """I3: start should warn when meta.json already exists."""
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    _setup_proofpack(tmp_path)
    # First start
    cmd_start(run_id="run1")
    # Second start should warn but succeed
    result = cmd_start(run_id="run2")
    assert result == 0
    captured = capsys.readouterr()  # type: ignore[union-attr]
    assert "already active" in captured.err
    meta = json.loads((tmp_path / ".proofpack" / "meta.json").read_text())
    assert meta["run_id"] == "run2"
