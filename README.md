# Brand Genome — constraint engine

The horizontal layer every agent in Project NEXT calls before it acts.

```bash
PYTHONPATH=. python run_demo.py       # five cases, no dependencies
PYTHONPATH=. streamlit run app.py     # the visual demo
```

**Deterministic. No LLM in the adjudication path.** The model generates; the
genome adjudicates. Never the reverse — because a brand director can sign off on
"blocked by rule CL-4471" and cannot sign off on "the model felt it was off-brand."

## What it checks

| Dimension | Rules | Auto-repairable? |
|---|---|---|
| Claims (substantiation, absolutes) | CL-* | Yes |
| Regulatory (therapeutic terms) | RG-* | **No — legal escalation** |
| Tone (voice, caps, exclamations) | TN-* | Yes |
| Banned adjacency | AD-* | **No — new concept required** |
| Equity guardrails | EQ-* | **No — new concept required** |
| Visual grammar | VS-* | Yes |

The distinction matters. Rewording an adjacency violation would let a bad
*concept* through with clean *copy* — so those escalate to a human instead.

## Extending it

`data/genome.json` holds three brands and three markets. Add a brand by copying
the schema; no code changes required. That is the point: the genome is data, and
brand teams own it.
