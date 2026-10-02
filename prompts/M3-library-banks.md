# M3 — Library UI, workspaces, case & guesstimate banks

**Read first:** @CLAUDE.md @docs/SPEC.md (§3, §6A, §8 mobile, §12) @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
Everything from M1 and M2 becomes usable from the browser, including on a phone.

## In scope
1. **Workspace tabs.** All state is scoped by workspace, and the active workspace persists in the URL.
2. **Upload.**
   - Accept PDF and DOCX. DOCX goes through a converter into the same pipeline.
   - Show a progress bar driven by `page_tasks` (polling or SSE).
   - Show clear states for encrypted, scanned→OCR, duplicate and new-edition uploads.
3. **Ingestion report UI.**
   - Sections, counts, and a low-confidence queue.
   - Inline label fixes (case type, sector, difficulty, speaker per turn, section type) → `label_overrides`.
4. **Document actions.** Re-index and delete (cascades chunks, signed files and banks).
5. **Browse.**
   - Filters: case type, sector, difficulty, framework, source book.
   - Each item opens its source pages (signed URL, deep-linked to the page).
6. **CaseScript bank.** A detail view shows:
   - metadata;
   - the transcript with speaker confidence;
   - linked Panorama primer.

   The approach, issue tree and recommendation sit behind a "Reveal (spoils interview use)" toggle. Log the reveal, because M5 avoids revealed cases by default.
7. **Guesstimate bank** and a datasheet viewer.
8. **Zero-case gaps.** If a case type or sector has 0 cases, show "Generate practice case" → an AI-generated CaseScript, badged (§12).

## Out of scope
Drills, mastery and the interviewer.

## Tests
- **Playwright:** upload a synthetic PDF → see the report → fix a label → re-index → confirm the fix persisted.
- **Mobile viewport:** library and case detail views at 390 px.
- **API tests:** delete cascade, and workspace scoping on every list endpoint.

## Definition of done
- [ ] All flows work on desktop and at 390 px.
- [ ] Revealed cases are tracked.
- [ ] `PROGRESS.md` is updated.
