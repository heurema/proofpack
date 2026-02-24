"""proofpack diff command — shows git diff since session start."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def cmd_diff(full: bool = False) -> int:
    pp_dir = Path(".proofpack")

    if not pp_dir.exists():
        print("Error: No proofpack session found. Run 'proofpack init' first.", file=sys.stderr)
        return 1

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

    repo = meta.get("repo", {})
    base_sha: str = repo.get("base_sha", "unknown")
    head_sha: str = repo.get("head_sha", "")

    if base_sha == "unknown":
        print(
            "Error: base_sha is 'unknown' — cannot compute diff (git was unavailable at session start).",
            file=sys.stderr,
        )
        return 1

    # Build git diff command
    if full:
        cmd = ["git", "diff", base_sha]
    else:
        cmd = ["git", "diff", "--stat", base_sha]

    if head_sha:
        cmd.append(head_sha)
    else:
        cmd.append("HEAD")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        print(f"Error: failed to run git: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(f"Error: git diff failed: {result.stderr.strip()}", file=sys.stderr)
        return 1

    output = result.stdout.strip()
    if not output:
        print("No changes since session start.")
    else:
        print(output)

    return 0
