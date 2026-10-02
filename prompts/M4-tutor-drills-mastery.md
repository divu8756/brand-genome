# M4 — Tutor drills, mastery, spaced repetition

**Read first:** @CLAUDE.md @docs/SPEC.md (§6B, §6C) @docs/SPEC_ADDENDUM.md (D7, D8) @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
Five tutor modes that grade reasoning, not just answers, and that feed a mastery model plus SM-2 reviews.

## In scope
1. **Selector drill.**
   - Show a case prompt only.
   - The user picks a framework and justifies it.
   - Grade the choice against the case's `framework_tags` and `trigger_signals`, and grade the reasoning separately.
   - Feedback cites the framework card's trigger signals and when-not-to-use.
2. **Structure drill.**
   - The user types a structure (free text or an indented list). An LLM converts it into `IssueNode`.
   - Align it with `issue_tree_json` using semantic node matching.
   - Report missing branches, overlapping (non-MECE) branches, extra branches, and depth gaps.
   - Render both trees side by side.
3. **Compare mode.** Two frameworks, grounded and cited, with a "use X when / Y when" table.
4. **Guesstimate drill.**
   - Step-by-step and Socratic, one step at a time.
   - Datasheet numbers are shown only on request, and each request is logged as a hint.
   - Arithmetic is checked by a deterministic tool.
5. **Grading.**
   - Structured output: rubric dimensions relevant to the mode, 1–5 each, with evidence quotes from the user's answer.
   - Hints are logged.
6. **Mastery.** `app/mastery/` implements D7 as pure functions. Each graded attempt updates every touched framework, case type and sector.
7. **Review queue.**
   - SM-2 per item.
   - Show a "Due today" list.
   - The next drill is picked by the D7 adaptive rule.
8. **Revealed cases.** Drills avoid cases revealed in M3, unless I override.

## Out of scope
The interviewer and the full dashboard. A simple mastery table is enough for now.

## Tests & evals
- **Unit tests** for D7:
  - mastery update;
  - difficulty weights;
  - hint penalty;
  - SM-2 intervals over a scripted sequence.
- **Structure-alignment tests:** synthetic trees with known missing and overlapping branches.
- **`evals.run grader`:**
  - Consistency: 10 answers graded 3× each, report per-dimension standard deviation.
  - Calibration: correlation with **my** grades on 10 answers (I will provide `evals/gold/my_grades.jsonl`).

## Definition of done
- [ ] All 5 modes work end-to-end in both workspaces.
- [ ] Mastery visibly changes after drills (§11).
- [ ] Grader standard deviation ≤ 0.5 per dimension. If not, report it and propose a fix.
- [ ] `PROGRESS.md` is updated.
