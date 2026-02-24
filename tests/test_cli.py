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
