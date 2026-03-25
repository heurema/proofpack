```
                            ____                 __
    ____  _________  ____  / __/___  ____ ______/ /__
   / __ \/ ___/ __ \/ __ \/ /_/ __ \/ __ `/ ___/ //_/
  / /_/ / /  / /_/ / /_/ / __/ /_/ / /_/ / /__/ ,<
 / .___/_/   \____/\____/_/ / .___/\__,_/\___/_/|_|
/_/                        /_/
```

**Proof-carrying CI gate for AI agent changes.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Format + CLI + CI gate. Contracts, receipts, and deterministic verification.

**Status:** MVP (pre-code)

---

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

- **[signum](https://github.com/heurema/signum)** — risk-adaptive development pipeline with adversarial code review
- **[herald](https://github.com/heurema/herald)** — daily curated news digest plugin for Claude Code
- **[teams-field-guide](https://github.com/heurema/teams-field-guide)** — comprehensive guide to Claude Code multi-agent teams
- **[arbiter](https://github.com/heurema/arbiter)** — multi-AI orchestrator (Codex + Gemini)

## License

MIT
