# CaseCoach

A private, single-user web app that ingests consulting and PM casebooks and teaches framework selection. It runs drills, tracks mastery, and acts as a 1:1 case interviewer. It is also an AI PM portfolio piece, so architecture, evals and observability are first-class.

**Sources of truth**
- `docs/SPEC.md`: the product spec.
- `docs/SPEC_ADDENDUM.md`: binding decisions. **It wins on conflict.**
- `docs/PROGRESS.md`: the current milestone, what's done, and known gaps.
- `docs/DECISIONS.md`: log every assumption or deviation here (date, what, why).

## Working rules
- **Plan before code.** Restate the goal, list risks and open questions, then wait for approval.
- **One milestone at a time.** Do not build later-milestone features. Leave `# TODO(Mx): ...` instead.
- **Never silently invent requirements.** Ask, or log the assumption in `docs/DECISIONS.md`.
- **"Done" means proven.** Show test and eval command output. Never claim a metric you did not measure.
- **End every milestone the same way.** Update `docs/PROGRESS.md`, list known gaps with numbers, and suggest a commit message.

## Hard rules (non-negotiable)
1. **Copyright.**
   - Casebook PDFs, extracted text, and page images are never committed. Fixtures live in `$FIXTURE_DIR` (git-ignored).
   - Gold labels reference content by `doc_id + pdf_page + turn_index/bbox`, never by copied text.
   - Unit tests use synthetic PDFs generated in code.
   - The storage bucket is private. Signed URLs last 10 minutes or less.
   - The app never exports source text. Tutor quotes are short excerpts with citations.
2. **Grounding.**
   - Every factual tutor answer cites book + `printed_page`.
   - If the answer isn't in the corpus, reply with "Not in your casebooks". General knowledge may follow, labelled "Not from your casebooks".
   - Every AI-generated field carries `provenance = ai_generated` and is badged in the UI.
3. **Workspace isolation.** Enforce it in SQL (`WHERE workspace_id = …`) inside the retrieval layer, never via prompt instructions. Cross-workspace retrieval happens only via an explicit `cross_reference=True` parameter.
4. **Leak-proof interviewer by construction.** The interviewer node's context never contains `issue_tree_json` or `model_recommendation`. Only the feedback node loads them.
5. **Provider interface.** Every LLM, vision, embedding and rerank call goes through `backend/app/providers/`. No vendor SDK imports anywhere else. Model ids come from env/config, never hard-coded.
6. **Observability.** Every LLM call is traced (Langfuse) with session_id, and its token cost is logged.
7. **No book-specific code paths keyed on filename or title.** Detectors may use layout and text patterns. If a heuristic only fits one book, document it as a detector with a confidence score.

## Stack
- **Frontend:** Next.js (App Router, TypeScript strict, Tailwind), pnpm, deployed on Vercel.
- **Backend:** Python 3.12, FastAPI, uv, SQLAlchemy 2 + Alembic, Pydantic v2, pytest, ruff. Deployed on Render.
- **Database:** Supabase Postgres + pgvector, Supabase Auth, and a private Storage bucket.
- **Agents:** LangGraph, with `langgraph-checkpoint-postgres` for persistence.
- **PDF:** PyMuPDF (layout, drawings, rendering), pdfplumber (tables), OCR fallback.
- **Models:** Gemini by default, through the provider interface. Claude and OpenAI adapters exist behind the same contract.
- **Tracing:** Langfuse.

## Repo layout
```
/frontend
/backend/app/{api,core,db,ingestion,retrieval,agents,tutor,mastery,providers,worker}
/backend/tests            # unit + integration; synthetic fixtures only
/evals/{gold,runners,reports}   # gold = labels by reference; reports git-ignored if they contain text
/docs  /prompts
```

## Commands
```
# backend
cd backend && uv sync
uv run alembic upgrade head
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run python -m app.worker                      # job worker
uv run python -m app.ingestion.cli ingest <pdf> --workspace consulting|pm
# evals
uv run python -m evals.run <suite>               # suites: ingestion, retrieval, grader, interviewer
# frontend
cd frontend && pnpm i && pnpm dev && pnpm lint && pnpm test
```

## Conventions
- All LLM structured outputs use Pydantic models. On a schema failure, validate, retry once, then mark the item low-confidence. Never crash the job.
- Schema changes go through Alembic migrations only.
- Config comes from `app/core/config.py` (pydantic-settings). `.env.example` is kept current.
- Frontend uses server components by default. Streaming uses SSE.

## Gotchas
- **Supabase pooler.** LangGraph PostgresSaver and the worker need a direct or session-mode connection, not the transaction pooler (port 6543), because prepared statements break there.
- **Vector dimensions.** A pgvector HNSW index on `vector` supports at most 2000 dims, so embeddings are stored at **1536**. Store `embedding_model` and `embedding_dim` on every chunk.
- **Page numbers.** `printed_page` ≠ `pdf_page`. Detect the offset per document and cite `printed_page`.
- **Free hosting.** Free Render services sleep. Ingestion runs in the worker, never inside a web request.
- **Licence.** PyMuPDF is AGPL. Note this in the README.
