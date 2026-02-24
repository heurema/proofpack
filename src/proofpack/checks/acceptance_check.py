"""Check 4 & 5: Acceptance commands and artifact existence."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.schemas import ContractV1


def check_acceptance_commands(pp_dir: Path) -> CheckResult:
    """Check 4: Verify that enough successful Bash events exist for required commands."""
    name = "acceptance_commands"

    contract_path = pp_dir / "contract.json"
    receipts_path = pp_dir / "receipts.jsonl"

    if not contract_path.exists():
        return CheckResult(name=name, passed=False, message="contract.json not found")

    try:
        contract = ContractV1.from_dict(json.loads(contract_path.read_text()))
    except (json.JSONDecodeError, KeyError, AssertionError, TypeError) as exc:
        return CheckResult(name=name, passed=False, message=f"contract.json parse error: {exc}")

    required = contract.acceptance_commands
    if not required:
        return CheckResult(
            name=name,
            passed=True,
            message="No acceptance commands required",
        )

    if not receipts_path.exists():
        return CheckResult(name=name, passed=False, message="receipts.jsonl not found")

    # Count successful Bash events (tool=Bash, exit_code=0)
    successful_bash = 0
    for line in receipts_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw: dict[str, object] = json.loads(line)
        except json.JSONDecodeError:
            continue
        if raw.get("tool") == "Bash" and raw.get("exit_code") == 0:
            successful_bash += 1

    if successful_bash < len(required):
        return CheckResult(
            name=name,
            passed=False,
            message=(
                f"Insufficient successful Bash events: "
                f"need {len(required)}, found {successful_bash}"
            ),
        )

    return CheckResult(
        name=name,
        passed=True,
        message=(
            f"Acceptance commands satisfied — "
            f"{successful_bash} successful Bash event(s) for {len(required)} required command(s)"
        ),
    )


def check_artifacts(pp_dir: Path, repo_root: Path | None = None) -> CheckResult:
    """Check 5: Verify that all required artifacts exist on disk."""
    name = "artifacts"

    contract_path = pp_dir / "contract.json"

    if not contract_path.exists():
        return CheckResult(
            name=name, passed=False, message="contract.json not found", severity="WARN"
        )

    try:
        contract = ContractV1.from_dict(json.loads(contract_path.read_text()))
    except (json.JSONDecodeError, KeyError, AssertionError, TypeError) as exc:
        return CheckResult(
            name=name,
            passed=False,
            message=f"contract.json parse error: {exc}",
            severity="WARN",
        )

    root = repo_root if repo_root is not None else pp_dir.parent
    artifacts = contract.acceptance_artifacts

    if not artifacts:
        return CheckResult(
            name=name,
            passed=True,
            message="No artifacts required",
            severity="WARN",
        )

    missing: list[str] = []
    for artifact in artifacts:
        if not (root / artifact).exists():
            missing.append(artifact)

    if missing:
        return CheckResult(
            name=name,
            passed=False,
            message=f"Missing artifacts: {', '.join(missing)}",
            severity="WARN",
        )

    return CheckResult(
        name=name,
        passed=True,
        message=f"All {len(artifacts)} artifact(s) present",
        severity="WARN",
    )
