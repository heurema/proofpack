"""CLI entry point for proofpack."""

from __future__ import annotations

import sys

import click

from proofpack import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="proofpack")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Proof-carrying CI gate for AI agent changes."""
    if ctx.invoked_subcommand is None:
        ctx.fail("Missing command.")


@cli.command()
@click.option("--title", default="", help="Work title.")
@click.option("--scope", default="", help="Comma-separated glob paths for allowed scope.")
def init(title: str, scope: str) -> None:
    """Initialize a new proofpack session."""
    from proofpack.commands.init import cmd_init

    sys.exit(cmd_init(title=title, scope=scope))


@cli.command()
@click.option("--run-id", "run_id", default="", help="Explicit run ID (auto-generated if omitted).")
def start(run_id: str) -> None:
    """Start a proofpack run."""
    from proofpack.commands.start import cmd_start

    sys.exit(cmd_start(run_id=run_id))


@cli.command()
def stop() -> None:
    """Finalize a proofpack run."""
    from proofpack.commands.stop import cmd_stop

    sys.exit(cmd_stop())


@cli.command()
@click.option("--mode", type=click.Choice(["warn", "fail"]), default="fail",
              help="Verification mode: warn (exit 0) or fail (exit 1) on violations.")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON.")
def verify(mode: str, json_output: bool) -> None:
    """Verify a proofpack run."""
    from proofpack.commands.verify import cmd_verify

    sys.exit(cmd_verify(mode=mode, json_output=json_output))


@cli.command()
def status() -> None:
    """Display current session state."""
    from proofpack.commands.status import cmd_status

    sys.exit(cmd_status())


@cli.command()
@click.option("--full", is_flag=True, default=False, help="Show full unified diff instead of stat summary.")
def diff(full: bool) -> None:
    """Show git diff since session start."""
    from proofpack.commands.diff import cmd_diff

    sys.exit(cmd_diff(full=full))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
