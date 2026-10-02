# M5 — 1:1 Case Interviewer agent

**Read first:** @CLAUDE.md (Hard rule 4) @docs/SPEC.md (§6D, §11, §12) @docs/SPEC_ADDENDUM.md (D5, D6, D7, D8) @docs/PROGRESS.md

Use plan mode. Include the LangGraph diagram (Mermaid) in the plan. Wait for approval.

## Goal
A realistic, leak-proof, persistent text interviewer that ends in a rubric-scored, cited feedback report.

## In scope
1. **Setup screen.** Workspace, case type (or random), sector, difficulty, and format:
   - interviewer-led by default for Consulting;
   - candidate-led by default for PM.

   Also: optional company style (PM, a placeholder until M6) and a timer. Unrevealed cases are chosen first.
2. **LangGraph graph.**
   - **Nodes:** prompt → clarifying → structuring → analysis_math → brainstorm_prioritise → synthesis → grade → feedback.
   - **Router:** stage transitions follow candidate signals plus interviewer judgement. Candidate-led mode lets the user drive transitions.
   - **Persistence:** PostgresSaver, `thread_id = session_id`. Refreshing the page resumes the interview.
3. **Context isolation (D6).** This is enforced in code: the interviewer node's state slice excludes the tree and the recommendation. Add a test that inspects the prompt actually sent to the provider.
4. **Clarifying questions.**
   - Answer only from `hidden_facts`.
   - If a fact is missing: invent a plausible value, store it in `session_invented_facts`, and read it back before every later answer.
5. **Exhibits** are revealed only on request. Arithmetic is verified by a deterministic tool; on an error, the interviewer probes ("walk me through that").
6. **Interviewer behaviour.**
   - Neutral tone.
   - Probes on weak logic ("why that segment?", "is that MECE?").
   - Steers toward the root cause.
   - Hints only when asked; each hint is logged and penalised per D7.
   - Extraction attempts are refused in character and logged.
   - Gibberish → a clarifying redirect.
7. **Abandon handling.** A session left mid-way is marked `abandoned`. The user can resume or end it; ending it produces a partial feedback report covering only the completed stages.
8. **Grade node.**
   - Uses the §6D rubric, 1–5 per dimension, with evidence quotes from user turns.
   - The empathy dimension applies to PM, the hypothesis dimension to Consulting.
   - Uses `evaluator_observations` as anchors.
9. **Feedback report.** It includes:
   - scores;
   - top 3 fixes;
   - where the framework choice helped or hurt;
   - the source issue tree, rendered, plus the recommendation, both cited;
   - the linked Panorama primer;
   - the next recommended drill (from mastery).

   Mastery and SM-2 are updated.
10. **Mobile-first chat UI** with a timer, a stage indicator, a hint button and an exhibit drawer.
11. **Cost.** Cost per session is logged and shown on the report.

## Out of scope
- the dashboard (M6);
- company-style personas (M6);
- voice (v2).

## Tests & evals (`evals.run interviewer`)
- **Leak red-team:** 20 scripted extraction attempts. A judge checks that responses before the feedback stage don't overlap issue-tree node labels or the recommendation. Target: **0 leaks**.
- **Consistency:** ask about the same missing fact 3 times across turns → the same value every time.
- **Persistence:** kill the backend mid-interview, reload, and confirm the state is intact.
- **Calibration:** correlation with my grades on 5 transcripts (`evals/gold/my_interview_grades.jsonl`).
- **Simulated candidates:** an LLM plays a strong and a weak candidate on 3 cases. The strong one should score higher on every dimension.

## Definition of done
- [ ] §11 interviewer items pass: no early leak, consistent invented facts.
- [ ] A full interview is playable on a phone.
- [ ] The eval report is committed (with no source text), and `PROGRESS.md` is updated.
