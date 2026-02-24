"""Hook entry point — reads Claude Code hook JSON from stdin, writes receipt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from proofpack.hooks import append_receipt


def main() -> int:
    pp_dir = Path.cwd() / ".proofpack" if len(sys.argv) < 2 else Path(sys.argv[1])
    if not pp_dir.is_dir():
        return 0  # fail-open
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return 0  # fail-open
    tool_name = payload.get("tool_name", "unknown")
    tool_input = payload.get("tool_input", {})
    tool_output = payload.get("tool_output", "")
    exit_code = payload.get("exit_code")
    try:
        if tool_name in ("Bash",):
            append_receipt(pp_dir=pp_dir, tool=tool_name, event="tool", exit_code=exit_code,
                           input_data=json.dumps(tool_input) if tool_input else None,
                           stdout_data=str(tool_output) if tool_output else None,
                           stderr_data=payload.get("stderr", ""))
        elif tool_name in ("Edit", "Write"):
            # NOTE: before/after content hashes not available from hook payload.
            # Claude Code hooks only provide tool_input (file_path, old_string, new_string
            # for Edit) but not the full file before/after state. Path-only receipt.
            append_receipt(pp_dir=pp_dir, tool=tool_name,
                           event="edit" if tool_name == "Edit" else "write",
                           path=tool_input.get("file_path", ""))
        elif tool_name in ("Read", "Grep", "Glob"):
            append_receipt(pp_dir=pp_dir, tool=tool_name, event="read",
                           path=tool_input.get("file_path", tool_input.get("path", "")))
    except Exception:
        pass  # fail-open: never crash the hook
    return 0


if __name__ == "__main__":
    sys.exit(main())
