"""Tests for proofpack init command."""
import json
from pathlib import Path

from proofpack.commands.init import cmd_init


def test_init_creates_proofpack_dir(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    result = cmd_init(title="Test task", scope="src/**,tests/**")
    assert result == 0
    pp = tmp_path / ".proofpack"
    assert pp.is_dir()
    contract = json.loads((pp / "contract.json").read_text())
    assert contract["schema_version"] == 1
    assert contract["work"]["title"] == "Test task"
    assert contract["scope"]["allowed_paths"] == ["src/**", "tests/**"]


def test_init_default_empty(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    result = cmd_init(title="", scope="")
    assert result == 0
    contract = json.loads((tmp_path / ".proofpack" / "contract.json").read_text())
    assert contract["work"]["title"] == ""
    assert contract["scope"]["allowed_paths"] == []


def test_init_already_exists(tmp_path: Path, monkeypatch: object) -> None:
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)
    (tmp_path / ".proofpack").mkdir()
    result = cmd_init(title="X", scope="")
    assert result == 1
