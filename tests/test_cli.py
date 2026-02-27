"""Tests for proofpack CLI."""
import subprocess
import sys


def test_cli_help() -> None:
    result = subprocess.run(  # noqa: E501
        [sys.executable, "-m", "proofpack", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "proofpack" in result.stdout.lower()


def test_cli_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_cli_init_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack", "init", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0


def test_cli_verify_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack", "verify", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "--mode" in result.stdout


def test_cli_no_command_returns_nonzero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack"], capture_output=True, text=True
    )
    assert result.returncode == 2


def test_cli_status_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack", "status", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "session" in result.stdout.lower() or "status" in result.stdout.lower()


def test_cli_verify_dry_run_in_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "proofpack", "verify", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--dry-run" in result.stdout
