"""Proofpack verification checks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    severity: str = "FAIL"  # FAIL or WARN
