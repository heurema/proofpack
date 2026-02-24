"""Check 4 & 5: Acceptance commands and artifact existence."""
from __future__ import annotations

import hashlib
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

    # Build set of expected input_sha256 hashes for required commands
    required_hashes: dict[str, str] = {}
    for cmd in required:
        # Hook stores input_data as json.dumps(tool_input), where tool_input is {"command": cmd}
        input_json = json.dumps({"command": cmd})
        h = hashlib.sha256(input_json.encode()).hexdigest()
        required_hashes[h] = cmd

    # Track which required commands were satisfied
    matched: set[str] = set()
    for line in receipts_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw: dict[str, object] = json.loads(line)
        except json.JSONDecodeError:
            continue
        if raw.get("tool") == "Bash" and raw.get("exit_code") == 0:
            input_hash = raw.get("input_sha256")
            if isinstance(input_hash, str) and input_hash in required_hashes:
                matched.add(input_hash)

    missing_cmds = [cmd for h, cmd in required_hashes.items() if h not in matched]

    if missing_cmds:
        return CheckResult(
            name=name,
            passed=False,
            message=(
                f"Missing acceptance commands: {', '.join(missing_cmds[:5])}"
                + (f" ... and {len(missing_cmds) - 5} more" if len(missing_cmds) > 5 else "")
            ),
        )

    return CheckResult(
        name=name,
        passed=True,
        message=f"All {len(required)} acceptance command(s) satisfied",
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
        # Reject absolute paths and parent-escaping traversals
        if artifact.startswith("/") or ".." in artifact.split("/"):
            missing.append(artifact)
            continue
        resolved = (root / artifact).resolve()
        if not resolved.is_file():
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
