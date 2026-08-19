"""
run_demo.py — the Brand Genome demo.

    python run_demo.py

Four cases, in the order to show them:
  1. A plausible, attractive, entirely non-compliant Dove post  -> BLOCKED
  2. The same post evaluated for a second market                -> different rules fire
  3. The Rexona fourth-official moment, done wrong              -> BLOCKED on adjacency
  4. A compliant post                                           -> ALLOW

The demo moment is case 1: let the audience read the post and like it, THEN
show the genome blocking it with rule IDs and returning the corrected version.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.genome import BrandGenome

G = BrandGenome()

CASES = [
    ("1. THE DEMO MOMENT — a post any brand manager might approve", "dove", "IN",
     "Reduces hair fall by 90% instantly! Get that FLAWLESS, perfect hair you're "
     "obsessed with — the ultimate weight loss for your hair.",
     ["monsoon", "hair_care"]),

    ("2. REPAIRABLE — claims and tone only, no concept violation", "dove", "IN",
     "Reduces hair fall by 90% instantly! Get that FLAWLESS, perfect hair "
     "you're obsessed with.",
     ["hair_care"]),

    ("2b. SAME COPY, DIFFERENT MARKET — the regulatory overlay", "lifebuoy", "IN",
     "Lifebuoy cures germs and prevents disease. Deadly bacteria don't stand a chance.",
     ["hygiene"]),

    ("3. THE REXONA MOMENT, DONE WRONG — speed without governance", "rexona", "IN",
     "That was a bad call by the ref! Rexona: you'll never sweat again, guaranteed!!!",
     ["football", "viral", "fourth_official"]),

    ("4. A COMPLIANT POST — the genome gets out of the way", "rexona", "IN",
     "Six added minutes. The one person who cannot lose their cool. "
     "Rexona gives up to 72h protection.",
     ["football", "fourth_official"]),
]


def show(v, title, copy):
    print("\n" + "=" * 82)
    print(title)
    print("-" * 82)
    print(f'  INPUT   "{copy}"')
    icon = {"BLOCKED": "BLOCKED ", "REVISE": "REVISE  ", "ALLOW": "ALLOW   "}[v.verdict]
    print(f"\n  VERDICT {icon} · {v.brand} · {v.market} · "
          f"{v.rules_evaluated} rules in {v.latency_ms} ms")
    if v.violations:
        print()
        for x in v.violations:
            tag = "HARD" if x.severity == "hard" else "soft"
            ev = f'  [{x.evidence}]' if x.evidence else ""
            print(f"    {tag:>4} {x.rule:<10} {x.dimension:<10} {x.reason}{ev}")
    if v.approved_variant:
        print(f'\n  APPROVED VARIANT\n    "{v.approved_variant}"')
    if v.substantiation_ref:
        print(f"    substantiation: {v.substantiation_ref}")
    if v.escalation:
        print(f"\n  ESCALATION\n    {v.escalation}")


if __name__ == "__main__":
    print("BRAND GENOME — constraint engine v1.0.0")
    print("Deterministic. No LLM in the adjudication path.")
    for title, brand, market, copy, tags in CASES:
        show(G.evaluate(brand, market, copy, tags), title, copy)
    print("\n" + "=" * 82)
    print("Every verdict carries a rule ID. A brand director signs off on CL-4471,")
    print("never on 'the model felt it was off-brand.'")
