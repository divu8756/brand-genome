# M1b — Slide-deck casebooks (IIMA)

**Read first:** @CLAUDE.md @docs/SPEC.md (§4b, §4c, §5 CaseScript/Guesstimate/IndustryReport, §11) @docs/SPEC_ADDENDUM.md (D1, D8) @docs/SPIKE_REPORT.md @docs/PROGRESS.md

Use plan mode. Wait for approval.

## Goal
Turn a landscape slide-deck casebook into structured CaseScripts, guesstimates and industry reports that meet the §11 IIMA thresholds.

## In scope
1. **Noise stripping.**
   - Text repeated at the same bbox on more than 30% of pages counts as navigation chrome. Use the thresholds from the spike report.
   - Strip footers and cover artefacts.
   - Image filter by size and position: keep only images that sit inside content regions and are larger than the spike threshold.
2. **Index-table detector.** Parse the index into a case registry (`S.No | name | sector | difficulty | page`). This registry becomes the backbone that every case links to.
3. **Header metadata parser** for `CaseType | Sector (Sub-sector) | Difficulty | Sub-type`.
   - Normalise difficulty to 1–5.
   - Reconcile against the index. If they disagree, keep the index value and flag the item.
4. **Transcript turn attribution**, using the strategy the spike recommended.
   - If the strategy is LLM-based: first turn = interviewer; questions vs answers; alternation consistency check; one re-pass on inconsistency.
   - Store `confidence` per turn.
   - Handle two-column reading order.
5. **Approach page parser.** Split the page into these blocks:
   - Problem Statement;
   - CASE FACTS → `hidden_facts{}`;
   - APPROACH/FRAMEWORK → render and run `vision_structured` → `issue_tree_json` (IssueNode schema);
   - RECOMMENDATIONS → `model_recommendation`;
   - INTERVIEWEE NOTES;
   - OBSERVATIONS → `evaluator_observations[]`.

   Pair each Approach page with its transcript page.
6. **Multi-type cases** (§12). `case_type` stays the primary type; add a `secondary_types[]` field.
7. **Guesstimates and datasheets.** Guesstimates → the Guesstimate table. Datasheet numbers → structured key/value with citations.
8. **Panorama reports.** Store them as `IndustryReport`s. Link each one to cases by normalised sector (`linked_case_ids[]`).
9. **Frameworks section** (~pp. 14–31) → `frameworks_raw` for M2.
10. **Report.** Extend the ingestion report with:
    - cases per type;
    - attribution confidence histogram;
    - issue trees rebuilt vs failed;
    - unmatched index rows.

## Out of scope
Retrieval, chat and UI.

## Tests & evals
- **Synthetic fixtures:** a slide page with a 2-column unlabelled transcript, a header line, and an Approach page with a vector-drawn tree.
- **`evals.run ingestion --doc iima`** against the gold set. It must report:
  - cases parsed with correct type, sector and difficulty (target ≥ 100/108);
  - guesstimates (25/25) and reports (27/27);
  - Approach pages with facts, tree and recommendations (target ≥ 90%);
  - speaker accuracy on the 10 gold cases (target ≥ 90%);
  - issue-tree similarity vs gold: node-label semantic match F1, and depth agreement.

## Definition of done
- [ ] Every §11 IIMA metric is reported with numbers, with failures listed by case.
- [ ] Re-running ingestion is idempotent and keeps label overrides.
- [ ] The full IIMA run takes less than 10 minutes on the worker (D10), or the bottleneck is profiled.
- [ ] `PROGRESS.md` is updated.
