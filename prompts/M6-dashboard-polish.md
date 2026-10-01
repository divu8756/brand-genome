# M6 — Dashboard, company-style rounds, primers, polish, portfolio

**Read first:** @CLAUDE.md @docs/SPEC.md (§6C, §6D company style, §8, §12) @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
A finished, deployable product with a portfolio-ready write-up.

## In scope
1. **Dashboard.**
   - Mastery heatmap (framework, case type and sector; per workspace).
   - Rubric trend per dimension.
   - Top 3 weak areas, each with a "do this next" button that launches the drill.
   - Streak.
   - Due reviews.
   - Session history with full transcripts and cost.
2. **Company-style PM rounds.**
   - Build a style profile per company from interview-experience chunks: round types, typical questions, emphasis, pace. Cite the profile.
   - The interviewer uses it as a persona layer only. It never invents questions and attributes them to the source.
3. **Industry primers.** "Read the [Sector] primer first" appears on case setup, the case detail page and feedback.
4. **Polish.**
   - Empty states, error states and loading skeletons.
   - Accessibility pass: contrast, focus and labels.
   - Mobile pass on every screen.
5. **Deploy.**
   - Vercel + Render + Supabase production setup.
   - Env checklist.
   - Worker deployment decision documented (Mac or Render worker).
6. **Docs.**
   - `README.md`: setup, environment variables, deploy steps, the AGPL note, and the copyright policy.
   - `docs/CASE_STUDY.md` for my portfolio:
     - problem;
     - users (me);
     - architecture diagram (Mermaid);
     - key decisions (link to the ADDENDUM);
     - **eval results tables from every milestone**;
     - cost per session;
     - what I'd do in v2 (voice, study-plan generator).

## Tests
- Playwright smoke test: login → drill → interview → dashboard reflects it.
- Every eval suite re-run on the final build; results go into CASE_STUDY.md.

## Definition of done
- [ ] All of §10 re-verified on the production deployment.
- [ ] Weakest areas show on the dashboard (§10).
- [ ] CASE_STUDY.md is complete with real numbers.
- [ ] Tagged `v1.0`.
