"""Summary generation for proofpack verify results."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from proofpack.checks import CheckResult


def generate_summary(pp_dir: Path, results: list[CheckResult], verdict: str) -> str:
    """Generate a Markdown summary of verification results."""
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")

    # Read run_id and contract details (best-effort)
    run_id = "unknown"
    work_title = "unknown"
    work_scope = "(not available)"

    meta_path = pp_dir / "meta.json"
    if meta_path.exists():
        try:
            meta_raw = json.loads(meta_path.read_text())
            run_id = meta_raw.get("run_id", run_id)
        except (json.JSONDecodeError, AttributeError):
            pass

    contract_path = pp_dir / "contract.json"
    if contract_path.exists():
        try:
            contract_raw = json.loads(contract_path.read_text())
            work_title = contract_raw.get("work", {}).get("title", work_title)
            allowed = contract_raw.get("scope", {}).get("allowed_paths", [])
            forbidden = contract_raw.get("scope", {}).get("forbidden_paths", [])
            scope_parts: list[str] = []
            if allowed:
                scope_parts.append(f"allowed: {', '.join(allowed)}")
            if forbidden:
                scope_parts.append(f"forbidden: {', '.join(forbidden)}")
            if scope_parts:
                work_scope = "; ".join(scope_parts)
            else:
                work_scope = "unrestricted"
        except (json.JSONDecodeError, AttributeError):
            pass

    lines: list[str] = [
        "# Proofpack Verification Summary",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Timestamp | {timestamp} |",
        f"| Run ID | `{run_id}` |",
        f"| Verdict | **{verdict}** |",
        "",
        "## Contract",
        "",
        f"- **Title:** {work_title}",
        f"- **Scope:** {work_scope}",
        "",
        "## Checks",
        "",
        "| # | Name | Result | Details |",
        "|---|------|--------|---------|",
    ]

    for i, result in enumerate(results, start=1):
        if result.passed:
            status = "PASS"
        else:
            status = result.severity  # FAIL or WARN
        lines.append(f"| {i} | {result.name} | {status} | {result.message} |")

    lines.append("")

    # Changed files section (best-effort via git)
    changed_files_info = _try_get_changed_files(pp_dir)
    lines.append("## Files Changed")
    lines.append("")
    if changed_files_info:
        for f in changed_files_info:
            lines.append(f"- `{f}`")
    else:
        lines.append("_(not available)_")
    lines.append("")

    return "\n".join(lines)


def _try_get_changed_files(pp_dir: Path) -> list[str] | None:
    """Attempt to get git changed files; returns None on failure."""
    import subprocess

    meta_path = pp_dir / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta_raw = json.loads(meta_path.read_text())
        base_sha = meta_raw.get("repo", {}).get("base_sha", "")
        if not base_sha or base_sha == "unknown":
            return None
        result = subprocess.run(
            ["git", "diff", "--name-only", base_sha, "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.splitlines() if f.strip()]
            return files if files else None
    except (json.JSONDecodeError, OSError):
        pass
    return None
