"""Tests for check 1: schema validation."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks.schema_check import check_schema


def _make_valid_pp(tmp_path: Path) -> Path:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    (pp / "contract.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run1",
                "work": {"title": "Test", "summary": "Do stuff"},
                "scope": {"allowed_paths": [], "forbidden_paths": []},
                "acceptance": {"commands": [], "artifacts": []},
            }
        )
    )
    (pp / "meta.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run1",
                "receipt_integrity": "full",
                "repo": {"vcs": "git", "head_sha": "abc", "base_sha": "def"},
                "runtime": {"name": "claude-code", "version": "1.0"},
                "env": {"os": "darwin", "ci": False},
            }
        )
    )
    (pp / "receipts.jsonl").write_text("")
    return pp


def test_valid_schema_passes(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    result = check_schema(pp)
    assert result.passed is True
    assert "0 receipt event" in result.message


def test_valid_schema_with_events_passes(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    event = json.dumps(
        {"run_id": "run1", "t": "2024-01-01T00:00:00Z", "event": "tool_use", "tool": "Bash"}
    )
    (pp / "receipts.jsonl").write_text(event + "\n")
    result = check_schema(pp)
    assert result.passed is True
    assert "1 receipt event" in result.message


def test_missing_contract_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "contract.json").unlink()
    result = check_schema(pp)
    assert result.passed is False
    assert "contract.json" in result.message


def test_missing_meta_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "meta.json").unlink()
    result = check_schema(pp)
    assert result.passed is False
    assert "meta.json" in result.message


def test_missing_receipts_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "receipts.jsonl").unlink()
    result = check_schema(pp)
    assert result.passed is False
    assert "receipts.jsonl" in result.message


def test_invalid_contract_json_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "contract.json").write_text("{bad json")
    result = check_schema(pp)
    assert result.passed is False
    assert "invalid JSON" in result.message


def test_invalid_meta_json_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "meta.json").write_text("{bad json")
    result = check_schema(pp)
    assert result.passed is False
    assert "invalid JSON" in result.message


def test_contract_missing_required_field_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    # Missing "work" key
    (pp / "contract.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run1",
                "scope": {"allowed_paths": [], "forbidden_paths": []},
                "acceptance": {"commands": [], "artifacts": []},
            }
        )
    )
    result = check_schema(pp)
    assert result.passed is False
    assert "missing required field" in result.message


def test_receipts_invalid_json_line_fails(tmp_path: Path) -> None:
    pp = _make_valid_pp(tmp_path)
    (pp / "receipts.jsonl").write_text("{bad\n")
    result = check_schema(pp)
    assert result.passed is False
    assert "invalid JSON" in result.message
