"""Check 1: Schema validation — all required files exist and parse correctly."""
from __future__ import annotations

import json
from pathlib import Path

from proofpack.checks import CheckResult
from proofpack.schemas import ContractV1, MetaV1, ReceiptEvent


def check_schema(pp_dir: Path) -> CheckResult:
    """Validate that contract.json, meta.json, and receipts.jsonl exist and parse."""
    name = "schema"

    contract_path = pp_dir / "contract.json"
    meta_path = pp_dir / "meta.json"
    receipts_path = pp_dir / "receipts.jsonl"

    for path in (contract_path, meta_path, receipts_path):
        if not path.exists():
            return CheckResult(
                name=name,
                passed=False,
                message=f"Missing required file: {path.name}",
            )

    try:
        contract_raw = json.loads(contract_path.read_text())
    except json.JSONDecodeError as exc:
        return CheckResult(name=name, passed=False, message=f"contract.json invalid JSON: {exc}")

    try:
        ContractV1.from_dict(contract_raw)
    except (KeyError, AssertionError, TypeError) as exc:
        return CheckResult(
            name=name, passed=False, message=f"contract.json missing required field: {exc}"
        )

    try:
        meta_raw = json.loads(meta_path.read_text())
    except json.JSONDecodeError as exc:
        return CheckResult(name=name, passed=False, message=f"meta.json invalid JSON: {exc}")

    try:
        MetaV1.from_dict(meta_raw)
    except (KeyError, AssertionError, TypeError) as exc:
        return CheckResult(
            name=name, passed=False, message=f"meta.json missing required field: {exc}"
        )

    event_count = 0
    for lineno, line in enumerate(receipts_path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            ReceiptEvent.from_json_line(line)
        except json.JSONDecodeError as exc:
            return CheckResult(
                name=name,
                passed=False,
                message=f"receipts.jsonl line {lineno} invalid JSON: {exc}",
            )
        except (KeyError, TypeError) as exc:
            return CheckResult(
                name=name,
                passed=False,
                message=f"receipts.jsonl line {lineno} missing required field: {exc}",
            )
        event_count += 1

    return CheckResult(
        name=name,
        passed=True,
        message=f"Schema valid — {event_count} receipt event(s)",
    )
