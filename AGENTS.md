# Project: M&A Trend Analysis Agent

> This file is read by **OpenAI Codex CLI** automatically.
> The mirror file for Claude Code is `CLAUDE.md` — keep both in sync.

## Collaboration Mode: Codex CLI ↔ Claude Code

This project is worked on by **two AI agents** sharing the same working directory:
- **Codex CLI (you)**
- **Claude Code**

Goal: cross-verify each other's work to improve correctness and complementarity.

### Default Role Split
- **Codex CLI (you)**: algorithm implementation, optimization, debugging, alternative implementations, low-level fixes
- **Claude Code**: architecture, refactoring, documentation, Korean reports, tests, large-context tasks

> Roles are not fixed. The user can override at any time.

### Collaboration Protocol

All handoffs happen through the `.collab/` directory.

#### 1. Handoff Board (`.collab/handoff.md`)
A shared bulletin board both agents read & write.
- **Always prepend new entries to the top** (newest first)
- Entry format:
  ```
  ## [YYYY-MM-DD HH:MM] FROM: codex TO: claude | TYPE: review-request
  ### Target: <file/lines>
  ### Request: <what you want reviewed/built/fixed>
  ### Context: <background, constraints>
  ### Response: (filled in by the other agent)
  ---
  ```
- TYPE values: `review-request`, `review-response`, `task-handoff`, `question`, `decision-log`

#### 2. Required at Task Start
Before doing any work:
1. Read the top 5 entries of `.collab/handoff.md` to see Claude's recent activity
2. Run `git log -n 5 <file>` on files you plan to edit — check if Claude touched them recently
3. If conflict risk, ask the user first

#### 3. Required at Task End
After any meaningful change (code edits, new files, refactors):
1. Prepend a summary + verification request to `.collab/handoff.md`
2. Suggest to the user: "want Claude to review this?"
3. Commit & push immediately (user does not need to ask separately)

#### 4. Review Request Pattern
Code you write should ideally be **reviewed by Claude**:
- Potential bugs / edge cases
- Performance / readability / better patterns
- Missing test cases

When Claude requests a review from you, evaluate objectively — do not rubber-stamp; provide reasoning.

### Collaboration Directory
```
.collab/
├── README.md        # human-readable rules
├── handoff.md       # bidirectional handoff board (REQUIRED)
└── decisions.md     # log of decisions both agents agreed on
```

### Notes
- `.collab/` files may be touched by both agents — `git pull` before writing
- Never edit the same source file Claude is currently working on (check handoff.md "in-progress" markers)
- If the user explicitly says "Codex only" or "Claude only", skip the collaboration steps

### Project-Specific
- Working directory: `d:/015. M&A/my-agent`
- Primary language: Python (agent.py), HTML reports
- Reports output to `reports/` (Korean filenames OK)
- Main branch: `main` — push immediately after edits
