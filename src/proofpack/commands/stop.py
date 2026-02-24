"""proofpack stop command — finalizes meta.json with head_sha."""

from __future__ import annotations

import json
import subprocess
import sys
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


def cmd_stop() -> int:
    pp_dir = Path(".proofpack")
    meta_path = pp_dir / "meta.json"

    if not meta_path.exists():
        print(
            "Error: .proofpack/meta.json not found. Run 'proofpack start' first.", file=sys.stderr
        )
        return 1

    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        print("Error: .proofpack/meta.json is not valid JSON.", file=sys.stderr)
        return 1

    if not isinstance(meta, dict):
        print("Error: .proofpack/meta.json is not a JSON object.", file=sys.stderr)
        return 1

    head_sha = _get_git_head_sha()

    if "repo" not in meta or not isinstance(meta.get("repo"), dict):
        meta["repo"] = {}
    meta["repo"]["head_sha"] = head_sha

    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=False) + "\n")

    run_id = meta.get("run_id", "")
    print(f"Finalized run {run_id!r}. head_sha={head_sha!r}")
    return 0
