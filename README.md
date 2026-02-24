# Proofpack

Proof-carrying CI gate for AI agent changes.

**Status:** MVP (pre-code)

Proofpack is a format + CLI + CI gate that accompanies changes made by AI agents with verifiable proof:
contracts, receipts, and deterministic verification.

## Concepts

- **Contract** — what the agent promised to do
- **Receipts** — evidence of what was actually done (tool calls, tests, edits)
- **Verification** — deterministic CI replay that checks receipts against contract

## Install

```bash
pip install proofpack
```

## Usage

```bash
proofpack init        # Initialize proofpack in a repo
proofpack build       # Build proofpack artifact from agent session
proofpack verify      # Verify proofpack artifact
```

## Part of

[AI Engineering Lab](https://github.com/Real-AI-Engineering) — independent R&D lab building trust infrastructure for AI agents.

## License

MIT
