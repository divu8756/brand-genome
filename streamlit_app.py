"""
streamlit_app.py — Brand Genome visual demo.

    streamlit run streamlit_app.py

Deployed at Streamlit Community Cloud. No PYTHONPATH needed: the repo root is
added to sys.path below so `core` imports cleanly from any working directory.

The demo moment: let the audience read an attractive, plausible post and like it.
Then show the genome blocking it, naming the rule, and returning the corrected
version. The gap between what a naked model produces and what a governed one
produces is the entire argument, and it lands in about fifteen seconds.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from core.genome import BrandGenome

st.set_page_config(page_title="Brand Genome", page_icon="🧬", layout="wide")
G = BrandGenome()

st.markdown("""
<style>
  .stApp { background:#FAFBFE; }
  [data-testid="stSidebar"] { background:#0A1F5C; }
  [data-testid="stSidebar"] * { color:#E8EEFA !important; }
  .t  { font-size:30px; font-weight:700; color:#0A1F5C; margin-bottom:0; }
  .s  { color:#5A6478; font-size:14px; margin-top:2px; }
  .v  { padding:10px 16px; border-radius:4px; font-weight:700; font-size:20px;
        letter-spacing:1px; display:inline-block; }
  .rule { font-family:Consolas,monospace; font-size:12px; font-weight:700; }
</style>""", unsafe_allow_html=True)

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

with st.sidebar:
    st.markdown("### Brand Genome")
    st.caption(f"v{G.g['version']} · updated {G.g['updated']}")
    st.markdown("---")
    st.markdown("**Encoded brands**")
    for k, b in G.g["brands"].items():
        st.caption(f"• {b['name']} — {len(b['claims'])} claims, "
                   f"{len(b['banned_adjacencies'])} adjacencies, "
                   f"{len(b['equity_guardrails'])} guardrails")
    st.markdown("**Markets**")
    for k, m in G.g["markets"].items():
        if not k.startswith("_"):
            st.caption(f"• {k} — {m['regulator']}")
    st.markdown("---")
    st.caption("**Deterministic.** No LLM in the adjudication path. "
               "The model generates; the genome adjudicates.")

st.markdown("<div class='t'>Brand Genome</div>", unsafe_allow_html=True)
st.markdown("<div class='s'>The horizontal layer every agent calls before it acts "
            "· Project NEXT · HUL TechTonic Season 8</div>", unsafe_allow_html=True)
st.markdown("")

preset = st.selectbox("Scenario", list(PRESETS.keys()))
pb, pm, pc, pt = PRESETS[preset]

c1, c2 = st.columns([3, 1])
with c1:
    copy = st.text_area("Proposed copy", value=pc, height=110,
                        placeholder="Paste what the creative agent produced…")
with c2:
    brand = st.selectbox("Brand", [b["name"] for b in G.g["brands"].values()],
                         index=list(G.g["brands"]).index(pb))
    market = st.selectbox("Market", [k for k in G.g["markets"] if not k.startswith("_")],
                          index=0 if pm == "IN" else 1)
    tags = st.text_input("Context tags", value=", ".join(pt))

if st.button("Evaluate against genome", type="primary", use_container_width=True) and copy.strip():
    v = G.evaluate(brand, market, copy, [t.strip() for t in tags.split(",") if t.strip()])
    col = {"BLOCKED": "#C0392B", "REVISE": "#C87A00", "ALLOW": "#00807D"}[v.verdict]
    st.markdown(f"<span class='v' style='background:{col};color:#fff'>{v.verdict}</span>",
                unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Rules evaluated", v.rules_evaluated)
    b.metric("Latency", f"{v.latency_ms} ms")
    c.metric("Violations", len(v.violations))

    if v.violations:
        st.markdown("#### Violations")
        for x in v.violations:
            tag = "🔴 HARD" if x.severity == "hard" else "🟡 soft"
            ev = f" · matched `{x.evidence}`" if x.evidence else ""
            st.markdown(f"{tag} &nbsp; <span class='rule'>{x.rule}</span> &nbsp; "
                        f"**{x.dimension}** — {x.reason}{ev}", unsafe_allow_html=True)

    if v.approved_variant:
        st.markdown("#### Approved variant")
        st.success(v.approved_variant)
        if v.substantiation_ref:
            st.caption(f"Substantiation on file: {v.substantiation_ref}")
    if v.escalation:
        st.markdown("#### Escalation")
        st.warning(v.escalation)

    with st.expander("Audit record (what the trail stores)"):
        st.code(v.to_json(), language="json")
