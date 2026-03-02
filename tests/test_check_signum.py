"""Tests for signum-specific verification checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from proofpack.checks.signum_check import (
    _extract_patch_files,
    check_signum_checksums,
    check_signum_decision,
    check_signum_schema,
    check_signum_scope,
)

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_signum_dir(tmp_path: Path) -> Path:
    signum = tmp_path / ".signum"
    signum.mkdir()
    return signum


def _write_proofpack_json(
    signum: Path,
    *,
    decision: str = "AUTO_OK",
    checksums: dict[str, str] | None = None,
) -> None:
    data = {
        "schema_version": "2",
        "run_id": "run-test-1",
        "decision": decision,
        "contract": "contract.json",
        "diff": "combined.patch",
        "checksums": checksums or {},
        "summary": "",
    }
    (signum / "proofpack.json").write_text(json.dumps(data))


def _write_contract_json(
    signum: Path,
    *,
    goal: str = "Test goal",
    in_scope: list[str] | None = None,
    out_of_scope: list[str] | None = None,
) -> None:
    data = {
        "schema_version": "2",
        "goal": goal,
        "inScope": in_scope or [],
        "outOfScope": out_of_scope or [],
        "acceptanceCriteria": [],
        "riskLevel": "low",
    }
    (signum / "contract.json").write_text(json.dumps(data))


def _write_patch(signum: Path, files: list[str]) -> None:
    """Write a minimal unified diff touching the given files."""
    lines: list[str] = []
    for f in files:
        lines.extend([
            f"--- a/{f}",
            f"+++ b/{f}",
            "@@ -1 +1 @@",
            "-old",
            "+new",
        ])
    (signum / "combined.patch").write_text("\n".join(lines) + "\n")


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ── check_signum_schema ───────────────────────────────────────────────────────


def test_schema_pass(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum)
    result = check_signum_schema(signum)
    assert result.passed is True
    assert result.name == "signum-schema"


def test_schema_missing_proofpack_json(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_contract_json(signum)
    result = check_signum_schema(signum)
    assert result.passed is False
    assert "proofpack.json not found" in result.message


def test_schema_missing_contract_json(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    result = check_signum_schema(signum)
    assert result.passed is False
    assert "contract.json not found" in result.message


def test_schema_invalid_json(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    (signum / "proofpack.json").write_text("{bad")
    _write_contract_json(signum)
    result = check_signum_schema(signum)
    assert result.passed is False
    assert "parse error" in result.message


def test_schema_both_missing(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    result = check_signum_schema(signum)
    assert result.passed is False
    assert "proofpack.json not found" in result.message
    assert "contract.json not found" in result.message


# ── check_signum_checksums ────────────────────────────────────────────────────


def test_checksums_pass(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    content = b"hello world"
    (signum / "contract.json").write_bytes(content)
    _write_proofpack_json(signum, checksums={
        "contract.json": f"sha256:{_sha256_hex(content)}",
    })
    result = check_signum_checksums(signum)
    assert result.passed is True
    assert "1 checksum(s) verified" in result.message


def test_checksums_mismatch(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    (signum / "contract.json").write_bytes(b"actual content")
    _write_proofpack_json(signum, checksums={
        "contract.json": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    })
    result = check_signum_checksums(signum)
    assert result.passed is False
    assert "hash mismatch" in result.message


def test_checksums_missing_file(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, checksums={
        "nonexistent.json": "sha256:abc",
    })
    result = check_signum_checksums(signum)
    assert result.passed is False
    assert "file not found" in result.message


def test_checksums_empty(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, checksums={})
    result = check_signum_checksums(signum)
    assert result.passed is True
    assert result.severity == "WARN"


def test_checksums_bare_hex(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    content = b"test data"
    (signum / "data.txt").write_bytes(content)
    _write_proofpack_json(signum, checksums={
        "data.txt": _sha256_hex(content),
    })
    result = check_signum_checksums(signum)
    assert result.passed is True


def test_checksums_no_proofpack_json(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    result = check_signum_checksums(signum)
    assert result.passed is False
    assert "Cannot read" in result.message


# ── _extract_patch_files ─────────────────────────────────────────────────────


def test_extract_patch_files_basic() -> None:
    patch = (
        "--- a/src/foo.py\n"
        "+++ b/src/foo.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        "--- a/src/bar.py\n"
        "+++ b/src/bar.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )
    assert _extract_patch_files(patch) == ["src/foo.py", "src/bar.py"]


def test_extract_patch_files_dedup() -> None:
    patch = (
        "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-a\n+b\n"
        "--- a/f.py\n+++ b/f.py\n@@ -5 +5 @@\n-c\n+d\n"
    )
    assert _extract_patch_files(patch) == ["f.py"]


def test_extract_patch_files_deletion() -> None:
    patch = "--- a/old.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-deleted\n"
    assert _extract_patch_files(patch) == []


# ── check_signum_scope ────────────────────────────────────────────────────────


def test_scope_pass(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum, in_scope=["src/**"], out_of_scope=[])
    _write_patch(signum, ["src/foo.py", "src/bar.py"])
    result = check_signum_scope(signum)
    assert result.passed is True
    assert "2 file(s) checked" in result.message


def test_scope_out_of_scope_violation(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum, in_scope=[], out_of_scope=["*.env"])
    _write_patch(signum, ["src/main.py", ".env"])
    result = check_signum_scope(signum)
    assert result.passed is False
    assert "outOfScope" in result.message


def test_scope_outside_in_scope(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum, in_scope=["src/**"], out_of_scope=[])
    _write_patch(signum, ["scripts/hack.sh"])
    result = check_signum_scope(signum)
    assert result.passed is False
    assert "inScope" in result.message


def test_scope_empty_in_scope_allows_all(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum, in_scope=[], out_of_scope=[])
    _write_patch(signum, ["anywhere/file.py"])
    result = check_signum_scope(signum)
    assert result.passed is True


def test_scope_no_patch_file(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    _write_contract_json(signum, in_scope=["src/**"])
    result = check_signum_scope(signum)
    assert result.passed is True
    assert result.severity == "WARN"
    assert "skipped" in result.message


def test_scope_no_contract(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum)
    result = check_signum_scope(signum)
    assert result.passed is False
    assert "Cannot read" in result.message


# ── check_signum_decision ─────────────────────────────────────────────────────


def test_decision_auto_ok(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, decision="AUTO_OK")
    result = check_signum_decision(signum)
    assert result.passed is True
    assert "AUTO_OK" in result.message


def test_decision_auto_block(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, decision="AUTO_BLOCK")
    result = check_signum_decision(signum)
    assert result.passed is False
    assert result.severity == "FAIL"


def test_decision_human_review(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, decision="HUMAN_REVIEW")
    result = check_signum_decision(signum)
    assert result.passed is False
    assert result.severity == "WARN"


def test_decision_unknown(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    _write_proofpack_json(signum, decision="SOMETHING_ELSE")
    result = check_signum_decision(signum)
    assert result.passed is False
    assert result.severity == "FAIL"
    assert "Unknown" in result.message


def test_decision_no_proofpack_json(tmp_path: Path) -> None:
    signum = _make_signum_dir(tmp_path)
    result = check_signum_decision(signum)
    assert result.passed is False
    assert "Cannot read" in result.message
