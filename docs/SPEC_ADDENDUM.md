# SPEC ADDENDUM — binding decisions

These decisions override `SPEC.md` where they conflict. All decisions below are **accepted** (2026-10-02). Change one only by editing it here and logging the change in `docs/DECISIONS.md`.

## D1. Gold set before pipeline (new milestone M0) — status: accepted
§11's acceptance criteria need ground truth, so it gets built first. Labels reference content and never copy text (Hard rule 1).

| File | Content |
|---|---|
| `evals/gold/iima_index.csv` | The 108 cases, 25 guesstimates and 27 Panorama reports, auto-extracted from the index table and hand-verified: `kind, s_no, name, case_type, sector, difficulty, printed_page` |
| `evals/gold/speaker/*.jsonl` | 10 IIMA cases, one line per turn: `{doc, pdf_page, turn_index, bbox, speaker}` |
| `evals/gold/issue_trees/*.json` | 10 hand-built issue trees (node labels may be paraphrased) |
| `evals/gold/xlri_inventory.json` | Expected frameworks, case types, teardowns, interview experiences, and the page offset |

## D2. Ingestion execution — status: accepted
- A Postgres `jobs` table plus a worker process (`SELECT … FOR UPDATE SKIP LOCKED`). No Redis.
- Progress is checkpointed **per page** in `page_tasks`, so a killed job resumes where it stopped.
- Vision pages run in parallel with a concurrency limit (default 6) and exponential backoff on 429s.
- The worker can run on a Mac (fine for a single user) or as a Render background worker. The web service never runs ingestion.

## D3. Retrieval — status: accepted
1. **Lexical:** Postgres full-text search (a weighted `tsvector`, title A / body B). This approximates BM25. Revisit `pg_search` only if the retrieval eval shows lexical misses.
2. **Vector:** pgvector HNSW with cosine distance.
3. **Fusion:** Reciprocal Rank Fusion (k = 60) over the top 50 from each.
4. **Rerank:** top 30 → 8 via the provider `rerank()`, which defaults to an LLM judge and can be switched off by config.
5. **Parent expansion:** return parent sections, de-duplicated.
6. **Filters:** workspace, section_type, case_type, difficulty, applied as SQL WHERE clauses before ranking. This deliberately overrides §7's order (rerank → filter): filtering first keeps workspace isolation in SQL (Hard rule 3) and stops filtered-out chunks from using up rerank slots.

## D4. Embeddings — status: accepted
- Gemini embedding model via the provider, truncated to 1536 dims and L2-normalised.
- `embedding_model` and `embedding_dim` are stored per chunk. A model change triggers a `reembed` job.

## D5. Interview persistence — status: accepted
- LangGraph `PostgresSaver`, with `thread_id = session_id`.
- Invented facts go into the `session_invented_facts` table *and* the graph state. They are always read back before answering, which makes them consistent by construction.

## D6. Interviewer context isolation — status: accepted
| Node | Sees |
|---|---|
| interviewer | prompt, hidden_facts, revealed exhibits, current stage, invented facts |
| grader | the transcript plus `evaluator_observations` (after the session ends) |
| feedback | everything, including `issue_tree_json` and `model_recommendation` |

- Arithmetic is verified by a deterministic Python tool, not by the LLM.
- Extraction attempts are refused in character and logged as `extraction_attempt`.

## D7. Mastery and spaced repetition — status: accepted
- **Performance:** `perf` (0–100) = mean rubric score / 5 × 100 − 10 per hint, floored at 0.
- **Difficulty weight:** `w` = {1: 0.6, 2: 0.8, 3: 1.0, 4: 1.2, 5: 1.4}.
- **Mastery update:** `mastery ← mastery + 0.3·w·(perf − mastery)`, clamped to 0–100. Starts at 0.
  - This applies to every framework, case type and sector the item touches.
- **Confidence:** `1 − exp(−attempts/3)`.
- **SM-2 quality:** `q = clamp(round(perf/20), 0, 5)`. Standard SM-2 then applies: q < 3 resets the interval to 1 day; EF starts at 2.5 and has a floor of 1.3.
- **Adaptive difficulty:** the next item's difficulty is `clamp(round(mastery/20)+1, 1, 5)`. Ties go to the most overdue review.
- Formulas live in `app/mastery/` as pure functions with unit tests.

## D8. Evals are deliverables — status: accepted
- Every milestone ships an eval suite runnable via `python -m evals.run <suite>`.
- Each run writes a dated markdown report to `evals/reports/` and logs to Langfuse datasets.
- Thresholds come from §11. A milestone may finish below threshold only if the gap is reported with numbers.

## D9. Auth — status: accepted
- Supabase Auth (magic link) with **one allow-listed email**.
- The backend verifies the JWT on every route.
- RLS denies anon access on all tables.

## D10. Performance targets — status: accepted
- **Tutor time-to-first-token:** p50 < 3 s, measured on a **warm** backend. Cold start on free Render is documented, not counted.
- **Ingestion:** a 400-page PDF finishes in under 10 minutes on the worker with vision concurrency 6.

## D11. Providers — status: accepted
- The `Provider` protocol: `chat()`, `chat_stream()`, `structured()`, `vision_structured()`, `embed()`, `rerank()`.
- Gemini is implemented fully. Claude and OpenAI adapters pass the same contract tests, which are skipped without keys.

## D12. Copyright-safe repo — status: accepted
- `.gitignore`: `*.pdf`, `fixtures/`, `evals/reports/*_text*`, and page renders.
- CI (GitHub Actions) runs only synthetic-fixture tests. Real-book evals run locally.
- §13's "ingestion test fixtures and ingestion-report snapshots for both books" means: synthetic fixtures generated in code, plus committed snapshots that contain only counts, labels and page references (no extracted text and no page images).
