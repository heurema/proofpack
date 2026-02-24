"""proofpack start command — creates meta.json and empty receipts.jsonl."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _get_git_head_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        pass
    return "unknown"


def cmd_start(run_id: str) -> int:
    pp_dir = Path(".proofpack")

    if not pp_dir.exists():
        print("Error: .proofpack/ not found. Run 'proofpack init' first.", file=sys.stderr)
        return 1

    if not run_id:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{ts}__local"

    base_sha = _get_git_head_sha()

    meta: dict[object, object] = {
        "schema_version": 1,
        "run_id": run_id,
        "receipt_integrity": "full",
        "repo": {
            "vcs": "git",
            "base_sha": base_sha,
            "head_sha": "",
        },
        "runtime": {
            "name": "claude-code",
            "version": "1.0",
        },
        "env": {
            "os": platform.system().lower(),
            "ci": False,
        },
    }

    (pp_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=False) + "\n")
    (pp_dir / "receipts.jsonl").write_text("")

    contract_path = pp_dir / "contract.json"
    if contract_path.exists():
        contract = json.loads(contract_path.read_text())
        contract["run_id"] = run_id
        contract_path.write_text(json.dumps(contract, indent=2, sort_keys=False) + "\n")

    print(f"Started run {run_id!r}. Created meta.json and receipts.jsonl.")
    return 0
