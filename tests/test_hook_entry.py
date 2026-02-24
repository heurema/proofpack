"""Tests for hook entry point."""
import json
import subprocess
import sys
from pathlib import Path


def _setup_session(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "meta.json").write_text(json.dumps({"run_id": "run1"}))
    (pp / "receipts.jsonl").write_text("")


def test_hook_entry_bash(tmp_path: Path) -> None:
    _setup_session(tmp_path)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "pytest"},
                          "tool_output": "ok", "exit_code": 0})
    result = subprocess.run(
        [sys.executable, "-m", "proofpack.hook_entry", str(tmp_path / ".proofpack")],
        input=payload, capture_output=True, text=True)
    assert result.returncode == 0
    lines = (tmp_path / ".proofpack" / "receipts.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["tool"] == "Bash"


def test_hook_entry_no_proofpack(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack.hook_entry", str(tmp_path / ".proofpack")],
        input="{}", capture_output=True, text=True)
    assert result.returncode == 0  # fail-open


def test_hook_entry_invalid_json(tmp_path: Path) -> None:
    _setup_session(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "proofpack.hook_entry", str(tmp_path / ".proofpack")],
        input="not json", capture_output=True, text=True)
    assert result.returncode == 0  # fail-open
