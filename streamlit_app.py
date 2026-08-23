"""
streamlit_app.py — Project NEXT

  TAB 1  BRAND GENOME             the horizontal governance layer
  TAB 2  CULTURAL MOMENT ENGINE   the agent that calls it

SINGLE FILE BY DESIGN. GitHub's web uploader silently skips zero-byte files, so
an empty core/__init__.py never arrives and package imports fail on Streamlit
Cloud. One file cannot have that problem.

    streamlit run streamlit_app.py

Deterministic where it matters. Nodes 01, 02, 05 and the entire genome never
touch a language model: a brand-fit score and a regulatory verdict get defended
in front of a brand director, so they carry rule IDs and reproduce exactly.
The model writes the narrative. It never decides whether something ships.
"""
from __future__ import annotations
from __future__ import annotations
import re, json, time, html
from dataclasses import dataclass, asdict, field
import streamlit as st


# ══════════════════════════════════════════════════════════════
# Verdict types
# ══════════════════════════════════════════════════════════════
@dataclass
class Violation:
    rule: str
    severity: str          # "hard" blocks, "soft" warns and logs
    dimension: str
    reason: str
    evidence: str = ""


@dataclass
class Verdict:
    verdict: str                        # ALLOW | REVISE | BLOCKED
    brand: str
    market: str
    violations: list = field(default_factory=list)
    approved_variant: str | None = None
    substantiation_ref: str | None = None
    latency_ms: float = 0.0
    rules_evaluated: int = 0
    escalation: str | None = None

    def to_json(self) -> str:
        d = asdict(self)
        d["violations"] = [asdict(v) if not isinstance(v, dict) else v
                           for v in self.violations]
        return json.dumps(d, indent=2)


# ══════════════════════════════════════════════════════════════
# The genome itself — loaded from JSON, not hard-coded
# ══════════════════════════════════════════════════════════════
class BrandGenome:
    def __init__(self, path=None):
        self.g = GENOME_DATA           # embedded below — no file I/O, no packages
        self._log: list = []           # decision + override audit trail

    # ---------- helpers ----------
    def brand(self, name: str) -> dict:
        b = self.g["brands"].get(name.lower())
        if not b:
            raise KeyError(f"no genome encoded for brand '{name}'")
        return b

    def market_rules(self, market: str) -> dict:
        return self.g["markets"].get(market.upper(), self.g["markets"]["_DEFAULT"])

    # ---------- the five checks ----------
    def _check_claims(self, copy: str, brand: dict, market: dict) -> list:
        out, low = [], copy.lower()
        # 1. Quantified claims need a substantiation reference
        for m in re.finditer(r"(\d{1,3})\s?%", copy):
            pct = int(m.group(1))
            substantiated = any(c["max_pct"] >= pct and c["market_ok"]
                                for c in brand["claims"])
            if not substantiated:
                out.append(Violation(
                    rule="CL-4471", severity="hard", dimension="claims",
                    reason=f"Quantified claim '{pct}%' has no substantiation on file "
                           f"for this market ({market['regulator']}).",
                    evidence=m.group(0)))
        # 2. Absolute-time claims
        for phrase in market["banned_phrases"]:
            if phrase in low:
                out.append(Violation(
                    rule="CL-4488", severity="hard", dimension="claims",
                    reason=f"Phrase '{phrase}' constitutes an unsupported absolute "
                           f"claim under {market['regulator']} guidance.",
                    evidence=phrase))
        # 3. Category-restricted claims
        for term, rule in market["restricted_terms"].items():
            if term in low:
                out.append(Violation(
                    rule=rule, severity="hard", dimension="claims",
                    reason=f"'{term}' is a restricted therapeutic claim in this market.",
                    evidence=term))
        return out

    def _check_tone(self, copy: str, brand: dict) -> list:
        out, low = [], copy.lower()
        t = brand["tone"]
        excl = copy.count("!")
        if excl > t["max_exclamations"]:
            out.append(Violation(
                rule="TN-0112", severity="soft", dimension="tone",
                reason=f"{excl} exclamation marks exceeds the {brand['name']} tone "
                       f"ceiling of {t['max_exclamations']}.",
                evidence="!" * excl))
        for word in t["banned_words"]:
            if re.search(rf"\b{re.escape(word)}\b", low):
                out.append(Violation(
                    rule="TN-0134", severity="soft", dimension="tone",
                    reason=f"'{word}' sits outside the {brand['name']} voice "
                           f"({t['descriptor']}).",
                    evidence=word))
        caps = re.findall(r"\b[A-Z]{4,}\b", copy)
        if caps and not t["allow_caps"]:
            out.append(Violation(
                rule="TN-0140", severity="soft", dimension="tone",
                reason="All-caps emphasis is outside the brand's typographic voice.",
                evidence=", ".join(caps)))
        return out

    def _check_adjacency(self, copy: str, tags: list, brand: dict) -> list:
        out, hay = [], (copy + " " + " ".join(tags)).lower()
        for adj in brand["banned_adjacencies"]:
            for kw in adj["keywords"]:
                if kw in hay:
                    out.append(Violation(
                        rule=adj["rule"], severity="hard", dimension="adjacency",
                        reason=f"{brand['name']} must never appear alongside "
                               f"{adj['topic']}. {adj['why']}",
                        evidence=kw))
                    break
        return out

    def _check_equity(self, copy: str, brand: dict) -> list:
        out, low = [], copy.lower()
        for g in brand["equity_guardrails"]:
            if any(k in low for k in g["keywords"]):
                out.append(Violation(
                    rule=g["rule"], severity="hard", dimension="equity",
                    reason=g["reason"]))
        return out

    def _check_visual(self, asset: dict, brand: dict) -> list:
        out, v = [], brand["visual"]
        pal = [p.upper() for p in v["palette"]]
        for c in asset.get("colours", []):
            if c.upper() not in pal:
                out.append(Violation(
                    rule="VS-0203", severity="soft", dimension="visual",
                    reason=f"Colour {c} is outside the approved {brand['name']} palette.",
                    evidence=c))
        for obj in asset.get("detected_objects", []):
            for banned in v.get("banned_objects", []):
                if banned in obj.lower():
                    out.append(Violation(
                        rule="VS-0211", severity="hard", dimension="visual",
                        reason=f"Detected object '{obj}' is prohibited in "
                               f"{brand['name']} imagery.", evidence=obj))
        logo = asset.get("logo_clear_space_pct")
        if logo is not None and logo < v.get("min_logo_clear_space_pct", 0):
            out.append(Violation(
                rule="VS-0220", severity="soft", dimension="visual",
                reason=f"Logo clear space {logo}% is below the "
                       f"{v['min_logo_clear_space_pct']}% minimum.",
                evidence=f"{logo}%"))
        dur = asset.get("duration_s")
        if dur is not None and dur > v.get("max_video_seconds", 999):
            out.append(Violation(
                rule="VS-0231", severity="soft", dimension="visual",
                reason=f"Video runs {dur}s against a {v['max_video_seconds']}s "
                       f"ceiling for this format.", evidence=f"{dur}s"))
        if asset.get("transcript"):
            out += [Violation(rule=x.rule, severity=x.severity, dimension="video_audio",
                            reason="In spoken track: " + x.reason, evidence=x.evidence)
                    for x in self._check_tone(asset["transcript"], brand)]
        return out

    # ---------- repair ----------
    def _repair(self, copy: str, violations: list, brand: dict, market: dict) -> tuple:
        fixed, ref = copy, None
        repairable = [v for v in violations
                      if v.dimension in ("claims", "tone", "visual")
                      and not v.rule.startswith("RG-")]
        blocking = [v for v in violations
                    if v.dimension in ("adjacency", "equity")
                    or v.rule.startswith("RG-")]

        rules_hit = {v.rule for v in repairable}

        if "CL-4471" in rules_hit:
            best = max((c for c in brand["claims"] if c["market_ok"]),
                       key=lambda c: c["max_pct"], default=None)
            fixed = re.sub(r"\s*\b(by|up to)?\s*\d{1,3}\s?%\s*(more|less|fewer)?",
                           " ", fixed, flags=re.I)
            if best:
                ref = best["ref"]
                if best["verb"].lower() in fixed.lower():
                    fixed = re.sub(re.escape(best["verb"]),
                                   best["approved_phrasing"], fixed, flags=re.I)

        for v in repairable:
            if v.rule == "CL-4488" and v.evidence:
                fixed = re.sub(rf"\s*\b{re.escape(v.evidence)}\b\s*", " ", fixed, flags=re.I)
            elif v.rule == "TN-0112":
                fixed = re.sub(r"!+", ".", fixed)
            elif v.rule == "TN-0134" and v.evidence:
                sub = brand["tone"]["substitutions"].get(v.evidence.lower())
                if sub:
                    fixed = re.sub(rf"\b{re.escape(v.evidence)}\b", sub, fixed, flags=re.I)
            elif v.rule == "TN-0140":
                fixed = re.sub(r"\b([A-Z]{4,})\b",
                               lambda m: m.group(1).capitalize(), fixed)

        # tidy
        fixed = re.sub(r"\s+([.,;:])", r"\1", fixed)
        fixed = re.sub(r"([.,;:]){2,}", r"\1", fixed)
        fixed = re.sub(r"\s{2,}", " ", fixed).strip()
        fixed = re.sub(r"^[\s.,;:—-]+", "", fixed)
        fixed = re.sub(r"\b(and|by|with)\s*(?=[.,;:]|$)", "", fixed, flags=re.I)
        fixed = re.sub(r"\s+([.,;:])", r"\1", fixed)
        fixed = re.sub(r"\s{2,}", " ", fixed).strip()
        if fixed and fixed[0].islower():
            fixed = fixed[0].upper() + fixed[1:]

        if blocking:
            reg = [v for v in blocking if v.rule.startswith("RG-")]
            if reg:
                return (None, ref,
                        f"Legal escalation required: {len(reg)} restricted therapeutic "
                        f"claim(s). Regulatory violations are never auto-repaired — "
                        f"route to market legal before any rewrite.")
            topics = ", ".join(sorted({v.dimension for v in blocking}))
            return (None, ref, f"New creative concept required: {topics} violation "
                               f"cannot be repaired by rewording.")
        return (fixed, ref, None)

    # ---------- drift, versioning, override logging ----------
    def record_decision(self, verdict, human_action: str, actor: str,
                        note: str = "") -> dict:
        rec = {"ts": time.time(), "brand": verdict.brand, "market": verdict.market,
               "genome_verdict": verdict.verdict, "human_action": human_action,
               "override": human_action == "publish" and verdict.verdict == "BLOCKED",
               "rules": [v.rule for v in verdict.violations],
               "actor": actor, "note": note, "genome_version": self.g["version"]}
        self._log.append(rec)
        return rec

    def override_rate(self, brand: str | None = None) -> dict:
        rows = [r for r in self._log
                if brand is None or r["brand"].lower() == brand.lower()]
        blocked = [r for r in rows if r["genome_verdict"] == "BLOCKED"]
        n_ovr = sum(1 for r in blocked if r["override"])
        rate = n_ovr / len(blocked) if blocked else 0.0
        return {"decisions": len(rows), "blocked": len(blocked),
                "overrides": n_ovr, "override_rate": round(rate, 3),
                "verdict": ("RECALIBRATE — genome is over-constraining" if rate > 0.12
                            else "healthy")}

    def drift(self, recent_copies: list, brand: str) -> dict:
        b = self.brand(brand)
        base = b.get("baseline_soft_rate", 0.10)
        rates = []
        for c in recent_copies:
            soft = [v for v in self._check_tone(c, b) if v.severity == "soft"]
            rates.append(len(soft) / max(1, len(c.split()) / 20))
        cur = sum(rates) / len(rates) if rates else 0.0
        delta = cur - base
        return {"baseline": base, "current": round(cur, 3), "delta": round(delta, 3),
                "n_assets": len(recent_copies),
                "status": ("DRIFT DETECTED — tone is loosening" if delta > 0.15
                           else "within tolerance")}

    def version(self) -> dict:
        return {"version": self.g["version"], "updated": self.g["updated"],
                "brands_encoded": len(self.g["brands"]),
                "brands_in_portfolio": self.g.get("portfolio_size", 400),
                "coverage_pct": round(100 * len(self.g["brands"])
                                    / self.g.get("portfolio_size", 400), 1),
                "markets_encoded": len([k for k in self.g["markets"]
                                        if not k.startswith("_")])}

    def evaluate(self, brand: str, market: str, copy: str,
                 context_tags: list | None = None, asset: dict | None = None) -> Verdict:
        t0 = time.perf_counter()
        b, m = self.brand(brand), self.market_rules(market)
        tags, asset = context_tags or [], asset or {}

        v = []
        v += self._check_claims(copy, b, m)
        v += self._check_tone(copy, b)
        v += self._check_adjacency(copy, tags, b)
        v += self._check_equity(copy, b)
        v += self._check_visual(asset, b)

        n_rules = (len(b["claims"]) + len(m["banned_phrases"]) +
                   len(m["restricted_terms"]) + len(b["tone"]["banned_words"]) +
                   len(b["banned_adjacencies"]) + len(b["equity_guardrails"]) + 3)

        hard = [x for x in v if x.severity == "hard"]
        verdict = "BLOCKED" if hard else ("REVISE" if v else "ALLOW")
        variant, ref, escalation = (None, None, None)
        if v:
            variant, ref, escalation = self._repair(copy, v, b, m)
            if variant and variant.strip().lower() == copy.strip().lower():
                variant = None

        return Verdict(verdict=verdict, brand=b["name"], market=market.upper(),
                       violations=v, approved_variant=variant,
                       substantiation_ref=ref,
                       latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                       rules_evaluated=n_rules, escalation=escalation)


# ==========================================================================
# EMBEDDED GENOME DATA
# ==========================================================================
GENOME_DATA = json.loads(r"""{
 "version": "1.0.0",
 "updated": "2026-08-12",
 "markets": {
  "IN": {
   "regulator": "ASCI",
   "banned_phrases": [
    "instantly",
    "overnight results",
    "guaranteed",
    "permanently cures"
   ],
   "restricted_terms": {
    "cures": "RG-IN-101",
    "clinically proven to cure": "RG-IN-101",
    "prevents disease": "RG-IN-104"
   }
  },
  "UK": {
   "regulator": "ASA",
   "banned_phrases": [
    "guaranteed",
    "miracle",
    "instantly"
   ],
   "restricted_terms": {
    "cures": "RG-UK-201",
    "prevents disease": "RG-UK-204"
   }
  },
  "_DEFAULT": {
   "regulator": "local advertising authority",
   "banned_phrases": [
    "guaranteed",
    "miracle"
   ],
   "restricted_terms": {
    "cures": "RG-XX-001"
   }
  }
 },
 "brands": {
  "dove": {
   "name": "Dove",
   "tone": {
    "descriptor": "warm, plain-spoken, never ironic or hyperbolic",
    "max_exclamations": 0,
    "allow_caps": false,
    "banned_words": [
     "flawless",
     "perfect",
     "anti-ageing",
     "slim",
     "obsessed"
    ],
    "substitutions": {
     "flawless": "healthy-looking",
     "perfect": "cared-for",
     "anti-ageing": "age-embracing",
     "slim": "comfortable",
     "obsessed": "delighted"
    }
   },
   "claims": [
    {
     "verb": "reduces hair fall",
     "approved_phrasing": "helps reduce hair fall with regular use",
     "max_pct": 0,
     "market_ok": true,
     "ref": "DV-2024-117 (clinical, 8-week, n=214)"
    },
    {
     "verb": "repairs damage",
     "approved_phrasing": "helps repair the look of damage",
     "max_pct": 0,
     "market_ok": true,
     "ref": "DV-2023-088 (instrumental)"
    }
   ],
   "banned_adjacencies": [
    {
     "rule": "AD-0901",
     "topic": "weight loss or body shrinking",
     "keywords": [
      "weight loss",
      "slimming",
      "shed kilos",
      "lose weight",
      "fat burn"
     ],
     "why": "It contradicts the Real Beauty equity built since 2004."
    },
    {
     "rule": "AD-0907",
     "topic": "cosmetic surgery or injectables",
     "keywords": [
      "botox",
      "filler",
      "surgery",
      "cosmetic procedure"
     ],
     "why": "Dove's position is care, not correction."
    }
   ],
   "equity_guardrails": [
    {
     "rule": "EQ-1101",
     "keywords": [
      "ugly",
      "fix your face",
      "before and after"
     ],
     "reason": "Deficit framing of appearance is a permanent-damage violation for Dove, not a temporary embarrassment."
    }
   ],
   "visual": {
    "palette": [
     "#FFFFFF",
     "#0A3C7D",
     "#F4C7C3",
     "#E8EEFA"
    ],
    "banned_objects": [
     "weighing scale",
     "measuring tape",
     "syringe"
    ],
    "min_logo_clear_space_pct": 12,
    "max_video_seconds": 30
   },
   "baseline_soft_rate": 0.1
  },
  "rexona": {
   "name": "Rexona",
   "tone": {
    "descriptor": "confident, energetic, performance-led; never mocking",
    "max_exclamations": 2,
    "allow_caps": true,
    "banned_words": [
     "smelly",
     "stink",
     "disgusting",
     "gross"
    ],
    "substitutions": {
     "smelly": "under pressure",
     "stink": "sweat",
     "disgusting": "intense",
     "gross": "tough"
    }
   },
   "claims": [
    {
     "verb": "protects",
     "approved_phrasing": "gives up to 72h protection",
     "max_pct": 0,
     "market_ok": true,
     "ref": "RX-2025-041 (72h protocol, n=180)"
    }
   ],
   "banned_adjacencies": [
    {
     "rule": "AD-0912",
     "topic": "body shaming or personal ridicule",
     "keywords": [
      "loser",
      "shame",
      "humiliate",
      "pathetic"
     ],
     "why": "The brand backs the person under pressure; it never mocks them."
    },
    {
     "rule": "AD-0915",
     "topic": "match-official controversy or refereeing decisions",
     "keywords": [
      "bad call",
      "blind ref",
      "wrong decision",
      "robbed"
     ],
     "why": "Taking a side in an officiating dispute converts a warm moment into a partisan one."
    }
   ],
   "equity_guardrails": [
    {
     "rule": "EQ-1108",
     "keywords": [
      "never sweat",
      "stops sweating completely"
     ],
     "reason": "Rexona's promise is performance under sweat, not its elimination. Overclaiming here breaks the tagline."
    }
   ],
   "visual": {
    "palette": [
     "#003DA5",
     "#FFFFFF",
     "#E4002B",
     "#111111"
    ],
    "banned_objects": [
     "referee card",
     "scoreboard dispute"
    ],
    "min_logo_clear_space_pct": 10,
    "max_video_seconds": 15
   },
   "baseline_soft_rate": 0.14
  },
  "lifebuoy": {
   "name": "Lifebuoy",
   "tone": {
    "descriptor": "protective, practical, community-minded; never fear-mongering",
    "max_exclamations": 1,
    "allow_caps": false,
    "banned_words": [
     "deadly",
     "killer",
     "lethal",
     "terrifying"
    ],
    "substitutions": {
     "deadly": "harmful",
     "killer": "harmful",
     "lethal": "harmful",
     "terrifying": "serious"
    }
   },
   "claims": [
    {
     "verb": "removes germs",
     "approved_phrasing": "helps remove 99.9% of germs",
     "max_pct": 99,
     "market_ok": true,
     "ref": "LB-2024-203 (in-vitro, EN1499)"
    }
   ],
   "banned_adjacencies": [
    {
     "rule": "AD-0920",
     "topic": "named disease outbreaks",
     "keywords": [
      "covid",
      "outbreak",
      "epidemic",
      "pandemic"
     ],
     "why": "Public-health events must not be used as a commercial hook."
    }
   ],
   "equity_guardrails": [
    {
     "rule": "EQ-1115",
     "keywords": [
      "your family will get sick",
      "protect or lose"
     ],
     "reason": "Fear-based parental framing is a permanent-damage violation for a hygiene brand."
    }
   ],
   "visual": {
    "palette": [
     "#E4002B",
     "#FFFFFF",
     "#00A0DF",
     "#1A1A1A"
    ],
    "banned_objects": [
     "hospital bed",
     "medical mask"
    ],
    "min_logo_clear_space_pct": 10,
    "max_video_seconds": 30
   },
   "baseline_soft_rate": 0.09
  }
 },
 "portfolio_size": 400
}""")


# ==========================================================================
# STREAMLIT UI & STYLING
# ==========================================================================


# ==========================================================================
# CULTURAL MOMENT ENGINE — the agent
# ==========================================================================
import os, re, json, time, math, random
from dataclasses import dataclass, field, asdict


# ══════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════
@dataclass
class MomentState:
    # input
    signal_text: str = ""
    brand: str = "rexona"
    markets: list = field(default_factory=lambda: ["IN"])

    # 01 signal
    signal: dict | None = None
    # 02 brand fit
    fit: dict | None = None
    # 03 brief
    brief: dict | None = None
    # 04 creative
    variants: list = field(default_factory=list)
    # 05 localisation
    localised: list = field(default_factory=list)
    # 06 gate
    gate: dict | None = None

    # control
    next_action: str = "detect"
    trace: list = field(default_factory=list)
    started: float = field(default_factory=time.perf_counter)
    # telemetry — the model prices inference per conversation, so the agent counts
    cost: dict = field(default_factory=lambda: {"llm_calls": 0, "genome_calls": 0,
                                                "est_inr": 0.0})

    INR_PER_LLM_CALL = 0.28          # Flash-tier, matches the value model

    def bill(self, llm: int = 0, genome: int = 0):
        self.cost["llm_calls"] += llm
        self.cost["genome_calls"] += genome
        self.cost["est_inr"] = round(self.cost["llm_calls"] * self.INR_PER_LLM_CALL, 3)

    def log(self, node: str, msg: str, deterministic: bool = True):
        self.trace.append({
            "t_ms": round((time.perf_counter() - self.started) * 1000, 1),
            "node": node, "msg": msg,
            "kind": "DETERMINISTIC" if deterministic else "LLM",
        })

    def to_json(self) -> str:
        d = asdict(self); d.pop("started", None)
        return json.dumps(d, indent=2, default=str)


# ══════════════════════════════════════════════════════════════
# LLM — optional, never in a decision path
# ══════════════════════════════════════════════════════════════
_MODEL = None

def _llm():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        _MODEL = genai.GenerativeModel("gemini-2.0-flash")
        return _MODEL
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════
# 01 SIGNAL DETECTOR — deterministic
# ══════════════════════════════════════════════════════════════
# STUB, AND LABELLED AS ONE. Production reads Brandwatch or Talkwalker, which is
# a PARTNER line in the build-vs-buy \u2014 there is no edge in rebuilding a listening
# tool. What this stub does is score an already-surfaced signal on observable
# features, so the arithmetic is visible rather than hidden inside a model. The
# weights below are illustrative and would be fitted on historical moment
# performance; they are not estimated.
VELOCITY_MARKERS = {
    "viral": 22, "trending": 18, "meme": 20, "everyone": 12, "blowing up": 25,
    "can't stop": 15, "millions": 18, "breaking": 14, "just happened": 16,
}
DECAY_HOURS = {"sport": 8, "awards": 14, "news": 10, "weather": 36,
               "festival": 72, "default": 18}

def _category(text: str) -> str:
    t = text.lower()
    for c, kws in {"sport": ["match", "goal", "referee", "official", "final", "cricket", "football"],
                   "awards": ["award", "oscar", "filmfare"],
                   "news": ["announced", "election", "budget"],
                   "weather": ["monsoon", "heatwave", "rain"],
                   "festival": ["diwali", "holi", "eid", "pongal"]}.items():
        if any(k in t for k in kws):
            return c
    return "default"

def signal_detector(s: MomentState) -> MomentState:
    text = s.signal_text
    low = text.lower()
    hits = [m for m in VELOCITY_MARKERS if m in low]
    velocity = min(100, 30 + sum(VELOCITY_MARKERS[m] for m in hits))
    cat = _category(text)
    window = DECAY_HOURS[cat]
    # a longer, more specific signal is more actionable
    specificity = min(100, 20 + len(text.split()) * 2)
    s.signal = {
        "category": cat, "velocity": velocity, "specificity": specificity,
        "window_hours": window, "markers": hits,
        "detected_at": "T+00:15",
        "verdict": "ACT" if velocity >= 55 else ("WATCH" if velocity >= 40 else "IGNORE"),
    }
    s.log("01 signal_detector",
          f"{cat} · velocity {velocity} · {window}h window · {s.signal['verdict']}")
    if s.signal["verdict"] == "ACT":
        s.next_action = "score"
    else:
        # Stop here and record WHY. A moment we deliberately did not chase is a
        # decision, and it belongs in the audit trail like any other.
        s.next_action = "gate"
        s.gate = {"decision": "NOT_PURSUED",
                  "why": (f"Velocity {velocity} is below the 55 action threshold "
                          f"({s.signal['verdict']}). No creative drafted, no spend committed."),
                  "rules": []}
        s.log("01 signal_detector", "below action threshold — no spend committed")
    return s


# ══════════════════════════════════════════════════════════════
# 02 BRAND-FIT SCORER — deterministic, calls the genome
# ══════════════════════════════════════════════════════════════
def brand_fit_scorer(s: MomentState, G: BrandGenome) -> MomentState:
    b = G.brand(s.brand)
    # the genome adjudicates the raw signal before a single asset is drafted
    v = G.evaluate(s.brand, s.markets[0], s.signal_text, [s.signal["category"]])
    s.bill(genome=1)
    hard = [x for x in v.violations if x.severity == "hard"]
    soft = [x for x in v.violations if x.severity == "soft"]

    # fit = velocity, less a penalty per genome violation on the SIGNAL itself
    penalty = len(hard) * 28 + len(soft) * 6
    fit = max(0, min(100, s.signal["velocity"] + s.signal["specificity"] // 4 - penalty))

    s.fit = {
        "score": fit, "brand": b["name"],
        "genome_verdict": v.verdict,
        "hard": [x.rule for x in hard], "soft": [x.rule for x in soft],
        "reasons": [x.reason for x in v.violations],
        "rules_evaluated": v.rules_evaluated, "latency_ms": v.latency_ms,
        "threshold": 60,
    }
    s.log("02 brand_fit_scorer",
          f"fit {fit}/100 · genome {v.verdict} · {v.rules_evaluated} rules in {v.latency_ms}ms"
          + (f" · hard {', '.join(x.rule for x in hard)}" if hard else ""))

    if hard:
        s.next_action = "gate"
        s.gate = {"decision": "BLOCKED_AT_SOURCE",
                  "why": "The signal itself violates the genome. No creative is drafted.",
                  "rules": [x.rule for x in hard]}
        s.log("02 brand_fit_scorer", "hard violation on the SIGNAL — nothing drafted")
    elif fit < 60:
        s.next_action = "gate"
        s.gate = {"decision": "BELOW_FIT_THRESHOLD",
                  "why": f"Brand fit {fit} is below the {s.fit['threshold']} threshold.",
                  "rules": []}
    else:
        s.next_action = "brief"
    return s


# ══════════════════════════════════════════════════════════════
# 03 MOMENT BRIEF — LLM, with deterministic fallback
# ══════════════════════════════════════════════════════════════
def moment_brief(s: MomentState, G: BrandGenome) -> MomentState:
    b = G.brand(s.brand)
    m = _llm()
    out, used_llm = None, False
    if m:
        prompt = (
            "You are drafting a one-paragraph creative brief for a live cultural "
            "moment. Return ONLY JSON with keys: angle, hook, why_now, tone_note.\n"
            "STRICT: no numbers or claims of any kind. No superlatives. "
            f"Brand voice: {b['tone']['descriptor']}. "
            f"Never use: {', '.join(b['tone']['banned_words'])}.\n\n"
            f"SIGNAL: {s.signal_text}\nBRAND: {b['name']}"
        )
        try:
            r = m.generate_content(prompt,
                generation_config={"response_mime_type": "application/json"})
            out = json.loads(r.text); used_llm = True; s.bill(llm=1)
        except Exception:
            out = None
    if out is None:
        out = {
            "angle": f"{b['name']} shows up where the pressure is, not where the noise is.",
            "hook": s.signal_text.strip().rstrip(".") + ".",
            "why_now": f"{s.signal['window_hours']}h window, velocity {s.signal['velocity']}.",
            "tone_note": b["tone"]["descriptor"],
        }
    s.brief = out
    s.log("03 moment_brief", "brief drafted" + ("" if used_llm else " (deterministic fallback)"),
          deterministic=not used_llm)
    s.next_action = "compose"
    return s


STOPWORDS_TRAILING = {"and","but","with","about","for","in","on","of","the","a",
                      "an","to","that","it","is","are","was","were","as","at"}

def _subject_of(signal: str) -> str:
    """
    Pull a short, publishable subject clause out of a raw listening signal.

    Listening desks speak in telemetry \u2014 "is trending", "everyone is posting",
    "going viral". None of that belongs in copy. Two passes: strip the telemetry
    vocabulary, then trim trailing connectives so we never end on "and" or
    "about", which an earlier regex-only version did.
    """
    t = re.split(r"[,;]| \u2014 ", signal.strip())[0]
    for pat in (r"\b(is|are|was|were)\s+(going\s+)?(viral|trending|blowing up)\b",
                r"\b(everyone|millions|fans|people)\s+\w+\s+\w+ing\b",
                r"\b(just happened|breaking news|breaking)\b",
                r"\bwent viral\b"):
        t = re.sub(pat, "", t, flags=re.I)
    words = [w for w in re.sub(r"\s{2,}", " ", t).strip(" ,.;\u2014-").split() if w]
    if not words:
        return "The moment"
    words = words[:10]
    while words and words[-1].lower().strip(".,") in STOPWORDS_TRAILING:
        words.pop()
    if not words:
        return "The moment"
    out = " ".join(words).strip(" ,.;")
    return out[:1].upper() + out[1:]


# ══════════════════════════════════════════════════════════════
# 04 CREATIVE COMPOSER — LLM, genome-constrained
# ══════════════════════════════════════════════════════════════
FORMATS = [("reel", 15), ("static", 0), ("story", 6)]

def creative_composer(s: MomentState, G: BrandGenome) -> MomentState:
    b = G.brand(s.brand)
    m = _llm()
    variants, used_llm = [], False

    if m:
        prompt = (
            "Write social copy for each format. Return ONLY a JSON list of objects "
            "with keys: format, copy. Max 18 words each.\n"
            "STRICT RULES:\n- No numbers, percentages or performance claims.\n"
            f"- Never use these words: {', '.join(b['tone']['banned_words'])}.\n"
            f"- Max {b['tone']['max_exclamations']} exclamation marks.\n"
            f"- Voice: {b['tone']['descriptor']}.\n\n"
            f"BRIEF: {json.dumps(s.brief)}\nFORMATS: {[f[0] for f in FORMATS]}"
        )
        try:
            r = m.generate_content(prompt,
                generation_config={"response_mime_type": "application/json"})
            got = json.loads(r.text)
            variants = [{"format": g.get("format", "static"), "copy": g.get("copy", "")}
                        for g in got][:3]
            used_llm = True; s.bill(llm=1)
        except Exception:
            variants = []

    if not variants:
        # DETERMINISTIC FALLBACK. An earlier version echoed the signal text back
        # three times, which meant the genome was adjudicating the INPUT rather
        # than three drafts \u2014 visibly not creative in a no-API-key demo.
        # These are per-format templates built from the brief, with the brand's
        # own approved phrasing where the genome has one on file.
        subject = _subject_of(s.signal_text)
        approved = next((c["approved_phrasing"] for c in b["claims"]
                         if c["market_ok"]), None)
        variants = [
            {"format": "reel",
             "copy": f"{subject}. Some things hold. {b['name']} is one of them."},
            {"format": "static",
             "copy": f"When {subject.lower()}, {b['name']} holds."},
            {"format": "story",
             "copy": (f"{subject}. {approved.capitalize()}." if approved
                      else f"{subject}. {b['name']}.")},
        ]

    # EVERY variant goes back through the genome before it can proceed
    checked = []
    for v in variants:
        verdict = G.evaluate(s.brand, s.markets[0], v["copy"], [s.signal["category"]])
        s.bill(genome=1)
        checked.append({
            **v,
            "verdict": verdict.verdict,
            "violations": [{"rule": x.rule, "severity": x.severity, "reason": x.reason}
                           for x in verdict.violations],
            "approved_variant": verdict.approved_variant,
            "escalation": verdict.escalation,
            "latency_ms": verdict.latency_ms,
        })
    s.variants = checked
    clean = sum(1 for c in checked if c["verdict"] == "ALLOW")
    revised = sum(1 for c in checked if c["verdict"] == "REVISE")
    blocked = sum(1 for c in checked if c["verdict"] == "BLOCKED")
    s.log("04 creative_composer",
          f"{len(checked)} variants · {clean} allow · {revised} revise · {blocked} blocked"
          + ("" if used_llm else " (deterministic fallback)"),
          deterministic=not used_llm)
    s.next_action = "localise"
    return s


# ══════════════════════════════════════════════════════════════
# 05 LOCALISER — deterministic, per-market regulatory overlay
# ══════════════════════════════════════════════════════════════
def localiser(s: MomentState, G: BrandGenome) -> MomentState:
    rows = []
    usable = [v for v in s.variants if v["verdict"] != "BLOCKED"]
    for mkt in s.markets:
        for v in usable:
            copy = v.get("approved_variant") or v["copy"]
            verdict = G.evaluate(s.brand, mkt, copy, [s.signal["category"]])
            s.bill(genome=1)
            rows.append({
                "market": mkt.upper(), "format": v["format"],
                "copy": verdict.approved_variant or copy,
                "verdict": verdict.verdict,
                "regulator": G.market_rules(mkt)["regulator"],
                "violations": [x.rule for x in verdict.violations],
                "escalation": verdict.escalation,
            })
    s.localised = rows
    ok = sum(1 for r in rows if r["verdict"] != "BLOCKED")
    s.log("05 localiser",
          f"{len(rows)} market-format pairs \u00b7 {ok} clear \u00b7 "
          f"{len(rows)-ok} blocked on local regulation \u00b7 "
          f"{s.cost['genome_calls']} genome calls, Rs {s.cost['est_inr']} inference")
    s.next_action = "gate"
    return s


# ══════════════════════════════════════════════════════════════
# 06 HUMAN GATE
# ══════════════════════════════════════════════════════════════
def human_gate(s: MomentState, G: BrandGenome | None = None,
               decision: str | None = None, actor: str = "brand.manager@hul") -> MomentState:
    """
    A real gate, not a display.

    `decision` is what the human actually chose \u2014 publish, revise or kill. It is
    written back to the genome via record_decision(), which is what makes the
    override-rate metric true rather than merely claimed. An earlier version
    printed AWAITING_HUMAN and recorded nothing, so the genome never learned
    whether its verdicts were being respected.
    """
    if s.gate:                       # already blocked upstream
        s.log("06 human_gate", f"{s.gate['decision']} — routed to human, nothing published")
        if G is not None and s.fit:
            rec = G.record_decision(
                type("V", (), {"brand": s.fit["brand"], "market": s.markets[0],
                               "verdict": s.fit["genome_verdict"],
                               "violations": [type("X", (), {"rule": r})()
                                              for r in s.fit.get("hard", [])]})(),
                human_action=decision or "kill", actor=actor,
                note=s.gate["decision"])
            s.gate["logged"] = True
            s.gate["override"] = rec["override"]
            s.log("06 human_gate",
                  f"decision logged \u00b7 override={rec['override']} \u00b7 actor {actor}")
        s.next_action = "done"
        return s
    ready = [r for r in s.localised if r["verdict"] != "BLOCKED"]
    escalations = [r for r in s.localised if r["escalation"]]
    s.gate = {
        "decision": "AWAITING_HUMAN",
        "ready": len(ready), "blocked": len(s.localised) - len(ready),
        "escalations": len(escalations),
        "why": "Tier-1 brands gate every publish regardless of confidence.",
        "elapsed": f"T+{4 if ready else 2}h",
    }
    if decision:
        s.gate["decision"] = decision.upper()
        s.gate["actor"] = actor
        if G is not None:
            rec = G.record_decision(
                type("V", (), {"brand": s.fit["brand"], "market": s.markets[0],
                               "verdict": "ALLOW", "violations": []})(),
                human_action=decision, actor=actor, note="moment engine")
            s.gate["logged"] = True
            s.gate["override"] = rec["override"]
    s.log("06 human_gate",
          f"{len(ready)} ready \u00b7 {len(s.localised)-len(ready)} blocked \u00b7 "
          f"{len(escalations)} escalations \u00b7 "
          + (f"human chose {decision}" if decision else "awaiting brand manager"))
    s.next_action = "done"
    return s


# ══════════════════════════════════════════════════════════════
# SUPERVISOR + GRAPH
# ══════════════════════════════════════════════════════════════
ROUTES = ["detect", "score", "brief", "compose", "localise", "gate"]

def supervisor(s: MomentState) -> MomentState:
    """Routes on state completeness, never on a model's opinion."""
    n = s.next_action
    if n == "done":
        return s
    if n in ("score", "brief", "compose", "localise") and not s.signal:
        s.next_action = "detect"
    elif n in ("brief", "compose", "localise") and not s.fit:
        s.next_action = "score"
    return s


def build_graph(G: BrandGenome):
    """LangGraph if available, otherwise an identical hand-rolled loop."""
    fns = {
        "detect":   lambda s: signal_detector(s),
        "score":    lambda s: brand_fit_scorer(s, G),
        "brief":    lambda s: moment_brief(s, G),
        "compose":  lambda s: creative_composer(s, G),
        "localise": lambda s: localiser(s, G),
        "gate":     lambda s: human_gate(s, G),
    }
    try:
        from langgraph.graph import StateGraph, END
        g = StateGraph(MomentState)
        for k, f in fns.items():
            g.add_node(k, f)
        g.add_node("supervisor", supervisor)
        g.set_entry_point("supervisor")
        g.add_conditional_edges("supervisor", lambda s: s.next_action,
                                {**{k: k for k in fns}, "done": END})
        for k in fns:
            g.add_edge(k, "supervisor")
        return g.compile(), "langgraph"
    except Exception:
        class Fallback:
            def invoke(self, s, max_hops=10):
                for _ in range(max_hops):
                    s = supervisor(s)
                    if s.next_action == "done":
                        break
                    f = fns.get(s.next_action)
                    if not f:
                        break
                    s = f(s)
                return s
        return Fallback(), "fallback"


def run(signal_text: str, brand: str = "rexona", markets: list | None = None,
        G: BrandGenome | None = None) -> MomentState:
    G = G or BrandGenome()
    app, backend = build_graph(G)
    s = MomentState(signal_text=signal_text, brand=brand,
                    markets=markets or ["IN", "UK"])
    s.log("supervisor", f"graph backend: {backend}")
    out = app.invoke(s)
    # LangGraph returns a dict of the dataclass fields; normalise so callers
    # always get a MomentState whichever backend ran.
    if isinstance(out, dict):
        st = MomentState()
        for k, v in out.items():
            if hasattr(st, k):
                setattr(st, k, v)
        return st
    return out


st.set_page_config(page_title="Brand Genome · Project NEXT",
                   page_icon="🧬", layout="wide",
                   initial_sidebar_state="expanded")
G = BrandGenome()

VERDICT_STYLE = {
    "ALLOW":   ("#00786F", "#E6F4F2", "✓", "Cleared for publication"),
    "REVISE":  ("#B26A00", "#FDF3E3", "!", "Publishable after the genome's repair"),
    "BLOCKED": ("#B3261E", "#FCEBE9", "✕", "Cannot ship — human decision required"),
}
DIM_LABEL = {"claims": "Claims", "tone": "Tone", "adjacency": "Adjacency",
             "equity": "Equity", "visual": "Visual", "video_audio": "Spoken track"}

U_MARK = """
<svg viewBox="0 0 64 64" class="umark" aria-hidden="true">
  <path d="M14 8 L14 36 A18 18 0 0 0 50 36 L50 8" fill="none"
        stroke="currentColor" stroke-width="7" stroke-linecap="round"/>
  <circle cx="24" cy="20" r="2.6" fill="currentColor"/>
  <circle cx="40" cy="20" r="2.6" fill="currentColor"/>
  <circle cx="32" cy="31" r="2.6" fill="currentColor"/>
  <circle cx="24" cy="42" r="2.6" fill="currentColor"/>
  <circle cx="40" cy="42" r="2.6" fill="currentColor"/>
  <path d="M28 55 h8" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
</svg>"""

# Safe, isolated CSS styling including explicit fixes for expander background/text shading
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root{
  --hul:#035597; --hul-deep:#0F0E9A; --ink:#0B1B3A; --ink-2:#5C6B85;
  --line:#E1E8F5; --surface:#FFFFFF; --canvas:#F5F8FD; --accent:#1B4DD1;
}

.stApp {
  background: var(--canvas);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Masthead */
.mast {
  background: linear-gradient(115deg, #06255C 0%, var(--hul) 55%, #0B6BB8 100%);
  border-radius: 16px; padding: 24px 28px; display: flex; align-items: center; gap: 20px;
  box-shadow: 0 10px 25px -15px rgba(3,85,151,.5); margin-bottom: 20px;
}
.mast * { color: #fff !important; }
.umark { width: 40px; height: 40px; color: #fff; flex: 0 0 40px; opacity: .95; }
.mast__title { font-size: 24px; font-weight: 800; letter-spacing: -.5px; line-height: 1.1; }
.mast__sub { font-size: 13px; opacity: .82; margin-top: 4px; font-weight: 400; }
.mast__badge { margin-left: auto; text-align: right; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; opacity: .8; line-height: 1.6; }
.mast__badge b { display: block; font-family: 'JetBrains Mono', monospace; font-size: 12px; opacity: 1; }

/* Section Headers */
.sect {
  font-size: 11px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-2); margin: 24px 0 10px; display: flex; align-items: center; gap: 10px;
}
.sect:after { content: ""; flex: 1; height: 1px; background: var(--line); }

/* Verdict Hero Card */
.bg-verdict {
  display: flex; align-items: center; gap: 20px; padding: 20px 24px; border-radius: 14px;
  background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--vc);
  box-shadow: 0 8px 24px -18px rgba(11,27,58, .4); margin-bottom: 16px;
}
.bg-verdict__mark {
  width: 48px; height: 48px; border-radius: 12px; background: var(--vbg);
  display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800;
  color: var(--vc); flex: 0 0 48px;
}
.bg-verdict__label { font-size: 22px; font-weight: 800; letter-spacing: .04em; color: var(--vc); }
.bg-verdict__sub { font-size: 13px; color: var(--ink-2); margin-top: 2px; }
.bg-verdict__rail { margin-left: auto; display: flex; gap: 28px; text-align: right; }
.bg-rail__n { font-size: 20px; font-weight: 700; color: var(--ink); font-family: 'JetBrains Mono', monospace; display: block; }
.bg-rail__l { font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); margin-top: 2px; display: block; }

/* Violation Cards */
.bg-viol {
  display: flex; background: var(--surface); border: 1px solid var(--line);
  border-radius: 12px; margin-bottom: 8px; overflow: hidden;
  box-shadow: 0 3px 10px -10px rgba(11,27,58, .4);
}
.bg-viol__bar { width: 5px; flex: 0 0 5px; background: var(--sc); }
.bg-viol__body { padding: 12px 16px; flex: 1; }
.bg-viol__head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.bg-sev { font-size: 10px; font-weight: 800; letter-spacing: .1em; padding: 2px 6px; border-radius: 4px; background: var(--sbg); color: var(--sc); }
.bg-rulechip { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; background: #EEF3FC; color: var(--hul); padding: 2px 6px; border-radius: 4px; }
.bg-dim { font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
.bg-viol__reason { font-size: 14px; line-height: 1.5; color: var(--ink); margin: 0; }
.bg-ev { display: inline-block; margin-top: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: #FFF4F2; border: 1px dashed #F0C4BC; color: #8C2C22; padding: 2px 8px; border-radius: 4px; }

/* Repair Diff */
.bg-diff { display: grid; grid-template-columns: 1fr 40px 1fr; gap: 0; align-items: stretch; margin-bottom: 16px; }
.bg-diff__col { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.bg-diff__col--out { border-color: #CFE7E2; background: #F4FBF9; }
.bg-diff__lab { font-size: 10px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); margin-bottom: 6px; }
.bg-diff__txt { font-size: 14px; line-height: 1.6; color: var(--ink); }
.bg-diff__arrow { display: flex; align-items: center; justify-content: center; font-size: 18px; color: var(--ink-2); }
.bg-subref { margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00786F; }

/* Escalation Notice */
.bg-esc { background: #FFFBF2; border: 1px solid #F0DDB8; border-left: 5px solid #B26A00; border-radius: 12px; padding: 14px 18px; font-size: 14px; line-height: 1.5; color: var(--ink); }
.bg-esc b { color: #8A5200; letter-spacing: .08em; font-size: 10px; text-transform: uppercase; display: block; margin-bottom: 4px; }

/* Fix Expander Shading / Contrast Issues */
[data-testid="stExpander"] {
  background-color: #FFFFFF !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(11,27,58,0.04) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
  color: var(--ink) !important;
  font-weight: 600 !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] { background: #06255C !important; }
[data-testid="stSidebar"] * { color: #D9E4F7 !important; }
.sb-head { display: flex; align-items: center; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,.15); margin-bottom: 14px; }
.sb-head .umark { width: 28px; height: 28px; flex: 0 0 28px; }
.sb-title { font-size: 15px; font-weight: 800; color: #fff; }
.sb-ver { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #8FAAD6; }
.sb-lab { font-size: 10px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #7E9BCC; margin: 16px 0 8px; }
.sb-card { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); border-radius: 8px; padding: 10px 12px; margin-bottom: 6px; }
.sb-card b { font-size: 13px; color: #fff; }
.sb-card small { display: block; font-size: 11px; color: #9FB8DE; margin-top: 2px; }
.sw { display: flex; gap: 3px; margin-top: 6px; }
.sw i { width: 12px; height: 12px; border-radius: 3px; display: block; border: 1px solid rgba(255,255,255, .3); }
.sb-foot { margin-top: 16px; padding: 12px; border-radius: 8px; background: rgba(27,77,209,.25); border: 1px solid rgba(120,165,240,.3); font-size: 11px; line-height: 1.5; color: #C7D9F6; }
.sb-foot b { color: #fff; }

.empty-state { background: var(--surface); border: 1px dashed var(--line); border-radius: 12px; padding: 30px; text-align: center; color: var(--ink-2); font-size: 14px; }
</style>
""", unsafe_allow_html=True)

PRESETS = {
    "— pick a scenario —": ("dove", "IN", "", []),
    "The demo moment (Dove, IN)": ("dove", "IN",
        "Reduces hair fall by 90% instantly! Get that FLAWLESS, perfect hair "
        "you're obsessed with — the ultimate weight loss for your hair.",
        ["monsoon", "hair_care"]),
    "Repairable — claims + tone only (Dove, IN)": ("dove", "IN",
        "Reduces hair fall by 90% instantly! Get that FLAWLESS, perfect hair "
        "you're obsessed with.", ["hair_care"]),
    "Regulatory escalation (Lifebuoy, IN)": ("lifebuoy", "IN",
        "Lifebuoy cures germs and prevents disease. Deadly bacteria don't stand a chance.",
        ["hygiene"]),
    "The Rexona moment, done wrong": ("rexona", "IN",
        "That was a bad call by the ref! Rexona: you'll never sweat again, guaranteed!!!",
        ["football", "viral", "fourth_official"]),
    "The Rexona moment, done right": ("rexona", "IN",
        "Six added minutes. The one person who cannot lose their cool. "
        "Rexona gives up to 72h protection.", ["football", "fourth_official"]),
}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"""<div class='sb-head'>{U_MARK}
      <div><div class='sb-title'>Brand Genome</div>
      <div class='sb-ver'>v{G.g['version']} · {G.g['updated']}</div></div></div>""",
                unsafe_allow_html=True)

    ver = G.version()
    st.markdown(f"""<div class='sb-lab'>Portfolio coverage</div>
      <div class='sb-card'><b>{ver['brands_encoded']} of {ver['brands_in_portfolio']} brands</b>
      <small>{ver['coverage_pct']}% encoded · {ver['markets_encoded']} markets live</small></div>""",
                unsafe_allow_html=True)

    st.markdown("<div class='sb-lab'>Encoded brands</div>", unsafe_allow_html=True)
    for b in G.g["brands"].values():
        sw = "".join(f"<i style='background:{c}'></i>" for c in b["visual"]["palette"])
        st.markdown(f"""<div class='sb-card'><b>{b['name']}</b>
          <small>{len(b['claims'])} claims · {len(b['banned_adjacencies'])} adjacencies
          · {len(b['equity_guardrails'])} guardrails</small>
          <div class='sw'>{sw}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div class='sb-lab'>Markets &amp; regulators</div>", unsafe_allow_html=True)
    for k, m in G.g["markets"].items():
        if not k.startswith("_"):
            st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.06);'><code>{k}</code><span>{m['regulator']}</span></div>", unsafe_allow_html=True)

    st.markdown("""<div class='sb-foot'><b>Deterministic by design.</b><br>
      No LLM in the adjudication path. The model generates;
      the genome adjudicates. Never the reverse.</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- masthead
st.markdown(f"""<div class='mast'>{U_MARK}
  <div><div class='mast__title'>Brand Genome</div>
  <div class='mast__sub'>The horizontal layer every creative agent calls before it acts</div></div>
  <div class='mast__badge'>Project NEXT<b>TechTonic S8</b></div></div>""",
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS — the governance layer, and the agent that calls it
# ══════════════════════════════════════════════════════════════════════════════
TAB_GENOME, TAB_AGENT = st.tabs([
    "  BRAND GENOME  ·  governance layer  ",
    "  CULTURAL MOMENT ENGINE  ·  the agent  "])

with TAB_AGENT:
    st.markdown("<div class='sect'>Live cultural moment</div>", unsafe_allow_html=True)
    st.caption("Six nodes under a LangGraph supervisor. Nodes 01, 02 and 05 are "
               "deterministic and call the genome; only the brief and the copy touch "
               "a language model. Nothing publishes without a human, and the human's "
               "decision is written back to the genome.")

    A_PRESETS = {
        "\u2014 pick a signal \u2014": ("", "rexona", ["IN"]),
        "The Rexona moment \u2014 runs clean": (
            "The fourth official raised the board and the Rexona logo went viral, "
            "everyone is sharing the meme from the final", "rexona", ["IN", "UK"]),
        "Same moment, done wrong \u2014 blocked at source": (
            "Everyone is sharing this viral meme, it is blowing up, millions saw the "
            "bad call by the blind ref and Rexona says you never sweat again guaranteed",
            "rexona", ["IN"]),
        "Monsoon hair \u2014 Dove": (
            "Monsoon frizz is trending, everyone is posting about hair fall in the rain",
            "dove", ["IN"]),
        "Low velocity \u2014 not pursued": ("Someone mentioned soap", "dove", ["IN"]),
    }
    ap = st.selectbox("Signal", list(A_PRESETS.keys()), key="ag_p",
                      label_visibility="collapsed")
    sig_d, br_d, mk_d = A_PRESETS[ap]

    c1, c2 = st.columns([3, 1])
    with c1:
        sig = st.text_area("Incoming signal", value=sig_d, height=88, key="ag_s",
                           placeholder="Paste what social listening surfaced\u2026")
    with c2:
        _names = [b["name"] for b in G.g["brands"].values()]
        _keys = list(G.g["brands"].keys())
        br = st.selectbox("Brand", _names, index=_keys.index(br_d), key="ag_b")
        mkts = st.multiselect("Markets",
                              [k for k in G.g["markets"] if not k.startswith("_")],
                              default=mk_d, key="ag_m")
    hd = st.radio("Human decision at the gate",
                  ["awaiting", "publish", "revise", "kill"], horizontal=True, key="ag_h")

    if st.button("Run the agent", type="primary", use_container_width=True,
                 key="ag_run") and sig.strip():
        s = run(sig, brand=br, markets=mkts or ["IN"], G=G)
        if hd != "awaiting":
            s = human_gate(s, G, decision=hd)

        st.markdown("<div class='sect'>Node trace</div>", unsafe_allow_html=True)
        for t in s.trace:
            tag = "#00786F" if t["kind"] == "DETERMINISTIC" else "#1B4DD1"
            st.markdown(
                f"<div style='display:flex;gap:14px;align-items:baseline;padding:5px 0;"
                f"border-bottom:1px solid #EDF1F8'>"
                f"<code style='color:#5A6478;font-size:11px;min-width:60px'>{t['t_ms']}ms</code>"
                f"<span style='background:{tag};color:#fff;font-size:9px;font-weight:700;"
                f"padding:2px 7px;border-radius:3px;letter-spacing:.5px'>{t['kind']}</span>"
                f"<b style='font-size:12px;min-width:168px'>{t['node']}</b>"
                f"<span style='font-size:12px;color:#1A1A2E'>{t['msg']}</span></div>",
                unsafe_allow_html=True)

        g = s.gate or {}
        dec = g.get("decision", "\u2014")
        col = {"AWAITING_HUMAN": "#B26A00", "BLOCKED_AT_SOURCE": "#B3261E",
               "NOT_PURSUED": "#5A6478", "BELOW_FIT_THRESHOLD": "#5A6478",
               "PUBLISH": "#00786F", "REVISE": "#B26A00", "KILL": "#B3261E"}.get(dec, "#5A6478")
        st.markdown(
            f"<div style='margin-top:16px;padding:16px 20px;border-radius:6px;"
            f"background:{col};color:#fff'><div style='font-size:19px;font-weight:700;"
            f"letter-spacing:.5px'>{dec.replace('_',' ')}</div>"
            f"<div style='font-size:12.5px;opacity:.92;margin-top:4px'>{g.get('why','')}</div>"
            f"</div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        if s.fit:
            m1.metric("Brand fit", f"{s.fit['score']}/100")
            m2.metric("Genome", s.fit["genome_verdict"])
        m3.metric("Genome calls", s.cost["genome_calls"])
        m4.metric("Inference", f"Rs {s.cost['est_inr']}")

        if g.get("logged"):
            st.caption(f"Decision written to the genome \u00b7 override={g.get('override')} "
                       f"\u00b7 override rate now "
                       f"{G.override_rate(s.fit['brand'])['override_rate'] if s.fit else 0}")

        if g.get("rules"):
            st.markdown("**Blocked on:** " + " \u00b7 ".join(f"`{r}`" for r in g["rules"]))
            for r in (s.fit or {}).get("reasons", []):
                st.caption("\u2022 " + r)

        if s.localised:
            st.markdown("<div class='sect'>Localised output</div>", unsafe_allow_html=True)
            import pandas as _pd
            st.dataframe(_pd.DataFrame([{
                "Market": r["market"], "Regulator": r["regulator"], "Format": r["format"],
                "Verdict": r["verdict"], "Copy": r["copy"],
                "Rules": ", ".join(r["violations"]) or "\u2014"} for r in s.localised]),
                use_container_width=True, hide_index=True)

        with st.expander("Full agent state \u2014 what the audit trail stores"):
            st.code(s.to_json(), language="json")

with TAB_GENOME:

    # ---------------------------------------------------------------- input section
    st.markdown("<div class='sect'>Submit an asset</div>", unsafe_allow_html=True)
    preset = st.selectbox("Scenario", list(PRESETS.keys()), label_visibility="collapsed")
    pb, pm, pc, pt = PRESETS[preset]

    c1, c2 = st.columns([3, 1.15], gap="medium")
    with c1:
        copy = st.text_area("Proposed copy", value=pc, height=120,
                            placeholder="Paste what the creative agent produced…")
    with c2:
        brand = st.selectbox("Brand", [b["name"] for b in G.g["brands"].values()],
                             index=list(G.g["brands"]).index(pb))
        market = st.selectbox("Market", [k for k in G.g["markets"] if not k.startswith("_")],
                              index=0 if pm == "IN" else 1)
        tags = st.text_input("Context tags", value=", ".join(pt))

    go = st.button("Evaluate against genome", type="primary", use_container_width=True)

    # ---------------------------------------------------------------- evaluation results
    if go and copy.strip():
        v = G.evaluate(brand, market, copy,
                       [t.strip() for t in tags.split(",") if t.strip()])
        vc, vbg, glyph, blurb = VERDICT_STYLE[v.verdict]
        hard = sum(1 for x in v.violations if x.severity == "hard")
        reg = G.market_rules(market)["regulator"]

        st.markdown("<div class='sect'>Adjudication</div>", unsafe_allow_html=True)
        st.markdown(f"""
          <div class='bg-verdict' style='--vc:{vc};--vbg:{vbg}'>
            <div class='bg-verdict__mark'>{glyph}</div>
            <div><div class='bg-verdict__label'>{v.verdict}</div>
              <div class='bg-verdict__sub'>{blurb} · {v.brand} · {v.market} · {reg}</div></div>
            <div class='bg-verdict__rail'>
              <div><span class='bg-rail__n'>{v.rules_evaluated}</span><span class='bg-rail__l'>Rules</span></div>
              <div><span class='bg-rail__n'>{hard}</span><span class='bg-rail__l'>Hard</span></div>
              <div><span class='bg-rail__n'>{len(v.violations) - hard}</span><span class='bg-rail__l'>Soft</span></div>
              <div><span class='bg-rail__n'>{v.latency_ms}</span><span class='bg-rail__l'>ms</span></div>
            </div></div>""", unsafe_allow_html=True)

        if v.violations:
            st.markdown(f"<div class='sect'>Violations · {len(v.violations)}</div>",
                        unsafe_allow_html=True)
            cards = []
            for x in sorted(v.violations, key=lambda x: x.severity != "hard"):
                sc, sbg = ("#B3261E", "#FCEBE9") if x.severity == "hard" else ("#B26A00", "#FDF3E3")
                ev = (f"<span class='bg-ev'>matched “{html.escape(x.evidence)}”</span>"
                      if x.evidence else "")
                cards.append(f"""
                  <div class='bg-viol' style='--sc:{sc};--sbg:{sbg}'>
                    <div class='bg-viol__bar'></div>
                    <div class='bg-viol__body'>
                      <div class='bg-viol__head'>
                        <span class='bg-sev'>{x.severity.upper()}</span>
                        <span class='bg-rulechip'>{x.rule}</span>
                        <span class='bg-dim'>{DIM_LABEL.get(x.dimension, x.dimension)}</span>
                      </div>
                      <p class='bg-viol__reason'>{html.escape(x.reason)}</p>{ev}
                    </div></div>""")
            st.markdown("".join(cards), unsafe_allow_html=True)

        if v.approved_variant:
            st.markdown("<div class='sect'>Deterministic repair</div>", unsafe_allow_html=True)
            ref = (f"<div class='bg-subref'>Substantiation on file · {html.escape(v.substantiation_ref)}</div>"
                   if v.substantiation_ref else "")
            st.markdown(f"""
              <div class='bg-diff'>
                <div class='bg-diff__col'><div class='bg-diff__lab'>Submitted</div>
                  <div class='bg-diff__txt'>{html.escape(copy.strip())}</div></div>
                <div class='bg-diff__arrow'>→</div>
                <div class='bg-diff__col bg-diff__col--out'><div class='bg-diff__lab'>Genome-approved variant</div>
                  <div class='bg-diff__txt'>{html.escape(v.approved_variant)}</div>{ref}</div>
              </div>""", unsafe_allow_html=True)

        if v.escalation:
            st.markdown("<div class='sect'>Escalation</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='bg-esc'><b>Human decision required</b>"
                        f"{html.escape(v.escalation)}</div>", unsafe_allow_html=True)

        with st.expander("Audit record — what the trail stores"):
            st.code(v.to_json(), language="json")
    else:
        st.markdown("<div class='sect'>Adjudication</div>", unsafe_allow_html=True)
        st.markdown("<div class='empty-state'>Pick a scenario or paste copy above, "
                    "then click <b>Evaluate against genome</b> to run adjudication.</div>", unsafe_allow_html=True)
