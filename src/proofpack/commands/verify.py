"""proofpack verify command — runs all checks and produces a summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.checks.acceptance_check import check_acceptance_commands, check_artifacts
from proofpack.checks.integrity_check import check_integrity
from proofpack.checks.schema_check import check_schema
from proofpack.checks.scope_check import check_scope
from proofpack.checks.summary import generate_summary


def _read_receipt_integrity(pp_dir: Path) -> str:
    """Return receipt_integrity from meta.json, defaulting to 'full'."""
    meta_path = pp_dir / "meta.json"
    if not meta_path.exists():
        return "full"
    try:
        raw = json.loads(meta_path.read_text())
        return str(raw.get("receipt_integrity", "full"))
    except (json.JSONDecodeError, AttributeError):
        return "full"


def cmd_verify(mode: str, json_output: bool) -> int:
    """Run the full verify pipeline and report results.

    Args:
        mode: "fail" to exit 1 on FAIL severity, "warn" to always exit 0.
        json_output: if True, emit JSON instead of Markdown summary.

    Returns:
        0 on PASS/WARN, 1 on FAIL (when mode="fail").
    """
    pp_dir = Path(".proofpack")

    if not pp_dir.exists():
        print("Error: .proofpack/ not found. Run 'proofpack init' first.", file=sys.stderr)
        return 1

    receipt_integrity = _read_receipt_integrity(pp_dir)
    partial = receipt_integrity == "partial"

    # Run checks in order
    results: list[CheckResult] = []

    # Check 1: schema (always full severity)
    schema_result = check_schema(pp_dir)
    results.append(schema_result)

    # Checks 2–4 downgrade to WARN when partial integrity
    integrity_result = check_integrity(pp_dir)
    if partial and not integrity_result.passed:
        integrity_result = CheckResult(
            name=integrity_result.name,
            passed=integrity_result.passed,
            message=integrity_result.message,
            severity="WARN",
        )
    results.append(integrity_result)

    scope_result = check_scope(pp_dir)
    if partial and not scope_result.passed:
        scope_result = CheckResult(
            name=scope_result.name,
            passed=scope_result.passed,
            message=scope_result.message,
            severity="WARN",
        )
    results.append(scope_result)

    acceptance_result = check_acceptance_commands(pp_dir)
    if partial and not acceptance_result.passed:
        acceptance_result = CheckResult(
            name=acceptance_result.name,
            passed=acceptance_result.passed,
            message=acceptance_result.message,
            severity="WARN",
        )
    results.append(acceptance_result)

    # Check 5: artifacts — always WARN severity (already set in check_artifacts)
    artifacts_result = check_artifacts(pp_dir)
    results.append(artifacts_result)

    # Determine verdict
    has_fail = any(not r.passed and r.severity == "FAIL" for r in results)
    has_warn = any(not r.passed for r in results)  # includes WARN failures

    if has_fail:
        verdict = "FAIL"
    elif has_warn:
        verdict = "WARN"
    else:
        verdict = "PASS"

    # Generate and write summary
    summary_text = generate_summary(pp_dir, results, verdict)
    summary_path = pp_dir / "summary.md"
    summary_path.write_text(summary_text)

    if json_output:
        output = {
            "verdict": verdict,
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(summary_text)

    # Exit code: 1 only when mode=fail and there is a FAIL-severity failure
    if mode == "fail" and has_fail:
        return 1
    return 0
