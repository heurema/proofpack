"""Receipt writing for Claude Code hook integration."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def append_receipt(
    pp_dir: Path,
    *,
    tool: str,
    event: str,
    exit_code: int | None = None,
    input_data: str | None = None,
    stdout_data: str | None = None,
    stderr_data: str | None = None,
    path: str | None = None,
    before_content: str | None = None,
    after_content: str | None = None,
) -> None:
    meta = json.loads((pp_dir / "meta.json").read_text())
    run_id = meta["run_id"]

    record: dict[str, object] = {
        "run_id": run_id,
        "t": datetime.now(UTC).isoformat(),
        "event": event,
        "tool": tool,
    }

    if input_data is not None:
        record["input_sha256"] = _sha256(input_data)
    if exit_code is not None:
        record["exit_code"] = exit_code
    if stdout_data is not None:
        record["stdout_sha256"] = _sha256(stdout_data)
    if stderr_data is not None:
        record["stderr_sha256"] = _sha256(stderr_data)
    if path is not None:
        record["path"] = path
    if before_content is not None:
        record["before_sha256"] = _sha256(before_content)
    if after_content is not None:
        record["after_sha256"] = _sha256(after_content)

    with open(pp_dir / "receipts.jsonl", "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
