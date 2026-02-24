"""Check 2: Receipt integrity — run_id matches and SHA-256 hashes are valid hex."""
from __future__ import annotations

import json
import re
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.schemas import MetaV1

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{4,64}$")
_SHA_FIELDS = (
    "input_sha256",
    "stdout_sha256",
    "stderr_sha256",
    "before_sha256",
    "after_sha256",
)


def check_integrity(pp_dir: Path) -> CheckResult:
    """Validate run_id consistency and SHA-256 field format in receipts."""
    name = "integrity"

    meta_path = pp_dir / "meta.json"
    receipts_path = pp_dir / "receipts.jsonl"

    if not meta_path.exists():
        return CheckResult(name=name, passed=False, message="meta.json not found")
    if not receipts_path.exists():
        return CheckResult(name=name, passed=False, message="receipts.jsonl not found")

    try:
        meta = MetaV1.from_dict(json.loads(meta_path.read_text()))
    except (json.JSONDecodeError, KeyError, AssertionError, TypeError) as exc:
        return CheckResult(name=name, passed=False, message=f"meta.json parse error: {exc}")

    expected_run_id = meta.run_id
    lines = receipts_path.read_text().splitlines()
    checked = 0

    for lineno, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            raw: dict[str, object] = json.loads(line)
        except json.JSONDecodeError as exc:
            return CheckResult(
                name=name,
                passed=False,
                message=f"receipts.jsonl line {lineno} invalid JSON: {exc}",
            )

        # Required fields
        for field in ("run_id", "t", "event", "tool"):
            if field not in raw:
                return CheckResult(
                    name=name,
                    passed=False,
                    message=f"receipts.jsonl line {lineno} missing required field: {field!r}",
                )

        # run_id must match meta
        actual_run_id = raw["run_id"]
        if actual_run_id != expected_run_id:
            return CheckResult(
                name=name,
                passed=False,
                message=(
                    f"receipts.jsonl line {lineno} run_id mismatch: "
                    f"expected {expected_run_id!r}, got {actual_run_id!r}"
                ),
            )

        # Validate SHA-256 fields
        for sha_field in _SHA_FIELDS:
            value = raw.get(sha_field)
            if value is not None:
                if not isinstance(value, str) or not _SHA256_RE.match(value):
                    return CheckResult(
                        name=name,
                        passed=False,
                        message=(
                            f"receipts.jsonl line {lineno} invalid {sha_field}: {value!r}"
                        ),
                    )

        checked += 1

    return CheckResult(
        name=name,
        passed=True,
        message=f"Integrity valid — {checked} event(s) checked",
    )
