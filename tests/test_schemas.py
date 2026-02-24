"""Tests for proofpack schema models."""

from proofpack.schemas import ContractV1, MetaV1, ReceiptEvent


def test_contract_from_dict() -> None:
    raw = {
        "schema_version": 1,
        "run_id": "2026-02-24T12-00-00Z__local",
        "work": {"title": "Test task", "summary": "Do something"},
        "scope": {
            "allowed_paths": ["src/**"],
            "forbidden_paths": [".github/**"],
        },
        "acceptance": {
            "commands": ["pytest -q"],
            "artifacts": [],
        },
    }
    c = ContractV1.from_dict(raw)
    assert c.schema_version == 1
    assert c.run_id == "2026-02-24T12-00-00Z__local"
    assert c.work_title == "Test task"
    assert c.allowed_paths == ["src/**"]
    assert c.forbidden_paths == [".github/**"]
    assert c.acceptance_commands == ["pytest -q"]


def test_contract_to_dict_roundtrip() -> None:
    raw = {
        "schema_version": 1,
        "run_id": "run1",
        "work": {"title": "T", "summary": "S"},
        "scope": {"allowed_paths": ["src/**"], "forbidden_paths": []},
        "acceptance": {"commands": [], "artifacts": []},
    }
    c = ContractV1.from_dict(raw)
    assert c.to_dict() == raw


def test_contract_missing_field_raises() -> None:
    import pytest
    with pytest.raises(KeyError):
        ContractV1.from_dict({"schema_version": 1})


def test_meta_from_dict() -> None:
    raw = {
        "schema_version": 1,
        "run_id": "run1",
        "receipt_integrity": "full",
        "repo": {"vcs": "git", "head_sha": "abc", "base_sha": "def"},
        "runtime": {"name": "claude-code", "version": "1.0"},
        "env": {"os": "darwin", "ci": False},
    }
    m = MetaV1.from_dict(raw)
    assert m.run_id == "run1"
    assert m.receipt_integrity == "full"
    assert m.head_sha == "abc"
    assert m.base_sha == "def"


def test_receipt_event_from_json_line() -> None:
    line = (
        '{"run_id":"run1","t":"2026-02-24T12:00:01Z",'
        '"event":"tool","tool":"Bash","input_sha256":"a1b2",'
        '"exit_code":0,"stdout_sha256":"c3d4","stderr_sha256":"e5f6"}'
    )
    r = ReceiptEvent.from_json_line(line)
    assert r.run_id == "run1"
    assert r.event == "tool"
    assert r.tool == "Bash"
    assert r.exit_code == 0


def test_receipt_event_edit() -> None:
    line = (
        '{"run_id":"run1","t":"2026-02-24T12:00:10Z",'
        '"event":"edit","tool":"Edit","path":"src/foo.py",'
        '"before_sha256":"1a2b","after_sha256":"3c4d"}'
    )
    r = ReceiptEvent.from_json_line(line)
    assert r.event == "edit"
    assert r.path == "src/foo.py"
