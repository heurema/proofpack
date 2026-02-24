"""Tests for check 2: receipt integrity."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks.integrity_check import check_integrity


def _make_meta(pp: Path, run_id: str = "run1") -> None:
    (pp / "meta.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": run_id,
                "receipt_integrity": "full",
                "repo": {"vcs": "git", "head_sha": "abc", "base_sha": "def"},
                "runtime": {"name": "claude-code", "version": "1.0"},
                "env": {"os": "darwin", "ci": False},
            }
        )
    )


def _make_event(run_id: str = "run1", **kwargs: object) -> str:
    data: dict[str, object] = {
        "run_id": run_id,
        "t": "2024-01-01T00:00:00Z",
        "event": "tool_use",
        "tool": "Bash",
    }
    data.update(kwargs)
    return json.dumps(data)


def test_empty_receipts_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    (pp / "receipts.jsonl").write_text("")
    result = check_integrity(pp)
    assert result.passed is True
    assert "0 event" in result.message


def test_valid_receipts_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    events = "\n".join(
        [
            _make_event(stdout_sha256="a" * 64),
            _make_event(input_sha256="b" * 64),
        ]
    )
    (pp / "receipts.jsonl").write_text(events + "\n")
    result = check_integrity(pp)
    assert result.passed is True
    assert "2 event" in result.message


def test_run_id_mismatch_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp, run_id="run1")
    (pp / "receipts.jsonl").write_text(_make_event(run_id="run-other") + "\n")
    result = check_integrity(pp)
    assert result.passed is False
    assert "mismatch" in result.message


def test_invalid_sha256_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    (pp / "receipts.jsonl").write_text(_make_event(stdout_sha256="not-hex!") + "\n")
    result = check_integrity(pp)
    assert result.passed is False
    assert "stdout_sha256" in result.message


def test_invalid_sha256_too_short_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    # Less than 64 hex chars — must be rejected
    (pp / "receipts.jsonl").write_text(_make_event(before_sha256="ab") + "\n")
    result = check_integrity(pp)
    assert result.passed is False
    assert "before_sha256" in result.message


def test_short_hex_hash_rejected(tmp_path: Path) -> None:
    """8-char hex like 'deadbeef' must fail — only 64-char SHA256 accepted."""
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    (pp / "receipts.jsonl").write_text(_make_event(stdout_sha256="deadbeef") + "\n")
    result = check_integrity(pp)
    assert result.passed is False
    assert "stdout_sha256" in result.message


def test_missing_tool_field_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_meta(pp)
    data = {"run_id": "run1", "t": "2024-01-01T00:00:00Z", "event": "tool_use"}
    (pp / "receipts.jsonl").write_text(json.dumps(data) + "\n")
    result = check_integrity(pp)
    assert result.passed is False
    assert "tool" in result.message
