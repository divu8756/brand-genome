# BUILD PROMPT: "CaseCoach" — RAG Case-Prep Tutor & AI Case Interviewer

## 0. ROLE
You are a senior full-stack AI engineer and learning-product designer with
experience in document-AI pipelines, production RAG, LangGraph agents, and MCP.
You care about grounded answers, clean architecture, and teaching that works.

Before coding:
- restate the plan;
- flag risks;
- list open questions;
- confirm which milestone you are starting.

Build incrementally. Each milestone must run end-to-end before the next.

## 1. CONTEXT
- **User:** an Executive MBA student preparing for BOTH management consulting
  and product management (PM) interviews.
- **Problem:** casebooks show frameworks applied to cases. They rarely teach
  WHEN to choose a framework, WHY it fits, or WHEN it fails. The user wants to:
  1. learn framework selection;
  2. practise realistic live cases;
  3. see measurable progress.
- **Outcome:** a private, single-user web app that does four things:
  1. Ingests uploaded casebooks.
  2. Teaches framework usage.
  3. Tracks learning progress.
  4. Acts as a 1:1 case interviewer.
- The app doubles as an AI PM portfolio piece, so architecture quality,
  evals, and observability matter.

## 2. ASSUMPTIONS (confirm or correct before building)
- Single user. Auth exists only to keep content private.
- Casebooks are copyrighted and for personal study only:
  - no public URLs, no sharing, no export of source text;
  - quote short excerpts only, always with citations.
- Stack:
  - **Frontend:** Next.js (App Router, TypeScript, Tailwind) on Vercel.
  - **Backend:** FastAPI on Render.
  - **Database:** Postgres + pgvector (Supabase), with a private storage
    bucket for the PDFs.
  - **Agents:** LangGraph.
  - **Models:** Gemini for LLM, vision, and embeddings, behind a provider
    interface so Claude or OpenAI can be swapped in.
- Interviews are text-based in v1. Voice comes in v2.
- Anything unstated is unknown. Ask, or state an assumption explicitly.
  Never silently invent requirements.

## 3. TWO ISOLATED WORKSPACES (tabs)
The app has two tabs: **Consulting** | **Product Management**.

Each workspace has its own:
- document library;
- vector namespace;
- framework catalogue;
- case bank and guesstimate bank;
- progress data.

Case-type taxonomy, seeded below and extended from ingested content:
- **Consulting:** profitability, market entry, pricing, growth strategy,
  M&A + due diligence, unconventional, guesstimates.
- **PM:** product improvement/design, root cause analysis (RCA),
  guesstimates, pricing, go-to-market (GTM), metrics, product strategy,
  hardware, teardown, "favourite product".

Retrieval never crosses workspaces unless the user toggles "cross-reference"
(useful for guesstimates and pricing, which overlap).

## 4. SOURCE CORPUS — OBSERVED FACTS
The parser must generalise to ANY casebook. Do not hard-code these two books;
use them as the primary test fixtures.

### 4a. PM casebook (XLRI Prometheus, 229 portrait pages, clean text layer)
**Contents:**
- concept glossary;
- frameworks: CIRCLES, User Journey, HEART, RICE, plus a list of
  prioritisation frameworks;
- worked cases for 8 case types;
- 8 product teardowns;
- 11 company interview experiences (Amazon, Google, Microsoft, Walmart…;
  some are 30+ pages);
- tips;
- a "last-minute cheat sheet".

**Parsing notes:**
- **Labelled dialogues:** worked cases use explicit "Candidate:/Interviewer:"
  turns with "Step #n" headings.
- **Page offset:** printed page numbers are 4 behind PDF page indices.
- **Tables:** RICE scoring tables flatten into word soup under plain
  extraction.
- **Duplicates:** Generative AI appears twice; the cheat sheet repeats
  CIRCLES, RCA, and GTM.

### 4b. Consulting casebook (IIMA Consult Prep Book 2025-26, 389 landscape slide pages)
**Contents:**
- The index (pp. 7–10) is a TABLE with columns
  `S.No | case name | sector | difficulty | page`. It covers 108 cases across
  6 types, 25 guesstimates, and 27 sector "Panorama" industry reports.
- Other sections:
  - structure of a case interview;
  - Important Frameworks (~pp. 14–31);
  - preamble with an intro case;
  - Consulting 101 primer;
  - datasheets with handy numbers for guesstimates.
- Printed page = PDF page (no offset here). Detect the offset per document;
  never assume it.

**Case format:** each case is a **transcript page** followed by an
**Approach page**.

- **Header metadata line:** `CaseType | Sector (Sub-sector) | Difficulty | Sub-type`,
  e.g. `Profitability | F&B | Easy | Cost Reduction`. Parse it directly.
- **Transcripts have NO speaker labels.** Turns simply alternate in a
  2-column layout, and font and colour are identical for both speakers.
  - First, check whether background rectangles or shading boxes mark turns.
  - Otherwise, use LLM speaker attribution with validation: questions vs
    answers, first turn = interviewer prompt, consistency checks.
  - Store a confidence score for each attribution.
- **Approach page** (structured; this is gold for the interviewer):
  - Problem Statement;
  - CASE FACTS → hidden facts;
  - APPROACH/FRAMEWORK, drawn as a vector-graphics issue tree. Text
    extraction scrambles it, so render the page and use vision to rebuild
    the tree as JSON;
  - RECOMMENDATIONS → model answer;
  - INTERVIEWEE NOTES;
  - OBSERVATIONS → evaluator rubric hints.
- **Noise to strip:**
  - navigation-button text repeated on every page ("PANORAMA REPORT",
    "FRAMEWORK", "INDEX");
  - cover artefacts;
  - footers;
  - ~1,700 images, mostly campus photos and decoration (filter by size and
    position).
- **Industry reports:** Panorama reports map to cases by sector. Link them,
  so the tutor can say "read the Aviation primer before this case".
- **Difficulty:** normalise to a 1–5 scale: Easy, Easy-Mod, Moderate,
  Mod-Challenging, Challenging.

### 4c. General ingestion rules
1. Detect layout per page: portrait text vs landscape slide, columns,
   tables, diagrams. Use layout-aware extraction (e.g., PyMuPDF/pdfplumber
   with column detection).
2. Route low-confidence pages (diagrams, tables, issue trees) to a vision
   model. Store the output as structured JSON plus a text rendering for
   embedding.
3. Detect scanned PDFs (no fonts) and fall back to OCR. Detect encrypted
   PDFs and report them clearly.
4. Store both `pdf_page` and `printed_page`. Always cite the printed page.
5. Deduplicate near-identical chunks. Treat cheat sheets as a "summary
   layer" linked to the full sections.
6. After each upload, show an ingestion report: sections found, cases parsed
   per type, frameworks detected, tables and diagrams rebuilt,
   low-confidence items, and failures. The user can fix labels, and fixes
   persist.

## 5. DATA MODEL (minimum)
- **Workspace**
- **Document:** file, title, edition/year, page_offset, layout_type, status.
- **Chunk:**
  - text, embedding;
  - section_type (framework | case_transcript | case_approach | guesstimate |
    industry_report | teardown | interview_experience | concept | tip |
    cheat_sheet | primer | datasheet);
  - case_type, sub_type, sector, difficulty, company;
  - frameworks[];
  - pdf_page, printed_page;
  - parent_section_id.
- **Framework:**
  - name, aliases, workspace, purpose, steps[];
  - when_to_use, trigger_signals[], when_not_to_use, alternatives[];
  - common_mistakes[], related[];
  - source_chunks[];
  - provenance per field: `casebook | ai_generated`.
- **CaseScript:**
  - source, case_type, sub_type, sector, difficulty;
  - prompt, hidden_facts{}, exhibits[];
  - issue_tree_json, model_recommendation;
  - evaluator_observations[], framework_tags[];
  - transcript_turns[] (speaker, text, confidence).
- **Guesstimate:** prompt, approach steps, assumptions, answer, source.
- **IndustryReport:** sector, key facts, linked_case_ids[].
- **Session** (`learn | drill | interview`, origin `web | mcp`), **Turn**,
  **RubricScore**.
- **MasteryRecord:** framework / case_type / sector, with score, confidence,
  attempts, last_seen, next_review.

## 6. FEATURES

### A. Library
- Upload PDF/DOCX into the active workspace. Show a progress bar and the
  ingestion report.
- Re-index and delete.
- Browse by case type, sector, difficulty, framework, or source book. Each
  item opens its source pages.

### B. Framework Tutor — "what, how, when, where, when NOT"
Each Framework Card shows:
- purpose and steps;
- trigger signals in a case prompt (e.g., "costs rising vs benchmarks" →
  cost tree/value chain);
- when NOT to use, and what to use instead;
- common mistakes;
- 2–3 cited cases where the framework was applied, drawn from both books
  where relevant.

Modes:
1. **Explain:** chat grounded in the corpus.
2. **Selector drill:** show a case prompt; the user picks and justifies a
   framework; the tutor grades both the choice and the reasoning.
3. **Structure drill:** the user types an issue tree or structure; the tutor
   compares it with the source approach (`issue_tree_json`) and highlights
   missing or overlapping (non-MECE) branches.
4. **Compare:** e.g., CIRCLES vs User Journey; value-chain vs profit-tree
   approaches.
5. **Guesstimate drill:** step-by-step approach, with datasheet numbers
   available on request.

Difficulty adapts to mastery.

### C. Progress Tracking
- Mastery score (0–100) per framework, case type, and sector. It updates
  after every drill and interview, weighted by difficulty.
- Spaced repetition (SM-2) schedules reviews of weak items.
- Dashboard:
  - mastery heatmap;
  - rubric trend per dimension;
  - top 3 weak areas, each with a "do this next" action;
  - streak;
  - session history with full transcripts (web and MCP sessions).

### D. 1:1 Case Interviewer (LangGraph state machine)
**Setup options:**
- workspace;
- case type (or random);
- sector;
- difficulty;
- format: interviewer-led (consulting) or candidate-led (PM);
- optional company style, drawn from the PM interview experiences;
- timer.

**States:**
1. **Prompt**
2. **Clarifying questions:** answer ONLY from `hidden_facts`. If a fact is
   missing, generate a plausible value, keep it consistent for the rest of
   the session, and log it as invented.
3. **Structuring**
4. **Analysis/math:** reveal exhibits only on request; verify the
   candidate's arithmetic.
5. **Brainstorm/prioritise**
6. **Synthesis/recommendation**
7. **Feedback**

**Interviewer behaviour:**
- Neutral and realistic.
- Probes ("why that segment?", "is that MECE?") and pushes back on weak
  logic.
- Steers toward the root cause the way the source transcripts do.
- No coaching unless the user asks for a hint. Hints are logged and reduce
  the score.
- Never reveals the issue tree or the recommendation before the candidate
  has attempted them.

**Rubric:** score each dimension 1–5, with evidence quotes from the user's
own turns. Use the source `evaluator_observations` as grading anchors.
- clarification quality;
- structure and framework fit (MECE-ness);
- hypothesis-driven thinking (consulting) / user empathy (PM);
- quantitative rigour;
- prioritisation;
- synthesis and communication;
- business judgement.

**Feedback report:**
- scores;
- top 3 fixes;
- where the framework choice helped or hurt;
- the source approach and issue tree (rendered and cited);
- the linked industry primer;
- the next recommended drill.

## 7. GROUNDING & HONESTY (non-negotiable)
- Every factual tutor answer cites its source (book + printed page).
- If the answer isn't in the corpus, say so. Then optionally offer general
  knowledge, labelled "Not from your casebooks".
- Badge AI-generated content (e.g., `when_not_to_use`, invented case facts).
- Retrieval: hybrid (BM25 + vector) → rerank → filter by workspace,
  section_type, and case_type. Return parent sections, not orphan fragments.
- If the two books disagree, show both and cite both.
- Never fabricate data or questions and attribute them to a source.

## 8. NON-FUNCTIONAL
- Ingestion runs as a background job. A 400-page PDF finishes in under
  10 minutes, resumes on failure, and processes vision pages in parallel.
- Tutor responses begin streaming within 3 seconds.
- Interview state persists through a page refresh.
- Tracing via Langfuse or LangSmith for all agent runs.
- Cost logged per session.
- Mobile-responsive UI. The interview screen must work well on a phone.

## 9. MCP
### 9a. Development (from day one)
Assume Claude Code has these MCP servers connected:
- **Supabase MCP:** schema, migrations, pgvector inspection.
- **GitHub MCP:** PRs and issues.
- **Playwright MCP:** E2E tests of the upload → tutor → interview flows.

### 9b. App v1
No MCP dependency. The backend calls the LLM and database directly.

### 9c. CaseCoach MCP server (milestone M7)
Expose CaseCoach as a remote MCP server, hosted in FastAPI, single user,
with OAuth or token auth.

Tools:
- `search_casebooks(workspace, query, filters)` → cited excerpts
- `get_framework_card(workspace, name)`
- `start_mock_interview(workspace, case_type, difficulty, sector?)` → session_id + prompt
- `submit_answer(session_id, text)` → interviewer reply
- `end_interview(session_id)` → rubric report
- `get_progress(workspace)` → mastery summary and weak areas

Rules:
- The same grounding, citation, and workspace-isolation rules apply as in
  the web app.
- Tools return only short, cited excerpts of source text. Never return bulk
  text.
- Sessions created via MCP appear in the web dashboard (`origin = mcp`).

### 9d. Optional integrations
- Google Drive import for casebooks (MCP or API).
- Google Calendar events for spaced-repetition reviews and mock sessions.

## 10. MILESTONES
- **M1:** Ingestion pipeline and ingestion report, tested on both books.
- **M2:** Grounded chat with citations, plus an auto-built framework
  catalogue per workspace.
- **M3:** Library UI, workspace isolation, CaseScript and Guesstimate banks.
- **M4:** Tutor drills, mastery scoring, spaced repetition.
- **M5:** Interviewer agent, rubric scoring, feedback report.
- **M6:** Progress dashboard, company-style PM rounds, industry-primer
  linking, polish.
- **M7:** CaseCoach MCP server (§9c).
- **v2:** Voice interviews; weekly study-plan generator; Drive/Calendar
  integrations.

## 11. ACCEPTANCE CRITERIA
- [ ] IIMA book: ≥ 100 of 108 cases parsed with the correct case type,
      sector, and difficulty. All 25 guesstimates and all 27 industry
      reports are detected.
- [ ] IIMA book: ≥ 90% of Approach pages yield case facts, an issue tree
      (JSON), and recommendations.
- [ ] Speaker attribution is ≥ 90% accurate on a 10-case hand-labelled
      sample.
- [ ] XLRI book: all 4 named frameworks, 8 case types, 8 teardowns, and
      11 interview experiences are detected. Citations use printed pages
      (offset handled).
- [ ] The RICE table and the IIMA issue trees are retrievable as structured
      data, not word soup.
- [ ] An out-of-corpus question gets an explicit "not in your casebooks"
      response.
- [ ] With cross-reference off, Consulting queries never return PM chunks,
      and vice versa.
- [ ] The interviewer never leaks the structure early. Invented facts stay
      consistent within a session.
- [ ] Mastery changes after drills, and the weakest areas show on the
      dashboard.
- [ ] M7: a full mock interview can be run from Claude Desktop via MCP. It
      appears in the web dashboard, and no tool returns more than short
      cited excerpts.

## 12. EDGE CASES
- Scanned, encrypted, or duplicate uploads; a new edition of the same book.
- A case that spans multiple types (e.g., pricing + market entry).
- A case type or sector with zero source cases → generate one, labelled
  AI-generated.
- The user abandons an interview mid-way.
- The user tries to extract the answer from the interviewer.
- The user submits gibberish or makes arithmetic errors.
- An MCP call with an invalid session_id or the wrong workspace → return a
  clear error and do not leak data.

## 13. DELIVERABLES
- Repo with `/frontend`, `/backend`, and `/mcp` (M7).
- README covering setup, environment variables, deploy steps, and MCP
  client configuration.
- Ingestion test fixtures and ingestion-report snapshots for both books.
- Eval set: 30 grounded Q&A pairs, 10 hand-labelled transcripts, and
  5 interview scripts with expected rubric ranges.
- Architecture diagram (Mermaid).

**Start by restating the M1 plan, listing open questions, and proposing the
folder structure. Do not write code until I confirm.**
