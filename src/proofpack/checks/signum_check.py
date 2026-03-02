"""Signum-specific verification checks for .signum/ artifacts."""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any

from proofpack.checks import CheckResult
from proofpack.schemas import SignumContractV2, SignumProofpackV2


def _parse_signum_proofpack(signum_dir: Path) -> SignumProofpackV2 | None:
    """Parse .signum/proofpack.json, returning None on failure."""
    path = signum_dir / "proofpack.json"
    if not path.exists():
        return None
    try:
        raw: dict[str, Any] = json.loads(path.read_text())
        return SignumProofpackV2.from_dict(raw)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _parse_signum_contract(signum_dir: Path) -> SignumContractV2 | None:
    """Parse .signum/contract.json, returning None on failure."""
    path = signum_dir / "contract.json"
    if not path.exists():
        return None
    try:
        raw: dict[str, Any] = json.loads(path.read_text())
        return SignumContractV2.from_dict(raw)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def check_signum_schema(signum_dir: Path) -> CheckResult:
    """Validate proofpack.json and contract.json exist and parse."""
    name = "signum-schema"
    errors: list[str] = []

    pp_path = signum_dir / "proofpack.json"
    if not pp_path.exists():
        errors.append("proofpack.json not found")
    else:
        try:
            raw = json.loads(pp_path.read_text())
            SignumProofpackV2.from_dict(raw)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            errors.append(f"proofpack.json parse error: {exc}")

    contract_path = signum_dir / "contract.json"
    if not contract_path.exists():
        errors.append("contract.json not found")
    else:
        try:
            raw = json.loads(contract_path.read_text())
            SignumContractV2.from_dict(raw)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            errors.append(f"contract.json parse error: {exc}")

    if errors:
        return CheckResult(name=name, passed=False, message="; ".join(errors))

    return CheckResult(name=name, passed=True, message="Schema valid")


def check_signum_checksums(signum_dir: Path) -> CheckResult:
    """Verify SHA-256 in proofpack.json match actual files on disk."""
    name = "signum-checksums"

    proof = _parse_signum_proofpack(signum_dir)
    if proof is None:
        return CheckResult(name=name, passed=False, message="Cannot read proofpack.json")

    if not proof.checksums:
        return CheckResult(
            name=name, passed=True, message="No checksums to verify", severity="WARN"
        )

    mismatches: list[str] = []
    for filename, expected_hash in proof.checksums.items():
        file_path = signum_dir / filename
        if not file_path.exists():
            mismatches.append(f"{filename}: file not found")
            continue

        actual_hash = "sha256:" + hashlib.sha256(file_path.read_bytes()).hexdigest()
        if expected_hash.startswith("sha256:"):
            if actual_hash != expected_hash:
                mismatches.append(f"{filename}: hash mismatch")
        else:
            # Bare hex hash
            bare_actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if bare_actual != expected_hash:
                mismatches.append(f"{filename}: hash mismatch")

    if mismatches:
        details = "; ".join(mismatches[:5])
        if len(mismatches) > 5:
            details += f" ... and {len(mismatches) - 5} more"
        return CheckResult(
            name=name,
            passed=False,
            message=f"{len(mismatches)} checksum failure(s): {details}",
        )

    return CheckResult(
        name=name,
        passed=True,
        message=f"All {len(proof.checksums)} checksum(s) verified",
    )


def _extract_patch_files(patch_text: str) -> list[str]:
    """Extract changed file paths from unified diff headers."""
    files: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:].strip()
            if path and path != "/dev/null":
                files.append(path)
        elif line.startswith("--- a/"):
            # Handle deletions (file only in --- a/, +++ /dev/null)
            pass
    return list(dict.fromkeys(files))  # dedupe preserving order


def check_signum_scope(signum_dir: Path) -> CheckResult:
    """Parse combined.patch to get changed files, check against inScope/outOfScope."""
    name = "signum-scope"

    contract = _parse_signum_contract(signum_dir)
    if contract is None:
        return CheckResult(name=name, passed=False, message="Cannot read contract.json")

    proof = _parse_signum_proofpack(signum_dir)
    diff_filename = proof.diff if proof else "combined.patch"
    patch_path = signum_dir / diff_filename
    if not patch_path.exists():
        return CheckResult(
            name=name,
            passed=True,
            message="Scope check skipped — no patch file",
            severity="WARN",
        )

    patch_text = patch_path.read_text()
    changed_files = _extract_patch_files(patch_text)

    if not changed_files:
        return CheckResult(
            name=name,
            passed=True,
            message="No changed files found in patch",
            severity="WARN",
        )

    violations: list[str] = []
    in_scope = contract.in_scope
    out_of_scope = contract.out_of_scope

    for f in changed_files:
        # Check outOfScope first (deny takes priority)
        if any(fnmatch.fnmatch(f, pat) for pat in out_of_scope):
            violations.append(f"File matches outOfScope: {f!r}")
            continue
        # Check inScope (empty = allow all)
        if in_scope and not any(fnmatch.fnmatch(f, pat) for pat in in_scope):
            violations.append(f"File outside inScope: {f!r}")

    if violations:
        details = "; ".join(violations[:5])
        if len(violations) > 5:
            details += f" ... and {len(violations) - 5} more"
        return CheckResult(
            name=name,
            passed=False,
            message=f"{len(violations)} scope violation(s): {details}",
        )

    return CheckResult(
        name=name,
        passed=True,
        message=f"Scope valid — {len(changed_files)} file(s) checked",
    )


def check_signum_decision(signum_dir: Path) -> CheckResult:
    """Map signum decision to proofpack verdict."""
    name = "signum-decision"

    proof = _parse_signum_proofpack(signum_dir)
    if proof is None:
        return CheckResult(name=name, passed=False, message="Cannot read proofpack.json")

    decision = proof.decision.upper()

    if decision == "AUTO_OK":
        return CheckResult(name=name, passed=True, message="Decision: AUTO_OK")
    elif decision == "AUTO_BLOCK":
        return CheckResult(
            name=name, passed=False, message="Decision: AUTO_BLOCK", severity="FAIL"
        )
    elif decision == "HUMAN_REVIEW":
        return CheckResult(
            name=name, passed=False, message="Decision: HUMAN_REVIEW", severity="WARN"
        )
    else:
        return CheckResult(
            name=name,
            passed=False,
            message=f"Unknown decision: {proof.decision!r}",
            severity="FAIL",
        )
