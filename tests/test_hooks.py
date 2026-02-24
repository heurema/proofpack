"""Tests for receipt writing from hook events."""
import json
from pathlib import Path

from proofpack.hooks import append_receipt


def test_append_receipt_bash(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "receipts.jsonl").write_text("")
    (pp / "meta.json").write_text(json.dumps({"run_id": "run1"}))
    append_receipt(pp_dir=pp, tool="Bash", event="tool", exit_code=0,
                   input_data="pytest -q", stdout_data="3 passed", stderr_data="")
    lines = (pp / "receipts.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    d = json.loads(lines[0])
    assert d["run_id"] == "run1"
    assert d["tool"] == "Bash"
    assert d["exit_code"] == 0
    assert len(d["input_sha256"]) == 64


def test_append_receipt_edit(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "receipts.jsonl").write_text("")
    (pp / "meta.json").write_text(json.dumps({"run_id": "run1"}))
    append_receipt(pp_dir=pp, tool="Edit", event="edit", path="src/foo.py",
                   before_content="old", after_content="new")
    d = json.loads((pp / "receipts.jsonl").read_text().strip())
    assert d["event"] == "edit"
    assert d["path"] == "src/foo.py"
    assert d["before_sha256"] != d["after_sha256"]


def test_append_multiple(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "receipts.jsonl").write_text("")
    (pp / "meta.json").write_text(json.dumps({"run_id": "run1"}))
    for i in range(3):
        append_receipt(pp_dir=pp, tool="Bash", event="tool", exit_code=i)
    lines = (pp / "receipts.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3
