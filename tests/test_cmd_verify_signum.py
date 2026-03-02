"""Tests for proofpack verify-signum command — full pipeline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from proofpack.commands.verify_signum import cmd_verify_signum


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _make_valid_signum(tmp_path: Path) -> Path:
    """Create a complete, valid .signum/ directory."""
    signum = tmp_path / ".signum"
    signum.mkdir()

    contract_data = {
        "schema_version": "2",
        "goal": "Add feature X",
        "inScope": ["src/**"],
        "outOfScope": [],
        "acceptanceCriteria": [{"description": "Tests pass"}],
        "riskLevel": "low",
    }
    contract_bytes = json.dumps(contract_data).encode()
    (signum / "contract.json").write_bytes(contract_bytes)

    patch_text = "--- a/src/main.py\n+++ b/src/main.py\n@@ -1 +1 @@\n-old\n+new\n"
    patch_bytes = patch_text.encode()
    (signum / "combined.patch").write_bytes(patch_bytes)

    proofpack_data = {
        "schema_version": "2",
        "run_id": "run-test-1",
        "decision": "AUTO_OK",
        "contract": "contract.json",
        "diff": "combined.patch",
        "checksums": {
            "contract.json": f"sha256:{_sha256_hex(contract_bytes)}",
            "combined.patch": f"sha256:{_sha256_hex(patch_bytes)}",
        },
        "summary": "",
    }
    (signum / "proofpack.json").write_text(json.dumps(proofpack_data))

    return signum


def test_verify_signum_pass(tmp_path: Path) -> None:
    signum = _make_valid_signum(tmp_path)
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=False,
    )
    assert result == 0
    assert (signum / "summary.md").exists()
    summary = (signum / "summary.md").read_text()
    assert "PASS" in summary


def test_verify_signum_fail_bad_schema(tmp_path: Path) -> None:
    signum = tmp_path / ".signum"
    signum.mkdir()
    (signum / "proofpack.json").write_text("{bad json")
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=False,
    )
    assert result == 1


def test_verify_signum_json_output(tmp_path: Path, capsys: object) -> None:
    signum = _make_valid_signum(tmp_path)
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=True,
    )
    assert result == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    data = json.loads(out)
    assert data["verdict"] == "PASS"
    assert len(data["checks"]) == 4


def test_verify_signum_warn_mode(tmp_path: Path) -> None:
    signum = tmp_path / ".signum"
    signum.mkdir()
    (signum / "proofpack.json").write_text(json.dumps({
        "schema_version": "2", "run_id": "r1", "decision": "AUTO_BLOCK",
        "contract": "contract.json", "diff": "combined.patch",
        "checksums": {}, "summary": "",
    }))
    (signum / "contract.json").write_text(json.dumps({
        "schema_version": "2", "goal": "test", "inScope": [], "outOfScope": [],
        "acceptanceCriteria": [], "riskLevel": "low",
    }))
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="warn", json_output=False,
    )
    # warn mode always returns 0
    assert result == 0


def test_verify_signum_nonexistent_dir(tmp_path: Path) -> None:
    result = cmd_verify_signum(
        signum_dir=str(tmp_path / "nonexistent"), mode="fail", json_output=False,
    )
    assert result == 1


def test_verify_signum_dry_run_no_summary_file(tmp_path: Path) -> None:
    signum = _make_valid_signum(tmp_path)
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=False, dry_run=True,
    )
    assert result == 0
    assert not (signum / "summary.md").exists()


def test_verify_signum_dry_run_still_prints(
    tmp_path: Path, capsys: object,
) -> None:
    signum = _make_valid_signum(tmp_path)
    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=False, dry_run=True,
    )
    assert result == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "PASS" in out


def test_verify_signum_human_review_is_warn(
    tmp_path: Path, capsys: object,
) -> None:
    """HUMAN_REVIEW → WARN verdict, exit 0 in fail mode."""
    signum = tmp_path / ".signum"
    signum.mkdir()

    contract_data = {
        "schema_version": "2", "goal": "test", "inScope": [], "outOfScope": [],
        "acceptanceCriteria": [], "riskLevel": "medium",
    }
    contract_bytes = json.dumps(contract_data).encode()
    (signum / "contract.json").write_bytes(contract_bytes)

    (signum / "proofpack.json").write_text(json.dumps({
        "schema_version": "2", "run_id": "r1", "decision": "HUMAN_REVIEW",
        "contract": "contract.json", "diff": "combined.patch",
        "checksums": {
            "contract.json": f"sha256:{_sha256_hex(contract_bytes)}",
        },
        "summary": "",
    }))

    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=True,
    )
    # HUMAN_REVIEW = WARN severity, not FAIL → exit 0
    assert result == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    data = json.loads(out)
    assert data["verdict"] == "WARN"


def test_verify_signum_auto_block_fails(tmp_path: Path) -> None:
    """AUTO_BLOCK → FAIL verdict, exit 1 in fail mode."""
    signum = tmp_path / ".signum"
    signum.mkdir()

    contract_data = {
        "schema_version": "2", "goal": "test", "inScope": [], "outOfScope": [],
        "acceptanceCriteria": [], "riskLevel": "high",
    }
    contract_bytes = json.dumps(contract_data).encode()
    (signum / "contract.json").write_bytes(contract_bytes)

    (signum / "proofpack.json").write_text(json.dumps({
        "schema_version": "2", "run_id": "r1", "decision": "AUTO_BLOCK",
        "contract": "contract.json", "diff": "combined.patch",
        "checksums": {
            "contract.json": f"sha256:{_sha256_hex(contract_bytes)}",
        },
        "summary": "",
    }))

    result = cmd_verify_signum(
        signum_dir=str(signum), mode="fail", json_output=False,
    )
    assert result == 1
    summary = (signum / "summary.md").read_text()
    assert "FAIL" in summary


def test_verify_shortcut_flag(tmp_path: Path, monkeypatch: object) -> None:
    """Test that verify --signum delegates to verify-signum."""
    import pytest

    mp = pytest.MonkeyPatch() if not isinstance(monkeypatch, pytest.MonkeyPatch) else monkeypatch
    mp.chdir(tmp_path)

    signum = _make_valid_signum(tmp_path)

    from click.testing import CliRunner

    from proofpack.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["verify", "--signum", str(signum)])
    assert result.exit_code == 0
    assert "PASS" in result.output
