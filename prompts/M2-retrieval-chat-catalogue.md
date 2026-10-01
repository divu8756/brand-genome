# M2 — Grounded chat + framework catalogue

**Read first:** @CLAUDE.md @docs/SPEC.md (§5 Framework, §6B Explain, §7, §10) @docs/SPEC_ADDENDUM.md (D3, D8, D10) @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
Grounded, cited, workspace-isolated answers that stream in under 3 s, plus an auto-built framework catalogue per workspace.

## In scope
1. **Retrieval service** (`app/retrieval/`), implementing D3 exactly:
   - lexical search + vector search → RRF → rerank → parent expansion;
   - SQL filters;
   - a `cross_reference` flag.
   - It returns `Evidence{chunk_id, doc_title, printed_page, section_type, text, score}`.
2. **Answer chain.**
   - Stream over SSE.
   - Every claim cites `[Book, p. X]`. Short quotes only.
   - If the evidence is insufficient, reply with "Not in your casebooks" and optionally add general knowledge labelled "Not from your casebooks".
   - If the two books disagree, show both and cite both.
3. **Framework catalogue builder.** Inputs are `frameworks_raw`, framework tags from cases, and the cheat sheet.
   - Merge aliases into one record.
   - Fill these fields: purpose, steps, when_to_use, trigger_signals, when_not_to_use, alternatives, common_mistakes, related, source_chunks.
   - **Provenance per field:** casebook if supported by a cited chunk, otherwise `ai_generated`.
   - Link 2–3 cited example cases per framework, across books where relevant.
4. **API:**
   - `POST /chat` (stream);
   - `GET /frameworks?workspace=`;
   - `GET /frameworks/{id}`.
5. **Minimal UI:**
   - a chat panel per workspace tab;
   - clickable citations (a signed URL opens the page);
   - Framework Card view with AI-generated badges.

## Out of scope
Drills, mastery, the library UI and the interviewer.

## Tests & evals
I will write `evals/gold/retrieval_{consulting,pm}.jsonl` (about 30 Qs each, with expected printed pages). You build the runner.

- **retrieval:** recall@8 and MRR for lexical-only, vector-only, and hybrid ± rerank. This ablation table goes in the report.
- **refusal:** 15 out-of-corpus questions → 100% "Not in your casebooks".
- **isolation:** a SQL-level test showing that 50 Consulting queries return 0 PM chunks with cross-reference off (and vice versa), plus a test that the flag allows it.
- **citation faithfulness:** an LLM judge checks that the cited page supports the claim, on 30 answers. I'll spot-check 10.
- **latency:** time-to-first-token p50/p95 over 20 warm requests.

## Definition of done
- [ ] §10 out-of-corpus and isolation items pass.
- [ ] The ablation table shows hybrid ≥ the best single method, or explains why not.
- [ ] TTFT p50 < 3 s warm (D10).
- [ ] Both catalogues are built. Counts and AI-generated field ratios are reported.
- [ ] `PROGRESS.md` is updated.
