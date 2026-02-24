"""Check 3: Scope compliance — changed files match contract scope."""
from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.schemas import ContractV1


def _check_file_scope(
    files: list[str],
    allowed: list[str],
    forbidden: list[str],
) -> list[str]:
    """Return a list of scope violations for the given files.

    Forbidden patterns are checked first; if a file matches any forbidden
    pattern it is a violation regardless of allowed patterns.
    Allowed patterns are checked next; if the allowed list is non-empty and a
    file does not match any allowed pattern it is a violation.
    An empty allowed list means all files are allowed (after forbidden check).
    """
    violations: list[str] = []
    for f in files:
        # Check forbidden first
        if any(fnmatch.fnmatch(f, pat) for pat in forbidden):
            violations.append(f"File matches forbidden pattern: {f!r}")
            continue
        # Check allowed (empty = allow all)
        if allowed and not any(fnmatch.fnmatch(f, pat) for pat in allowed):
            violations.append(f"File outside allowed scope: {f!r}")
    return violations


def _get_changed_files(base_sha: str) -> list[str] | None:
    """Return files changed since base_sha via git, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_sha, "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return [line for line in result.stdout.splitlines() if line.strip()]
    except OSError:
        pass
    return None


def check_scope(pp_dir: Path, changed_files: list[str] | None = None) -> CheckResult:
    """Verify that all changed files fall within the contract scope."""
    name = "scope"

    contract_path = pp_dir / "contract.json"
    meta_path = pp_dir / "meta.json"

    if not contract_path.exists():
        return CheckResult(name=name, passed=False, message="contract.json not found")

    try:
        contract = ContractV1.from_dict(json.loads(contract_path.read_text()))
    except (json.JSONDecodeError, KeyError, AssertionError, TypeError) as exc:
        return CheckResult(name=name, passed=False, message=f"contract.json parse error: {exc}")

    if changed_files is None:
        # Try to resolve via git using base_sha from meta.json
        if meta_path.exists():
            try:
                meta_raw = json.loads(meta_path.read_text())
                base_sha = meta_raw.get("repo", {}).get("base_sha", "")
            except (json.JSONDecodeError, AttributeError):
                base_sha = ""
        else:
            base_sha = ""

        if base_sha and base_sha != "unknown":
            changed_files = _get_changed_files(base_sha)

    if changed_files is None:
        return CheckResult(
            name=name,
            passed=True,
            message="Scope check skipped — no changed files available",
        )

    violations = _check_file_scope(
        files=changed_files,
        allowed=contract.allowed_paths,
        forbidden=contract.forbidden_paths,
    )

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
