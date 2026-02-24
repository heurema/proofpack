"""Tests for check 4 (acceptance commands) and check 5 (artifact existence)."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks.acceptance_check import check_acceptance_commands, check_artifacts


def _make_contract(
    pp: Path,
    commands: list[str] | None = None,
    artifacts: list[str] | None = None,
) -> None:
    (pp / "contract.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run1",
                "work": {"title": "Test", "summary": ""},
                "scope": {"allowed_paths": [], "forbidden_paths": []},
                "acceptance": {
                    "commands": commands if commands is not None else [],
                    "artifacts": artifacts if artifacts is not None else [],
                },
            }
        )
    )


def _bash_event(exit_code: int = 0) -> str:
    return json.dumps(
        {
            "run_id": "run1",
            "t": "2024-01-01T00:00:00Z",
            "event": "tool_use",
            "tool": "Bash",
            "exit_code": exit_code,
        }
    )


# ── acceptance_commands ───────────────────────────────────────────────────────


def test_no_commands_required_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=[])
    (pp / "receipts.jsonl").write_text("")
    result = check_acceptance_commands(pp)
    assert result.passed is True
    assert "No acceptance commands" in result.message


def test_commands_present_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest", "ruff check"])
    receipts = "\n".join([_bash_event(0), _bash_event(0)])
    (pp / "receipts.jsonl").write_text(receipts + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is True


def test_commands_missing_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest", "ruff check"])
    # Only 1 successful Bash event but 2 required
    (pp / "receipts.jsonl").write_text(_bash_event(0) + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is False
    assert "Insufficient" in result.message


def test_failed_bash_events_not_counted(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest"])
    # exit_code=1 should not count
    (pp / "receipts.jsonl").write_text(_bash_event(1) + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is False


def test_empty_receipts_with_required_commands_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest"])
    (pp / "receipts.jsonl").write_text("")
    result = check_acceptance_commands(pp)
    assert result.passed is False


# ── artifacts ─────────────────────────────────────────────────────────────────


def test_no_artifacts_required_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, artifacts=[])
    result = check_artifacts(pp)
    assert result.passed is True
    assert result.severity == "WARN"


def test_artifacts_exist_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    artifact = tmp_path / "output.txt"
    artifact.write_text("done")
    _make_contract(pp, artifacts=["output.txt"])
    result = check_artifacts(pp, repo_root=tmp_path)
    assert result.passed is True
    assert result.severity == "WARN"


def test_artifacts_missing_fails_with_warn(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, artifacts=["missing_file.txt"])
    result = check_artifacts(pp, repo_root=tmp_path)
    assert result.passed is False
    assert result.severity == "WARN"
    assert "missing_file.txt" in result.message


def test_partial_artifacts_missing_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    present = tmp_path / "present.txt"
    present.write_text("here")
    _make_contract(pp, artifacts=["present.txt", "absent.txt"])
    result = check_artifacts(pp, repo_root=tmp_path)
    assert result.passed is False
    assert "absent.txt" in result.message
    assert result.severity == "WARN"
