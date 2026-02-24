"""proofpack init command — creates .proofpack/ with contract template."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def cmd_init(title: str, scope: str) -> int:
    pp_dir = Path(".proofpack")

    if pp_dir.exists():
        print("Error: .proofpack/ already exists.", file=sys.stderr)
        return 1

    allowed_paths = [p.strip() for p in scope.split(",") if p.strip()] if scope else []

    contract: dict[str, Any] = {
        "schema_version": 1,
        "run_id": "",
        "work": {
            "title": title,
            "summary": "",
        },
        "scope": {
            "allowed_paths": allowed_paths,
            "forbidden_paths": [],
        },
        "acceptance": {
            "commands": [],
            "artifacts": [],
        },
    }

    pp_dir.mkdir()
    contract_path = pp_dir / "contract.json"
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=False) + "\n")

    print(f"Initialized .proofpack/ with contract.json (title={title!r})")
    return 0
