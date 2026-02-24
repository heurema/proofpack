"""proofpack status command — displays current session state."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def cmd_status() -> int:
    pp_dir = Path(".proofpack")

    if not pp_dir.exists():
        print("No proofpack session found. Run 'proofpack init' first.")
        return 0

    # Read contract.json (project metadata)
    title = ""
    scope: list[str] = []
    contract_path = pp_dir / "contract.json"
    if contract_path.exists():
        try:
            contract = json.loads(contract_path.read_text())
            title = contract.get("work", {}).get("title", "")
            scope = contract.get("scope", {}).get("allowed_paths", [])
        except (json.JSONDecodeError, AttributeError):
            pass

    # Read meta.json (session state)
    meta_path = pp_dir / "meta.json"
    if not meta_path.exists():
        print(f"Session: initialized (no run started)")
        if title:
            print(f"Title:   {title}")
        if scope:
            print(f"Scope:   {', '.join(scope)}")
        return 0

    try:
        meta = json.loads(meta_path.read_text())
    except (json.JSONDecodeError, AttributeError):
        print("Error: .proofpack/meta.json is not valid JSON.", file=sys.stderr)
        print("Session: initialized (meta.json corrupt)")
        return 0

    run_id = meta.get("run_id", "unknown")
    integrity = meta.get("receipt_integrity", "unknown")
    head_sha = meta.get("repo", {}).get("head_sha", "")
    state = "finalized" if head_sha and head_sha != "unknown" else "active"

    print(f"Session: {state}")
    print(f"Run ID:  {run_id}")
    if title:
        print(f"Title:   {title}")
    if scope:
        print(f"Scope:   {', '.join(scope)}")
    print(f"Integrity: {integrity}")
    if head_sha:
        print(f"Head SHA:  {head_sha}")

    return 0
