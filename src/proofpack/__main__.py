"""CLI entry point for proofpack."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    from proofpack import __version__

    parser = argparse.ArgumentParser(
        prog="proofpack",
        description="Proof-carrying CI gate for AI agent changes.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"proofpack {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize a new proofpack session.")
    init_parser.add_argument("--title", default="", help="Work title.")
    init_parser.add_argument(
        "--scope", default="", help="Comma-separated glob paths for allowed scope."
    )

    # start
    start_parser = subparsers.add_parser("start", help="Start a proofpack run.")
    start_parser.add_argument(
        "--run-id", default="", dest="run_id", help="Explicit run ID (auto-generated if omitted)."
    )

    # stop
    subparsers.add_parser("stop", help="Finalize a proofpack run.")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify a proofpack run.")
    verify_parser.add_argument(
        "--mode",
        choices=["warn", "fail"],
        default="fail",
        help="Verification mode: warn (exit 0) or fail (exit 1) on violations.",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        from proofpack.commands.init import cmd_init
        return cmd_init(title=args.title, scope=args.scope)

    if args.command == "start":
        from proofpack.commands.start import cmd_start
        return cmd_start(run_id=args.run_id)

    if args.command == "stop":
        from proofpack.commands.stop import cmd_stop
        return cmd_stop()

    if args.command == "verify":
        from proofpack.commands.verify import cmd_verify
        return cmd_verify(mode=args.mode, json_output=args.json_output)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
