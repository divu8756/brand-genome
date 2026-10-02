# CaseCoach — Claude Code Kit

## What's in here
| File | Where it goes in your repo | Purpose |
|---|---|---|
| `CLAUDE.md` | repo root | Loaded automatically in every Claude Code session. Rules, stack, layout, gotchas. Kept short on purpose. |
| `docs/SPEC_ADDENDUM.md` | `docs/` | Decisions that close the gaps in your build prompt. **Overrides SPEC.md where they conflict.** Each one is marked *proposed*; edit before M0. |
| `prompts/M0…M6*.md` | `prompts/` | One prompt per milestone. Each one is paste-ready. |

You also need to save **your original build prompt, unchanged, as `docs/SPEC.md`**. Every prompt refers to it by section number (§4, §6D, etc.).

## Setup (once)
1. `mkdir casecoach && cd casecoach && git init`
2. Copy in `CLAUDE.md`, `docs/`, `prompts/`, and save your spec as `docs/SPEC.md`.
3. Put both casebook PDFs **outside the repo**, e.g. `~/casecoach-fixtures/`. Add `FIXTURE_DIR=~/casecoach-fixtures` to `backend/.env` later. They must never be committed (see CLAUDE.md, Copyright).
4. Read `docs/SPEC_ADDENDUM.md` and change anything you disagree with *before* M0. It is much cheaper to change now.

## Running a milestone
1. Start a fresh session (`/clear`) so earlier context doesn't leak in.
2. Switch to **plan mode** (Shift+Tab until it shows plan mode).
3. Paste the milestone prompt, or type: `Run @prompts/M1a-ingestion-core.md`
4. Read the plan. Push back on anything vague. Approve it.
5. When it reports done, **check the Definition of Done yourself**: run the commands, open the eval report.
6. `git commit` and `git tag m1a`, then move on.

## Order
M0 → M1a → M1b → M2 → M3 → M4 → M5 → M6

M1 is split in two because IIMA parsing (unlabelled transcripts, issue-tree vision) is the riskiest work in the project and deserves its own session.

## Your manual work (Claude Code can't do this for you)
- **M0:** hand-label the gold set using the CLI it builds. Budget roughly 3–4 hours.
- **M2:** write about 30 test questions per workspace with expected pages.
- **M4/M5:** grade 10 answers or transcripts yourself to calibrate the AI grader.

These hand-made sets *are* your eval story for interviews. Don't skip them.

## When it drifts
Say: "Stop. Re-read @CLAUDE.md and @prompts/<current>.md. List what you did that's out of scope." Then revert or fix.
