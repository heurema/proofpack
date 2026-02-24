"""Schema models for proofpack: ContractV1, MetaV1, ReceiptEvent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContractV1:
    """Parsed representation of a proofpack contract (schema version 1)."""

    schema_version: int
    run_id: str
    work_title: str
    work_summary: str
    allowed_paths: list[str]
    forbidden_paths: list[str]
    acceptance_commands: list[str]
    acceptance_artifacts: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContractV1:
        work = raw["work"]
        assert isinstance(work, dict)
        scope = raw["scope"]
        assert isinstance(scope, dict)
        acceptance = raw["acceptance"]
        assert isinstance(acceptance, dict)
        return cls(
            schema_version=raw["schema_version"],
            run_id=raw["run_id"],
            work_title=work["title"],
            work_summary=work["summary"],
            allowed_paths=scope["allowed_paths"],
            forbidden_paths=scope["forbidden_paths"],
            acceptance_commands=acceptance["commands"],
            acceptance_artifacts=acceptance["artifacts"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "work": {
                "title": self.work_title,
                "summary": self.work_summary,
            },
            "scope": {
                "allowed_paths": self.allowed_paths,
                "forbidden_paths": self.forbidden_paths,
            },
            "acceptance": {
                "commands": self.acceptance_commands,
                "artifacts": self.acceptance_artifacts,
            },
        }


@dataclass(frozen=True)
class MetaV1:
    """Parsed representation of proofpack run metadata (schema version 1)."""

    schema_version: int
    run_id: str
    receipt_integrity: str
    vcs: str
    head_sha: str
    base_sha: str
    runtime_name: str
    runtime_version: str
    env_os: str
    env_ci: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MetaV1:
        repo = raw["repo"]
        assert isinstance(repo, dict)
        runtime = raw["runtime"]
        assert isinstance(runtime, dict)
        env = raw["env"]
        assert isinstance(env, dict)
        return cls(
            schema_version=raw["schema_version"],
            run_id=raw["run_id"],
            receipt_integrity=raw["receipt_integrity"],
            vcs=repo["vcs"],
            head_sha=repo["head_sha"],
            base_sha=repo["base_sha"],
            runtime_name=runtime["name"],
            runtime_version=runtime["version"],
            env_os=env["os"],
            env_ci=env["ci"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "receipt_integrity": self.receipt_integrity,
            "repo": {
                "vcs": self.vcs,
                "head_sha": self.head_sha,
                "base_sha": self.base_sha,
            },
            "runtime": {
                "name": self.runtime_name,
                "version": self.runtime_version,
            },
            "env": {
                "os": self.env_os,
                "ci": self.env_ci,
            },
        }


@dataclass(frozen=True)
class ReceiptEvent:
    """A single event line from a proofpack receipt JSONL file."""

    run_id: str
    t: str
    event: str
    tool: str | None
    # tool event fields
    input_sha256: str | None
    exit_code: int | None
    stdout_sha256: str | None
    stderr_sha256: str | None
    # edit event fields
    path: str | None
    before_sha256: str | None
    after_sha256: str | None

    @classmethod
    def from_json_line(cls, line: str) -> ReceiptEvent:
        raw: dict[str, Any] = json.loads(line)
        return cls(
            run_id=raw["run_id"],
            t=raw["t"],
            event=raw["event"],
            tool=raw.get("tool"),
            input_sha256=raw.get("input_sha256"),
            exit_code=raw.get("exit_code"),
            stdout_sha256=raw.get("stdout_sha256"),
            stderr_sha256=raw.get("stderr_sha256"),
            path=raw.get("path"),
            before_sha256=raw.get("before_sha256"),
            after_sha256=raw.get("after_sha256"),
        )

    def to_json_line(self) -> str:
        data: dict[str, Any] = {"run_id": self.run_id, "t": self.t, "event": self.event}
        if self.tool is not None:
            data["tool"] = self.tool
        if self.input_sha256 is not None:
            data["input_sha256"] = self.input_sha256
        if self.exit_code is not None:
            data["exit_code"] = self.exit_code
        if self.stdout_sha256 is not None:
            data["stdout_sha256"] = self.stdout_sha256
        if self.stderr_sha256 is not None:
            data["stderr_sha256"] = self.stderr_sha256
        if self.path is not None:
            data["path"] = self.path
        if self.before_sha256 is not None:
            data["before_sha256"] = self.before_sha256
        if self.after_sha256 is not None:
            data["after_sha256"] = self.after_sha256
        return json.dumps(data)
