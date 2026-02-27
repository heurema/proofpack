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

## See Also

Other [heurema](https://github.com/heurema) projects:

- **[sigil](https://github.com/heurema/sigil)** — risk-adaptive development pipeline with adversarial code review
- **[herald](https://github.com/heurema/herald)** — daily curated news digest plugin for Claude Code
- **[teams-field-guide](https://github.com/heurema/teams-field-guide)** — comprehensive guide to Claude Code multi-agent teams
- **[arbiter](https://github.com/heurema/arbiter)** — multi-AI orchestrator (Codex + Gemini)

## License

MIT
