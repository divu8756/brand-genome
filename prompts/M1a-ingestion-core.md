# M1a — Generic ingestion pipeline + XLRI

**Read first:** @CLAUDE.md @docs/SPEC.md (§4a, §4c, §5, §8, §10, §11) @docs/SPEC_ADDENDUM.md (D2, D4, D8, D12) @docs/SPIKE_REPORT.md @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
A book-agnostic, resumable ingestion pipeline. It must be proven on the XLRI PM casebook and produce an ingestion report.

## In scope
1. **Data model.** Write Alembic migrations for `documents`, `sections` (hierarchical, with `parent_section_id`), `chunks` (all §5 Chunk fields plus `embedding_model`, `embedding_dim`, a `tsvector` column and a `content_hash`), `frameworks_raw`, `label_overrides` and `ingestion_reports`.
2. **Job flow.** `POST /documents` uploads to the private bucket and enqueues a job. The worker processes it page by page with checkpoints (D2).
3. **Pre-flight.**
   - Detect encryption and fail with a clear message.
   - Detect scanned PDFs (no fonts) and route them to OCR.
   - Detect duplicate uploads by file hash.
   - Detect a new edition: same title, different hash. Version it and mark the old one superseded.
4. **Page analysis.** For each page, record:
   - orientation;
   - column count;
   - table candidates (pdfplumber);
   - diagram candidates (drawing density);
   - an extraction-confidence score.

   Low-confidence pages go to vision and are stored as JSON plus a text rendering.
5. **Page offsets.** Use the offset detector from the spike, and store both `pdf_page` and `printed_page`.
6. **Section detection.**
   - Use headings, font-size hierarchy and TOC/bookmarks when present.
   - Classify each section's `section_type` (§5 enum) with an LLM over the heading plus the first 500 characters.
   - Cache the result and record a confidence score.
7. **XLRI specifics (generic detectors, not filename logic).**
   - **Labelled dialogue parser:** `Candidate:`/`Interviewer:` turns and `Step #n` headings → transcript turns with confidence 1.0.
   - **Framework detection:** CIRCLES, User Journey, HEART, RICE, plus the prioritisation list.
   - **RICE and other tables** → structured JSON plus a markdown rendering for embedding. Never word soup.
   - **Content detection:** teardowns, and interview experiences (with `company`).
8. **Chunking and dedup.**
   - Chunk within sections, 300–800 tokens, without splitting dialogue turns.
   - Near-duplicates (cosine > 0.95 or MinHash) are linked rather than duplicated.
   - The cheat sheet becomes a `cheat_sheet` summary layer linked to the full sections.
9. **Embedding.** Embed through the provider (D4) in batches. Build the HNSW and GIN indexes.
10. **Ingestion report.** Store it as JSON plus `GET /documents/{id}/report`. It covers sections found, counts by type, frameworks detected, tables and diagrams rebuilt, low-confidence items and failures.
11. **Label overrides.** `PATCH` overrides persist and are re-applied on re-index.

## Out of scope
- IIMA-specific parsing (M1b);
- retrieval and chat (M2);
- the upload UI (M3). Use the CLI and the API only.

## Tests & evals
- **Unit tests** on synthetic PDFs generated in code with reportlab, committed. They cover:
  - two-column layout;
  - a labelled dialogue;
  - a table;
  - a page offset;
  - an encrypted file;
  - a scanned (image-only) page;
  - duplicate pages.
- **Resume test:** kill the worker mid-job, restart it, and confirm no pages are duplicated or skipped.
- **`evals.run ingestion --doc xlri`:** compare against `evals/gold/xlri_inventory.json` and report §10 item 4 (frameworks, case types, teardowns, interview experiences, offset).

## Definition of done
- [ ] All §10 XLRI items pass, or their gaps are reported with numbers.
- [ ] The RICE table is retrievable from the DB as structured JSON (show a query).
- [ ] Citations use `printed_page` (offset 4 verified on 3 sample pages).
- [ ] Total XLRI ingestion time is logged, and the cost is logged in Langfuse.
- [ ] `PROGRESS.md` is updated.
