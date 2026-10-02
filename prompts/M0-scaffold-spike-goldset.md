# M0 — Scaffold, risk spike, gold set

**Read first:** @CLAUDE.md @docs/SPEC.md (§2, §4, §11) @docs/SPEC_ADDENDUM.md (D1, D2, D9, D11, D12)

Use plan mode. Your plan must:
1. restate the goal;
2. list the risks;
3. list open questions for me;
4. list the files you will create.

Wait for my approval before writing code.

## Goal
1. A runnable empty skeleton.
2. Evidence on the two riskiest parsing problems.
3. The tooling I need to hand-label the gold set.

## In scope

### 1. Scaffold
Create the repo layout from CLAUDE.md, plus:
- **Backend:**
  - FastAPI `/health`;
  - pydantic-settings config;
  - Alembic with a first migration that enables `vector` and creates `workspaces` (seeded with "consulting" and "pm"), `documents`, `jobs` and `page_tasks`.
- **Providers:** the `Provider` protocol (D11) plus the Gemini adapter, with `embed` and `vision_structured` working. Claude and OpenAI adapters are stubs that raise NotImplementedError.
- **Langfuse:** a tracing wrapper applied inside the provider layer.
- **Frontend:**
  - Next.js app with a Supabase magic-link login;
  - an allow-listed email (D9);
  - an empty two-tab shell (Consulting | Product Management).
- **Repo hygiene:**
  - `.env.example` and the `.gitignore` from D12;
  - a GitHub Actions workflow running ruff, pytest, and pnpm lint;
  - `docs/PROGRESS.md` and `docs/DECISIONS.md`.

### 2. Spike
Write throwaway-quality scripts in `backend/spikes/`, reading from `$FIXTURE_DIR`. The output is `docs/SPIKE_REPORT.md`.
- **a. IIMA transcript turns.** Check 5 case transcript pages. Use `page.get_drawings()` and text-block bboxes to find whether rectangles, fills or vertical gaps delimit turns.
  - Report the evidence per page.
  - Recommend one of: geometric, geometric + LLM, or LLM-only attribution.
- **b. Issue trees.** On 3 Approach pages:
  - render at 2× resolution;
  - extract the tree with `vision_structured` into this schema: `IssueNode{label:str, children:list[IssueNode]}`;
  - write the JSON side-by-side with plain text extraction so I can judge it.
- **c. Page offsets.** Prototype printed-page offset detection: find page-number text in the header/footer zones and take the mode of `printed − pdf`. Run it on both books. Expected results: XLRI = 4, IIMA = 0.
- **d. IIMA index.** Extract the index table (pp. 7–10) into `evals/gold/iima_index.csv` (D1 schema) for me to verify.
- **e. Noise.** Measure repeated text/bbox pairs across pages and image size/position stats, and propose noise filter thresholds.

### 3. Labelling CLI
`uv run python -m evals.label speaker <doc> <pdf_page>`:
- shows text blocks in reading order with indices;
- I type I/C for each block;
- the result is written to `evals/gold/speaker/<case>.jsonl` by reference (no text).

Add a matching `issue-tree` command that opens a JSON template for me to fill in.

## Out of scope
- the real ingestion pipeline;
- chunking;
- the retrieval UI beyond the shell.

## Definition of done
- [ ] `uv run pytest`, ruff and `pnpm lint` all pass locally and in CI.
- [ ] Login works with my email and rejects any other email.
- [ ] `docs/SPIKE_REPORT.md` has evidence and a recommendation for each of a–e.
- [ ] `iima_index.csv` is generated, and its row counts are reported against 108 / 25 / 27.
- [ ] The labelling CLI works on one page end-to-end.
- [ ] No PDF text or images are tracked by git (`git ls-files` check shown).

## Report back
- Spike recommendations.
- Anything in SPEC or ADDENDUM the spike contradicts.
- **Then stop.** I will label the gold set before M1a.
