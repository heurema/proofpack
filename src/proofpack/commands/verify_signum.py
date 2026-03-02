"""proofpack verify-signum command — runs signum-specific checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.checks.signum_check import (
    check_signum_checksums,
    check_signum_decision,
    check_signum_schema,
    check_signum_scope,
)


def _generate_signum_summary(
    signum_dir: Path, results: list[CheckResult], verdict: str
) -> str:
    """Generate a Markdown summary for signum verification."""
    from datetime import UTC, datetime

    timestamp = datetime.now(UTC).isoformat(timespec="seconds")

    # Read run_id and contract details (best-effort)
    run_id = "unknown"
    goal = "unknown"
    scope_info = "(not available)"

    pp_path = signum_dir / "proofpack.json"
    if pp_path.exists():
        try:
            raw = json.loads(pp_path.read_text())
            run_id = raw.get("run_id", run_id)
        except (json.JSONDecodeError, AttributeError):
            pass

    contract_path = signum_dir / "contract.json"
    if contract_path.exists():
        try:
            raw = json.loads(contract_path.read_text())
            in_scope = raw.get("inScope", [])
            out_of_scope = raw.get("outOfScope", [])
            goal = raw.get("goal", goal)
            parts: list[str] = []
            if in_scope:
                parts.append(f"inScope: {', '.join(in_scope)}")
            if out_of_scope:
                parts.append(f"outOfScope: {', '.join(out_of_scope)}")
            scope_info = "; ".join(parts) if parts else "unrestricted"
        except (json.JSONDecodeError, AttributeError):
            pass

    lines: list[str] = [
        "# Signum Verification Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Timestamp | {timestamp} |",
        f"| Run ID | `{run_id}` |",
        f"| Verdict | **{verdict}** |",
        "",
        "## Contract",
        "",
        f"- **Goal:** {goal}",
        f"- **Scope:** {scope_info}",
        "",
        "## Checks",
        "",
        "| # | Name | Result | Details |",
        "|---|------|--------|---------|",
    ]

    for i, result in enumerate(results, start=1):
        status = "PASS" if result.passed else result.severity
        lines.append(f"| {i} | {result.name} | {status} | {result.message} |")

    lines.append("")
    return "\n".join(lines)


def cmd_verify_signum(
    signum_dir: str, mode: str, json_output: bool, dry_run: bool = False
) -> int:
    """Run signum-specific verification pipeline.

    Args:
        signum_dir: path to the .signum/ directory.
        mode: "fail" to exit 1 on FAIL severity, "warn" to always exit 0.
        json_output: if True, emit JSON instead of Markdown summary.
        dry_run: if True, skip writing summary.md to disk.

    Returns:
        0 on PASS/WARN, 1 on FAIL (when mode="fail").
    """
    path = Path(signum_dir)

    if not path.is_dir():
        print(f"Error: {signum_dir} not found or not a directory.", file=sys.stderr)
        return 1

    results: list[CheckResult] = [
        check_signum_schema(path),
        check_signum_checksums(path),
        check_signum_scope(path),
        check_signum_decision(path),
    ]

    has_fail = any(not r.passed and r.severity == "FAIL" for r in results)
    has_warn = any(not r.passed for r in results)

    if has_fail:
        verdict = "FAIL"
    elif has_warn:
        verdict = "WARN"
    else:
        verdict = "PASS"

    summary_text = _generate_signum_summary(path, results, verdict)
    if not dry_run:
        summary_path = path / "summary.md"
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

    if mode == "fail" and has_fail:
        return 1
    return 0
