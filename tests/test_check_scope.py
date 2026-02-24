"""Tests for check 3: scope compliance."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks.scope_check import _check_file_scope, check_scope

# ── unit tests for _check_file_scope ──────────────────────────────────────────


def test_all_files_in_scope_passes() -> None:
    violations = _check_file_scope(
        files=["src/foo.py", "src/bar.py"],
        allowed=["src/**"],
        forbidden=[],
    )
    assert violations == []


def test_file_outside_scope_fails() -> None:
    violations = _check_file_scope(
        files=["src/foo.py", "scripts/hack.sh"],
        allowed=["src/**"],
        forbidden=[],
    )
    assert len(violations) == 1
    assert "scripts/hack.sh" in violations[0]


def test_file_in_forbidden_fails() -> None:
    violations = _check_file_scope(
        files=["src/foo.py", ".env"],
        allowed=["src/**"],
        forbidden=[".env", "*.secret"],
    )
    assert len(violations) == 1
    assert ".env" in violations[0]


def test_forbidden_takes_priority_over_allowed() -> None:
    violations = _check_file_scope(
        files=["src/secrets.env"],
        allowed=["src/**"],
        forbidden=["*.env"],
    )
    assert len(violations) == 1
    assert "forbidden" in violations[0]


def test_empty_allowed_allows_all() -> None:
    violations = _check_file_scope(
        files=["anything/goes.txt", "really/anything.py"],
        allowed=[],
        forbidden=[],
    )
    assert violations == []


def test_empty_allowed_still_respects_forbidden() -> None:
    violations = _check_file_scope(
        files=["safe.py", "bad.secret"],
        allowed=[],
        forbidden=["*.secret"],
    )
    assert len(violations) == 1
    assert "bad.secret" in violations[0]


def test_multiple_violations() -> None:
    violations = _check_file_scope(
        files=["a.py", "b.py", "c.py"],
        allowed=["a.py"],
        forbidden=[],
    )
    assert len(violations) == 2


# ── integration tests for check_scope ──────────────────────────────────────────


def _make_contract(pp: Path, allowed: list[str], forbidden: list[str]) -> None:
    (pp / "contract.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run1",
                "work": {"title": "Test", "summary": ""},
                "scope": {"allowed_paths": allowed, "forbidden_paths": forbidden},
                "acceptance": {"commands": [], "artifacts": []},
            }
        )
    )


def test_check_scope_passes(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, allowed=["src/**"], forbidden=[])
    result = check_scope(pp, changed_files=["src/foo.py"])
    assert result.passed is True


def test_check_scope_fails_outside(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, allowed=["src/**"], forbidden=[])
    result = check_scope(pp, changed_files=["scripts/hack.sh"])
    assert result.passed is False
    assert "scope violation" in result.message


def test_check_scope_fails_forbidden(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, allowed=[], forbidden=["*.env"])
    result = check_scope(pp, changed_files=[".env"])
    assert result.passed is False
    assert "scope violation" in result.message


def test_check_scope_empty_allowed_allows_all(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, allowed=[], forbidden=[])
    result = check_scope(pp, changed_files=["anywhere/file.py", "other/place.txt"])
    assert result.passed is True


def test_check_scope_no_changed_files_skips(tmp_path: Path) -> None:
    pp = tmp_path / ".proofpack"
    pp.mkdir()
    _make_contract(pp, allowed=["src/**"], forbidden=[])
    # No changed_files and no meta.json with a valid base_sha
    result = check_scope(pp, changed_files=None)
    assert result.passed is True
    assert "skipped" in result.message
    assert result.severity == "WARN"
