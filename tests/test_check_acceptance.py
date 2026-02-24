"""Tests for check 4 (acceptance commands) and check 5 (artifact existence)."""
from __future__ import annotations

import hashlib
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


def _cmd_hash(command: str) -> str:
    """Compute input_sha256 as the hook would for a given command string."""
    input_json = json.dumps({"command": command})
    return hashlib.sha256(input_json.encode()).hexdigest()


def _bash_event(exit_code: int = 0, command: str | None = None) -> str:
    data: dict[str, object] = {
        "run_id": "run1",
        "t": "2024-01-01T00:00:00Z",
        "event": "tool_use",
        "tool": "Bash",
        "exit_code": exit_code,
    }
    if command is not None:
        data["input_sha256"] = _cmd_hash(command)
    return json.dumps(data)


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
    receipts = "\n".join([
        _bash_event(0, command="pytest"),
        _bash_event(0, command="ruff check"),
    ])
    (pp / "receipts.jsonl").write_text(receipts + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is True


def test_commands_missing_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest", "ruff check"])
    # Only pytest matched, ruff check missing
    (pp / "receipts.jsonl").write_text(_bash_event(0, command="pytest") + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is False
    assert "ruff check" in result.message


def test_failed_bash_events_not_counted(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest"])
    # exit_code=1 should not count even with matching hash
    (pp / "receipts.jsonl").write_text(_bash_event(1, command="pytest") + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is False


def test_empty_receipts_with_required_commands_fails(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest"])
    (pp / "receipts.jsonl").write_text("")
    result = check_acceptance_commands(pp)
    assert result.passed is False


def test_unmatched_bash_event_doesnt_satisfy(tmp_path: Path) -> None:
    """A successful Bash event for a different command should not satisfy."""
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, commands=["pytest"])
    (pp / "receipts.jsonl").write_text(_bash_event(0, command="echo hello") + "\n")
    result = check_acceptance_commands(pp)
    assert result.passed is False


def test_artifacts_path_traversal_rejected(tmp_path: Path) -> None:
    """Absolute paths and parent-escaping paths should be rejected."""
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, artifacts=["/etc/passwd", "../outside.txt"])
    result = check_artifacts(pp, repo_root=tmp_path)
    assert result.passed is False
    assert "/etc/passwd" in result.message


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
