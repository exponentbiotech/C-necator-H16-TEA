#!/usr/bin/env python3
"""
Leatherback Fairfield TEA Dashboard — v10
=========================================
Dedicated Fairfield model built from the April 2026 site handoff and PDF.

Scope:
  - Facility: former AB InBev brewery, 3101 Busch Dr, Fairfield CA
  - Fixed phase sizes: 50,000 L / 150,000 L / 400,000 L
  - Continuous fermentation only in the Streamlit UI: 24 h HRT, 85 % uptime,
    per-scenario CDW titer and PHB sliders (v7/v9 base 60 g/L, 60 % PHB).
  - DSP pathway selector (v9): NaOCl hypochlorite (Biopol-era baseline),
    NaOH hot alkali, Mechanical + enzymatic (modern CMO standard).
    Default = Mechanical + enzymatic. Each pathway has its own extraction
    cost, CDW-side DSP cost, and phase-scaled CapEx adder.
  - PHBV production (v9): global toggle drives both S1 and S2. When ON,
    co-substrate feed (propionate / valerate / levulinate) drives HV
    incorporation; PHBV selling price auto-scales with HV content
    (Tianan / Kaneka / Danimer benchmarks) with manual override.
  - Scenarios modeled: S1 (Jelly Belly COD) and S2 (70/30 JB COD + DLP)
  - Finance: 9 % discount rate, 10-year horizon
  - CapEx sliders: acquisition cost + added major CapEx + (v9) DSP-pathway
    CapEx adder where applicable

Revision history:
  v5 — Original Fairfield biorefinery model (feed-grade SCP + PHA).
       Default feed-grade SCP price was set to $0.46/kg, which was sourced
       from a commodity soybean-meal reference and not reconciled against
       bacterial-SCP commercial benchmarks. That value sat below the model's
       own computed SCP MSP, which meant the base-case revenue figure was
       understated across every phase and scenario.
  v6 — Corrected SCP default and introduced an exploratory human-grade
       protein scenario. v6 is retained in the repository for reference only.
  v7 — This revision. The SCP+PHA biorefinery thesis is the sole modeled
       scope. The human-grade-protein scenario is removed from the model
       (revenue-contributing scenarios are S1 and S2 only). The default
       feed-grade SCP selling price is set to $2.00/kg, anchored to fishmeal
       (FRED PFISHUSDM, 2024-2025), Calysta FeedKind, and Unibio UniProtein
       commercial benchmarks. The SCP selling-price slider range is widened
       to $0.30-$8.00/kg so that downside stress tests and specialty upside
       can both be examined.

       v7 also locks both modeled scenarios to a shared biology base case:
       60 g/L CDW titer and 60% PHB content. The earlier v5/v6 S1 design-
       basis titer of 35 g/L ("conservative Year 1") has been retired in
       favor of a single-anchor 60 g/L base across S1 and S2, and the
       earlier PHB split (S1 60% / S2 40%) has been retired in favor of a
       single-anchor 60% PHB across both scenarios. The practical effect
       is that S1 and S2 now produce the same PHA and SCP tonnage by
       construction; they are differentiated only by cost-side biology
       (nitrogen reduction intensity, carbon recovery, feedstock mix),
       which keeps the scenario comparison a genuine apples-to-apples
       operating-cost study rather than a composite of product-slate and
       operating-cost effects. The 35 g/L downside titer and the old
       60%/40% PHB splits remain accessible through the sidebar sliders
       for sensitivity work. All other v5 functionality is preserved.

       v7 also documents two defects identified in the
       Fairfield_TEA_v7_Final.pdf site handoff document, both on page 7:
       (1) the $0.46/kg SCP selling-price value was quoted with a fishmeal-
       parity rationale but numerically anchored to the soybean-meal
       commodity band (~4x below fishmeal); (2) the stated Phase III annual
       gross CDW of ~10,700 MT/yr does not match the handoff's own formula
       (306,000 L x 35 g/L x 8,760/24 / 1e6), which actually evaluates to
       ~3,909 MT/yr (a 2.74x arithmetic inflation). Defect 1 was transcribed
       into v5 and is corrected in v7. Defect 2 did not propagate into v5/v7
       because the TEA computes annual CDW from first principles; it is
       flagged here for correction at the handoff source.

  v8 — Historically added a fed-batch operating-mode alternative in the
       sidebar. The fed-batch UI was later removed; the dashboard now
       exposes continuous fermentation only. The compute layer still
       accepts operating_mode overrides for scripted analyses.

  v9 — Two extensions to v8:

       (a) DSP pathway selector. v7 and v8 implicitly modeled a Biopol-era
       NaOCl hypochlorite extraction flowsheet at ~$1.80/kg sellable PHA
       all-in (centrifuge + dry + hypochlorite digestion). v9 exposes three
       literature-anchored pathways with their own extraction cost, CDW-
       side DSP cost, and phase-scaled CapEx adder:

         * NaOCl hypochlorite (v7/v8 baseline, conservative): $0.638/kg
           PHA extraction + $0.42/kg CDW downstream, no CapEx adder,
           Mw-degrading, high-salinity wastewater caveat.
         * NaOH hot alkali (Hahn 1994, Choi 1997 variant): $0.45/kg PHA
           extraction + $0.38/kg CDW, +$1.5M Phase III CapEx for alkali-
           resistant vessels, Mw-degrading.
         * Mechanical + enzymatic (high-pressure homogenization +
           protease / lipase polishing, Kapritchkoff 2006 / Jacquel
           2008 variant):
           $0.25/kg PHA + $0.30/kg CDW, +$6M Phase III CapEx, Mw-
           preserving, requires high-density biomass (>100 g/L) to work
           well. Default v9 pathway.

       The default shift from NaOCl to mechanical+enzymatic lowers the
       v9 base-case MSP by roughly $0.40/kg PHA vs v8. Users who want
       to reproduce v8 numbers exactly can flip the DSP pathway selector
       to "NaOCl hypochlorite".

       (b) Explicit PHBV production. v7 and v8 carried a fixed 70/30
       PHB/PHBV blend at fixed prices ($5.50 / $7.00), which ignored
       both the biology (NCIMB 11599 produces PHBV only with co-feeding
       of short-chain organic acid precursors) and the price-vs-HV
       scaling seen in the commercial PHBV market. v9 adds a global
       PHBV toggle. When OFF, behavior matches v8 exactly. When ON:
         * A co-substrate selector (propionate / valerate / levulinate,
           default propionate). Propionate is the industry-standard
           choice (Doi 1988, Madison-Huisman 1999; Tianan Biopolymer,
           Kaneka disclosures).
         * A mol-% HV-incorporation slider (2-20 %, default 10 %).
         * A co-substrate mass ratio slider (kg co-substrate per kg HV
           incorporated) with literature defaults per co-substrate.
         * A PHBV selling-price model that auto-scales with HV content
           (anchored to $5.50/kg at 5% HV, $7/kg at 10%, $9/kg at 15%,
           $12/kg at 20%), with a manual-override checkbox that unlocks
           a flat price slider for stress-testing.
         * The entire PHA revenue stream is sold as PHBV at the scaled
           price; the 70/30 PHB/PHBV blend is not used in PHBV mode.
         * Co-substrate cost appears as a new line in the variable-cost
           stack.

  v10 — Reintroduces human-grade SCP (HGP) as a modeled product, layered
        on top of the v9 SCP+PHA biorefinery. Superset of v9: when the
        HGP toggle is OFF, v10 behaves identically to v9 (including all
        DSP and PHBV options). When the HGP toggle is ON, the SCP revenue
        stream is re-priced and re-costed as human-grade protein:

          * HGP selling price: flat slider, default $8.00/kg, range
            $3.00-$12.00/kg. Anchored to (a) 2024-2025 trade-survey
            pricing for ingredient-grade mycoprotein (Quorn), $6-10/kg,
            with Finnigan 2019 Curr. Dev. Nutr. as the nutritional-
            profile reference for that category; (b) Solar Foods Solein
            public production-cost targets (single-digit USD/kg dry
            protein at Factory 01 nameplate scale); and (c) Ritala
            2017 (Front. Microbiol.) review of bacterial SCP for human
            consumption. Calysta FeedKind is NOT used as an HGP-price
            anchor (FeedKind is feed-grade only; no FeedKind-HP price
            has been publicly disclosed).
          * HGP production mode sub-selector:
              - "Co-production with polymer" (default): the non-PHA
                fraction of CDW is sold as HGP. PHB and PHBV behavior
                are unchanged from v9.
              - "HGP alone (minimize PHA)": the fermenter is operated
                N-replete AND the strain is assumed to carry a phaCAB
                knockout (delta-phaC in C. necator; polymer-negative
                phenotype established by Slater 1988 and Peoples &
                Sinskey 1989, with phaCAB operon mapped by Pohlmann
                2006) so that PHA accumulation is abolished entirely.
                PHB content is overridden to 0 % by default
                (slider range 0-15 %, where the upper bound represents
                the wild-type N-replete case if the KO strain is not
                yet available). Essentially the whole CDW is sold as
                HGP; PHA revenue is de minimis in this mode.
          * HGP-specific downstream cost line: $1.80/kg sellable HGP
            (range $0.50-$5.00/kg), covering endotoxin removal by
            ultrafiltration / TFF, food-grade spray drying, sanitary
            packaging, and QA overhead. This is an internal bottom-up
            engineering estimate (see the hgp_dsp_engineering_estimate
            entry in the reference library), informed by Ritala 2017,
            Jacquel 2008, and public Quorn / Solein flowsheet
            disclosures; it is NOT lifted as a scalar from any single
            published TEA.
          * HGP whole-cell recovery: 85 % of the non-PHA CDW fraction
            (range 60-95 %), matching spray-dried whole-cell mash
            processes (Quorn / Solein style). This is slightly higher
            than feed-grade pelletized SCP (78 %) because the mash is
            less processed.
          * Crude-protein content: 63 % default (range 45-75 %),
            consistent with Quorn ingredient-grade mash and bacterial
            SCP literature.
          * Regulatory caveat surfaced in the sidebar: C. necator H16
            has a mixed regulatory footprint (EFSA QPS "production
            purposes only"; PHA polymer holds FDA Food Contact
            Notifications such as Kaneka FCN 1835) but the biomass
            itself is not GRAS and is not EFSA-Novel-Food-authorised
            as a food ingredient in any major market. Solar Foods
            Solein (a Xanthobacter-group organism, NOT C. necator)
            holds Singapore novel-food approval (2022) and US
            self-affirmed GRAS (2024), with EFSA Novel Food review
            in progress; these clearances do not extend to a new
            C. necator HGP. US GRAS / EFSA Novel Food dossiers
            typically run 2-3 years. HGP economics are pro-forma
            pending that clearance.
          * Facility CapEx for the HGP retrofit (endotoxin skid,
            sanitary spray drier, GFSI compliance) is NOT auto-added
            to the CapEx stack. Users who want to stress-test the
            food-grade retrofit should bump the "Added major CapEx"
            slider by a literature-anchored $8-15M at Phase III.

        v9 remains in the repository (tea_dashboard_v9.py) and is the
        recommended fallback for SCP+PHA-only biorefinery runs.

Run locally:
    cd ~/Downloads
    streamlit run tea_dashboard_v10.py

Deploy to Streamlit Community Cloud:
    1. Push this file + all *_80gL.py files to a public GitHub repo.
    2. Go to share.streamlit.io and deploy from that repo.
    3. In the app's Settings > Secrets, add:
           GROQ_API_KEY = "gsk_..."

Requirements (requirements.txt):
    streamlit>=1.32
    numpy
    matplotlib
    groq>=0.9
"""
from __future__ import annotations

import hmac
import importlib
import math
import sys
from dataclasses import dataclass, fields, replace as _dc_replace
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

try:
    from groq import Groq as _Groq
except ImportError:
    _Groq = None  # type: ignore[assignment,misc]

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

scp = importlib.import_module("scp_teconomics_80gL")
pha = importlib.import_module("pha_teconomics_80gL")
bio = importlib.import_module("biorefinery_teconomics_80gL")

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Leatherback Fairfield TEA Dashboard v10",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
/* ═══ SIDEBAR ═══════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}

/* Default text colour for everything in the sidebar */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] * {
    color: #f1f5f9 !important;
}

/* ── Sidebar expanders ─────────────────────────────────────── */
section[data-testid="stSidebar"] details {
    background-color: #1e293b !important;
    border: 1px solid #475569 !important;
    border-radius: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] details > summary {
    background-color: #1e293b !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 0.7rem !important;
}
section[data-testid="stSidebar"] details > summary * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] details > summary p,
section[data-testid="stSidebar"] details > summary span {
    color: #ffffff !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] details > summary:hover {
    background-color: #334155 !important;
    border-radius: 0.5rem !important;
}
section[data-testid="stSidebar"] details > summary svg {
    fill: #94a3b8 !important;
    stroke: #94a3b8 !important;
}

/* ── Labels, captions, help text ───────────────────────────── */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] small {
    color: #cbd5e1 !important;
}

/* ── Number inputs: the box itself ─────────────────────────── */
section[data-testid="stSidebar"] input[type="number"],
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #475569 !important;
}

/* ── Number inputs: +/- stepper buttons ────────────────────── */
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button {
    background-color: #334155 !important;
    color: #ffffff !important;
    border: 1px solid #475569 !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button:hover {
    background-color: #475569 !important;
}

/* ── Slider track / thumb ──────────────────────────────────── */
section[data-testid="stSidebar"] div[data-testid="stSlider"] div[data-baseweb] {
    background-color: transparent !important;
}

/* ── Select boxes (dropdowns) ──────────────────────────────── */
section[data-testid="stSidebar"] div[data-baseweb="select"],
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
}

/* ── Checkboxes ────────────────────────────────────────────── */
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label span {
    color: #f1f5f9 !important;
}

/* ── Sidebar section header pill ───────────────────────────── */
.sb-hdr {
    background: linear-gradient(135deg, #0ea5e9, #3b82f6);
    color: #ffffff !important;
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    margin: 1.1rem 0 0.5rem 0;
    display: inline-block;
    box-shadow: 0 1px 3px rgba(14,165,233,0.3);
}

/* ── Radio buttons ─────────────────────────────────────────── */
section[data-testid="stSidebar"] .stRadio label {
    color: #e2e8f0 !important;
    font-size: 0.9rem !important;
}


/* ═══ MAIN AREA ═════════════════════════════════════════════ */

/* Metric cards */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 0.6rem;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
div[data-testid="stMetric"] label { font-size: 0.78rem; color: #64748b !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.35rem; color: #0f172a !important;
}

/* Section headers */
.section-hdr {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    border-left: 4px solid #0ea5e9;
    padding: 0.3rem 0 0.3rem 0.7rem;
    margin-top: 1.8rem;
    margin-bottom: 0.6rem;
    background: #f0f9ff;
    border-radius: 0 0.4rem 0.4rem 0;
}

/* Figure frame */
.fig-frame {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 0.6rem;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    border-radius: 0.6rem;
    margin-bottom: 0.4rem;
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
}
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] span,
div[data-testid="stChatMessage"] li { color: #0f172a !important; }

div[data-testid="stChatInput"] textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
}
div[data-testid="stChatInput"] textarea::placeholder { color: #94a3b8 !important; }
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)


def _section(title: str) -> None:
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)


def _sb_hdr(title: str) -> None:
    """Visible sidebar section header pill on the dark background."""
    st.sidebar.markdown(f'<div class="sb-hdr">{title}</div>', unsafe_allow_html=True)


def _render_chat_text(text: str, *, trailing_cursor: bool = False) -> str:
    """Escape only $ signs so Streamlit doesn't parse them as LaTeX math.
    Keeps all other markdown (bold, lists, line breaks) working normally."""
    safe = text.replace("$", r"\$")
    if trailing_cursor:
        safe += " ▌"
    return safe


def _app_password() -> str:
    """Read shared app password from secrets (cloud) or env (local)."""
    import os
    try:
        return str(st.secrets["APP_PASSWORD"])
    except Exception:
        return os.environ.get("APP_PASSWORD", "")


def _require_app_password() -> None:
    """Block app rendering until the shared password is entered."""
    expected = _app_password()
    if not expected:
        return
    if st.session_state.get("app_password_ok", False):
        return

    st.title("Leatherback Fairfield TEA Dashboard v10")
    st.caption("Protected access. Enter the shared password to view the dashboard.")

    with st.form("app_password_form", clear_on_submit=False):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted and hmac.compare_digest(entered, expected):
        st.session_state["app_password_ok"] = True
        st.rerun()
    elif submitted:
        st.error("Incorrect password.")

    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def humanize(name: str) -> str:
    text = name.replace("_", " ")
    for src, dst in (
        ("kg ", "kg "), ("cdw", "CDW"), ("dcw", "DCW"), ("co2", "CO2"),
        ("h2", "H2"), ("phb", "PHB"), ("phbv", "PHBV"),
        ("nh4so4", "(NH4)2SO4"), ("npv", "NPV"), ("cip", "CIP"),
        ("kwh", "kWh"), ("m3", "m3"), ("tpy", "t/y"),
    ):
        text = text.replace(src, dst)
    return text.capitalize()


def step_for(value: Any) -> Any:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return 250_000 if abs(value) >= 100_000 else 1
    mag = abs(float(value))
    if mag >= 1_000_000: return 250_000.0
    if mag >= 1_000:     return 100.0
    if mag >= 100:       return 1.0
    if mag >= 10:        return 0.5
    if mag >= 1:         return 0.1
    return 0.01


def changed(value: Any, default: Any) -> bool:
    if isinstance(value, bool):
        return value != default
    return not math.isclose(float(value), float(default), rel_tol=1e-9, abs_tol=1e-12)


def _display_text(value: Any) -> str:
    text = str(value)
    replacements = {
        "H_2/CO_2": "H2/CO2",
        "CO_2": "CO2",
        "H_2": "H2",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _target_price_label(model_key: str) -> str:
    return "Target PHA selling price ($/kg)" if model_key == "bio" else "Target selling price ($/kg)"


def _target_price_help(model_key: str) -> str:
    if model_key == "bio":
        return "Used for Payback and IRR figures as the PHA selling price. SCP revenue stays tied to the SCP market price input."
    return "Used for Payback and IRR figures."


def _swept_price_axis_label(model_key: str) -> str:
    return "PHA selling price ($/kg)" if model_key == "bio" else "Selling price ($/kg)"


def _swept_price_title_label(model_key: str) -> str:
    return "PHA Selling Price" if model_key == "bio" else "Selling Price"


def _selected_price_context(model_key: str, sell_price: float, scp_price: float) -> str:
    if model_key == "bio":
        return f"PHA ${sell_price:.2f}/kg and SCP ${scp_price:.2f}/kg"
    return f"${sell_price:.2f}/kg"


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL METADATA  (ranges, labels, basis)
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_META: Dict[str, Dict[str, Dict[str, Any]]] = {
    "scp": {
        "titer_g_per_L":              {"label": "Biomass titer (g/L CDW)", "basis": "literature", "recommended": (50.0, 120.0), "note": "Optimized high-cell-density C. necator scenario; model default 80 g/L CDW."},
        "protein_fraction_of_dcw":    {"label": "Protein fraction of CDW", "basis": "engineering", "recommended": (0.45, 0.70), "note": "Product-quality assumption."},
        "yield_h2":                   {"label": "H2/CO2 biomass yield (kg DCW/kg H2)", "basis": "literature", "recommended": (2.0, 3.5), "note": "Ishizaki / Matassa autotrophic yields."},
        "yield_fructose":             {"label": "Fructose biomass yield (kg DCW/kg sugar)", "basis": "literature", "recommended": (0.40, 0.60)},
        "yield_dlp":                  {"label": "DLP biomass yield (kg DCW/kg sugar)", "basis": "literature", "recommended": (0.40, 0.65)},
        "yield_molasses":             {"label": "Molasses biomass yield (kg DCW/kg sugar)", "basis": "literature", "recommended": (0.20, 0.40)},
        "electrolysis_kwh_per_kg_h2": {"label": "Electrolysis energy (kWh/kg H2)", "basis": "literature", "recommended": (48.0, 60.0)},
        "nh4so4_price_per_kg":        {"label": "(NH4)2SO4 price ($/kg)", "basis": "market", "recommended": (0.30, 0.50)},
        "labor_small_scale":  {"label": "Labor — Phase I ramp ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor — Phase II/III ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor — full scale ($/yr)", "basis": "scenario"},
        "npv_discount_rate":  {"label": "NPV discount rate", "basis": "scenario"},
        "npv_years":          {"label": "NPV horizon (years)", "basis": "scenario"},
    },
    "pha": {
        "fedbatch_titer_factor":      {"label": "Fed-batch titer multiplier", "basis": "engineering", "recommended": (1.4, 2.5)},
        "titer_h2_con":               {"label": "Conservative H2/CO2 PHB titer (g/L)", "basis": "literature", "recommended": (15.0, 20.0)},
        "titer_fructose_con":         {"label": "Conservative fructose PHB titer (g/L)", "basis": "literature", "recommended": (15.0, 20.0)},
        "titer_dlp_con":              {"label": "Conservative DLP PHB titer (g/L)", "basis": "literature", "recommended": (15.0, 22.0)},
        "titer_molasses_con":         {"label": "Conservative molasses PHB titer (g/L)", "basis": "literature", "recommended": (10.0, 16.0)},
        "titer_h2_opt":               {"label": "Optimized H2/CO2 PHB titer (g/L)", "basis": "literature", "recommended": (25.0, 40.0)},
        "titer_fructose_opt":         {"label": "Optimized fructose PHB titer (g/L)", "basis": "literature", "recommended": (22.0, 35.0)},
        "titer_dlp_opt":              {"label": "Optimized DLP PHB titer (g/L)", "basis": "literature", "recommended": (22.0, 35.0)},
        "titer_molasses_opt":         {"label": "Optimized molasses PHB titer (g/L)", "basis": "literature", "recommended": (18.0, 28.0)},
        "phb_frac_h2_opt":            {"label": "Optimized H2/CO2 PHB fraction", "basis": "literature", "recommended": (0.65, 0.80)},
        "phb_frac_fructose_opt":      {"label": "Optimized fructose PHB fraction", "basis": "literature", "recommended": (0.55, 0.70)},
        "phb_frac_dlp_opt":           {"label": "Optimized DLP PHB fraction", "basis": "literature", "recommended": (0.55, 0.70)},
        "phb_frac_molasses_opt":      {"label": "Optimized molasses PHB fraction", "basis": "literature", "recommended": (0.45, 0.65)},
        "yield_h2_opt":               {"label": "Optimized H2/CO2 PHB yield (kg/kg H2)", "basis": "literature", "recommended": (1.8, 2.5)},
        "yield_fructose_opt":         {"label": "Optimized fructose PHB yield (g/g)", "basis": "literature", "recommended": (0.25, 0.40)},
        "yield_dlp_opt":              {"label": "Optimized DLP PHB yield (g/g)", "basis": "literature", "recommended": (0.28, 0.40)},
        "yield_molasses_opt":         {"label": "Optimized molasses PHB yield (g/g)", "basis": "literature", "recommended": (0.15, 0.28)},
        "electrolysis_kwh_per_kg_h2": {"label": "Electrolysis energy (kWh/kg H2)", "basis": "literature", "recommended": (48.0, 60.0)},
        "nh4so4_price_per_kg":        {"label": "(NH4)2SO4 price ($/kg)", "basis": "market", "recommended": (0.30, 0.50)},
        "labor_small_scale":  {"label": "Labor — Phase I ramp ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor — Phase II/III ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor — full scale ($/yr)", "basis": "scenario"},
        "npv_discount_rate":  {"label": "NPV discount rate", "basis": "scenario"},
        "npv_years":          {"label": "NPV horizon (years)", "basis": "scenario"},
    },
    "bio": {
        "scp_recovery":               {"label": "SCP recovery fraction", "basis": "engineering", "recommended": (0.75, 0.95)},
        "scp_protein_fraction":       {"label": "SCP protein fraction", "basis": "engineering", "recommended": (0.45, 0.70)},
        "phb_market_price":           {"label": "PHB market price ($/kg)", "basis": "market", "recommended": (1.5, 8.5)},
        "scp_market_price":           {"label": "SCP market price ($/kg)", "basis": "market", "recommended": (1.0, 4.0)},
        "fedbatch_titer_factor":      {"label": "Fed-batch titer multiplier", "basis": "engineering", "recommended": (1.4, 2.5)},
        "titer_h2_opt":               {"label": "Opt. H2/CO2 PHB titer (g/L)", "basis": "literature", "recommended": (25.0, 40.0)},
        "titer_fructose_opt":         {"label": "Opt. fructose PHB titer (g/L)", "basis": "literature", "recommended": (22.0, 35.0)},
        "titer_dlp_opt":              {"label": "Opt. DLP PHB titer (g/L)", "basis": "literature", "recommended": (22.0, 35.0)},
        "titer_molasses_opt":         {"label": "Opt. molasses PHB titer (g/L)", "basis": "literature", "recommended": (18.0, 28.0)},
        "phb_frac_h2_opt":            {"label": "Opt. H2/CO2 PHB fraction", "basis": "literature", "recommended": (0.65, 0.80)},
        "phb_frac_fructose_opt":      {"label": "Opt. fructose PHB fraction", "basis": "literature", "recommended": (0.55, 0.70)},
        "phb_frac_dlp_opt":           {"label": "Opt. DLP PHB fraction", "basis": "literature", "recommended": (0.55, 0.70)},
        "phb_frac_molasses_opt":      {"label": "Opt. molasses PHB fraction", "basis": "literature", "recommended": (0.45, 0.65)},
        "yield_h2_opt":               {"label": "Opt. H2/CO2 PHB yield (kg/kg H2)", "basis": "literature", "recommended": (1.8, 2.5)},
        "yield_fructose_opt":         {"label": "Opt. fructose PHB yield (g/g)", "basis": "literature", "recommended": (0.25, 0.40)},
        "yield_dlp_opt":              {"label": "Opt. DLP PHB yield (g/g)", "basis": "literature", "recommended": (0.28, 0.40)},
        "yield_molasses_opt":         {"label": "Opt. molasses PHB yield (g/g)", "basis": "literature", "recommended": (0.15, 0.28)},
        "electrolysis_kwh_per_kg_h2": {"label": "Electrolysis energy (kWh/kg H2)", "basis": "literature", "recommended": (48.0, 60.0)},
        "nh4so4_price_per_kg":        {"label": "(NH4)2SO4 price ($/kg)", "basis": "market", "recommended": (0.30, 0.50)},
        "labor_small_scale":  {"label": "Labor — Phase I ramp ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor — Phase II/III ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor — full scale ($/yr)", "basis": "scenario"},
        "npv_discount_rate":  {"label": "NPV discount rate", "basis": "scenario"},
        "npv_years":          {"label": "NPV horizon (years)", "basis": "scenario"},
    },
}

FINANCE_DEFAULTS: Dict[str, Dict[str, float]] = {
    "scp": {
        "reference_capacity_tpy": 1_200.0,
        "base_installed_capex_ref": 45_000_000.0,
        "capex_scaling_exponent": 0.0,
        "added_capex_ref": 0.0,
    },
    "pha": {
        "reference_capacity_tpy": 1_200.0,
        "base_installed_capex_ref": 45_000_000.0,
        "capex_scaling_exponent": 0.0,
        "added_capex_ref": 0.0,
    },
    "bio": {
        "reference_capacity_tpy": 1_200.0,
        "base_installed_capex_ref": 45_000_000.0,
        "capex_scaling_exponent": 0.0,
        "added_capex_ref": 0.0,
    },
}

# Site-specific capacity tiers derived from 400,000 L fermentation volume.
# Fed-batch, DLP optimized: 81 g/L CDW, 114 h cycle, 0.80 working volume.
# Phase I (20 % util) ≈ 400 t/y CDW; Phase II (60 %) ≈ 1,200; Phase III (90 %) ≈ 1,800.
FAIRFIELD_CAPACITIES: Dict[str, List[float]] = {
    "scp": [400.0, 1_200.0, 1_800.0],
    "pha": [400.0, 1_200.0, 1_800.0],
    "bio": [400.0, 1_200.0, 1_800.0],
}

PHASE_LABELS: Dict[float, str] = {
    400.0:   "Phase I  (20 %)",
    1_200.0: "Phase II (60 %)",
    1_800.0: "Phase III (90 %)",
}

# Fairfield-specific assumption overrides applied to model defaults
SITE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "bio": dict(
        electricity_price=0.12,
        dlp_price_per_kg_sugar=0.11,
        npv_discount_rate=0.09,
        labor_small_scale=750_000.0,
        labor_medium_scale=2_500_000.0,
        labor_large_scale=3_500_000.0,
    ),
    "scp": dict(
        electricity_price=0.12,
        dlp_price_per_kg_sugar=0.11,
        npv_discount_rate=0.09,
        labor_small_scale=750_000.0,
        labor_medium_scale=2_500_000.0,
        labor_large_scale=3_500_000.0,
    ),
    "pha": dict(
        electricity_price=0.12,
        dlp_price_per_kg_sugar=0.11,
        npv_discount_rate=0.09,
        labor_small_scale=750_000.0,
        labor_medium_scale=2_500_000.0,
        labor_large_scale=3_500_000.0,
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION MAP  (parameter -> sidebar expander group)
# ═══════════════════════════════════════════════════════════════════════════════

SECTION_MAP: Dict[str, Dict[str, str]] = {
    "scp": {
        "recovery_fraction": "Product", "product_moisture_fraction": "Product",
        "titer_g_per_L": "Fermentation", "protein_fraction_of_dcw": "Product",
        "batch_time_h": "Fermentation", "turnaround_h": "Fermentation",
        "working_volume_fraction": "Fermentation", "residence_time_h": "Fermentation",
        "yield_h2": "Yields", "yield_fructose": "Yields",
        "yield_dlp": "Yields", "yield_molasses": "Yields",
        "co2_kg_per_kg_dcw": "Utilities", "co2_price_per_kg": "Feedstocks & Utilities",
        "electricity_price": "Feedstocks & Utilities",
        "electrolysis_kwh_per_kg_h2": "Utilities",
        "fructose_price_per_kg": "Feedstocks & Utilities",
        "dlp_price_per_kg_sugar": "Feedstocks & Utilities",
        "molasses_price_per_kg_sugar": "Feedstocks & Utilities",
        "pretreatment_fructose": "Downstream & Pretreatment",
        "pretreatment_dlp": "Downstream & Pretreatment",
        "pretreatment_molasses": "Downstream & Pretreatment",
        "n_fraction_of_dcw": "Nitrogen", "nh4so4_n_fraction": "Nitrogen",
        "nh4so4_price_per_kg": "Nitrogen",
        "n_supplement_reduction_fructose": "Nitrogen",
        "n_supplement_reduction_dlp": "Nitrogen",
        "n_supplement_reduction_molasses": "Nitrogen",
        "aeration_kwh_m3_h_gas": "Utilities", "aeration_kwh_m3_h_fructose": "Utilities",
        "aeration_kwh_m3_h_dlp": "Utilities", "aeration_kwh_m3_h_molasses": "Utilities",
        "cake_moisture_fraction": "Downstream & Pretreatment",
        "capex_threshold": "Finance & CapEx",
        "labor_small_scale": "Finance & CapEx", "labor_medium_scale": "Finance & CapEx",
        "labor_large_scale": "Finance & CapEx",
        "npv_discount_rate": "Finance & CapEx", "npv_years": "Finance & CapEx",
        "hours_per_year": "Schedule",
    },
    "pha": {
        "extraction_recovery": "Product & Extraction", "product_moisture_fraction": "Product & Extraction",
        "batch_growth_h": "Fermentation", "batch_accumulation_h": "Fermentation",
        "batch_cip_h": "Fermentation", "working_volume_fraction": "Fermentation",
        "fedbatch_growth_h": "Fermentation", "fedbatch_accumulation_h": "Fermentation",
        "fedbatch_cip_h": "Fermentation", "fedbatch_titer_factor": "Fermentation",
        "titer_h2_con": "Conservative PHA Basis", "titer_fructose_con": "Conservative PHA Basis",
        "titer_dlp_con": "Conservative PHA Basis", "titer_molasses_con": "Conservative PHA Basis",
        "titer_h2_opt": "Optimized PHA Basis", "titer_fructose_opt": "Optimized PHA Basis",
        "titer_dlp_opt": "Optimized PHA Basis", "titer_molasses_opt": "Optimized PHA Basis",
        "phb_frac_h2_con": "Conservative PHA Basis", "phb_frac_fructose_con": "Conservative PHA Basis",
        "phb_frac_dlp_con": "Conservative PHA Basis", "phb_frac_molasses_con": "Conservative PHA Basis",
        "phb_frac_h2_opt": "Optimized PHA Basis", "phb_frac_fructose_opt": "Optimized PHA Basis",
        "phb_frac_dlp_opt": "Optimized PHA Basis", "phb_frac_molasses_opt": "Optimized PHA Basis",
        "yield_h2_con": "Conservative PHA Basis", "yield_fructose_con": "Conservative PHA Basis",
        "yield_dlp_con": "Conservative PHA Basis", "yield_molasses_con": "Conservative PHA Basis",
        "yield_h2_opt": "Optimized PHA Basis", "yield_fructose_opt": "Optimized PHA Basis",
        "yield_dlp_opt": "Optimized PHA Basis", "yield_molasses_opt": "Optimized PHA Basis",
        "phbv_yield_factor": "Product & Extraction", "propionate_kg_per_kg_phbv": "Product & Extraction",
        "propionate_price_per_kg": "Feedstocks & Utilities",
        "co2_kg_per_kg_cdw": "Utilities", "co2_price_per_kg": "Feedstocks & Utilities",
        "electricity_price": "Feedstocks & Utilities", "electrolysis_kwh_per_kg_h2": "Utilities",
        "fructose_price_per_kg": "Feedstocks & Utilities",
        "dlp_price_per_kg_sugar": "Feedstocks & Utilities",
        "molasses_price_per_kg_sugar": "Feedstocks & Utilities",
        "pretreatment_fructose": "Feedstocks & Utilities",
        "pretreatment_dlp": "Feedstocks & Utilities",
        "pretreatment_molasses": "Feedstocks & Utilities",
        "n_fraction_of_cdw": "Nitrogen", "nh4so4_n_fraction": "Nitrogen",
        "nh4so4_price_per_kg": "Nitrogen",
        "n_reduction_fructose": "Nitrogen", "n_reduction_dlp": "Nitrogen",
        "n_reduction_molasses": "Nitrogen",
        "aeration_kwh_m3_h_gas": "Utilities", "aeration_kwh_m3_h_fructose": "Utilities",
        "aeration_kwh_m3_h_dlp": "Utilities", "aeration_kwh_m3_h_molasses": "Utilities",
        "centrifuge_kwh_per_m3": "Utilities",
        "fiber_grade_required": "Product & Extraction",
        "drying_kwh_per_kg_water": "Product & Extraction", "wet_pha_moisture": "Product & Extraction",
        "capex_threshold": "Finance & CapEx",
        "labor_small_scale": "Finance & CapEx", "labor_medium_scale": "Finance & CapEx",
        "labor_large_scale": "Finance & CapEx",
        "npv_discount_rate": "Finance & CapEx", "npv_years": "Finance & CapEx",
        "hours_per_year": "Schedule",
    },
    "bio": {
        "extraction_recovery": "Product & Extraction", "pha_product_moisture": "Product & Extraction",
        "scp_recovery": "SCP Product", "scp_wash_cost_per_kg": "SCP Product",
        "scp_cake_moisture": "SCP Product", "scp_product_moisture": "SCP Product",
        "scp_drying_kwh_per_kg_water": "SCP Product", "scp_protein_fraction": "SCP Product",
        "phb_market_price": "Market Prices", "scp_market_price": "Market Prices",
        "batch_growth_h": "Fermentation", "batch_accumulation_h": "Fermentation",
        "batch_cip_h": "Fermentation", "working_volume_fraction": "Fermentation",
        "fedbatch_growth_h": "Fermentation", "fedbatch_accumulation_h": "Fermentation",
        "fedbatch_cip_h": "Fermentation", "fedbatch_titer_factor": "Fermentation",
        "titer_h2_con": "Conservative PHA Basis", "titer_fructose_con": "Conservative PHA Basis",
        "titer_dlp_con": "Conservative PHA Basis", "titer_molasses_con": "Conservative PHA Basis",
        "titer_h2_opt": "Optimized PHA Basis", "titer_fructose_opt": "Optimized PHA Basis",
        "titer_dlp_opt": "Optimized PHA Basis", "titer_molasses_opt": "Optimized PHA Basis",
        "phb_frac_h2_con": "Conservative PHA Basis", "phb_frac_fructose_con": "Conservative PHA Basis",
        "phb_frac_dlp_con": "Conservative PHA Basis", "phb_frac_molasses_con": "Conservative PHA Basis",
        "phb_frac_h2_opt": "Optimized PHA Basis", "phb_frac_fructose_opt": "Optimized PHA Basis",
        "phb_frac_dlp_opt": "Optimized PHA Basis", "phb_frac_molasses_opt": "Optimized PHA Basis",
        "yield_h2_con": "Conservative PHA Basis", "yield_fructose_con": "Conservative PHA Basis",
        "yield_dlp_con": "Conservative PHA Basis", "yield_molasses_con": "Conservative PHA Basis",
        "yield_h2_opt": "Optimized PHA Basis", "yield_fructose_opt": "Optimized PHA Basis",
        "yield_dlp_opt": "Optimized PHA Basis", "yield_molasses_opt": "Optimized PHA Basis",
        "phbv_yield_factor": "Product & Extraction", "propionate_kg_per_kg_phbv": "Product & Extraction",
        "propionate_price_per_kg": "Feedstocks & Utilities",
        "co2_kg_per_kg_cdw": "Utilities", "co2_price_per_kg": "Feedstocks & Utilities",
        "electricity_price": "Feedstocks & Utilities", "electrolysis_kwh_per_kg_h2": "Utilities",
        "fructose_price_per_kg": "Feedstocks & Utilities",
        "dlp_price_per_kg_sugar": "Feedstocks & Utilities",
        "molasses_price_per_kg_sugar": "Feedstocks & Utilities",
        "pretreatment_fructose": "Feedstocks & Utilities",
        "pretreatment_dlp": "Feedstocks & Utilities",
        "pretreatment_molasses": "Feedstocks & Utilities",
        "n_fraction_of_cdw": "Nitrogen", "nh4so4_n_fraction": "Nitrogen",
        "nh4so4_price_per_kg": "Nitrogen",
        "n_reduction_fructose": "Nitrogen", "n_reduction_dlp": "Nitrogen",
        "n_reduction_molasses": "Nitrogen",
        "aeration_kwh_m3_h_gas": "Utilities", "aeration_kwh_m3_h_fructose": "Utilities",
        "aeration_kwh_m3_h_dlp": "Utilities", "aeration_kwh_m3_h_molasses": "Utilities",
        "centrifuge_kwh_per_m3": "Utilities",
        "fiber_grade_required": "Product & Extraction",
        "pha_drying_kwh_per_kg_water": "Product & Extraction", "wet_pha_moisture": "Product & Extraction",
        "capex_threshold": "Finance & CapEx",
        "labor_small_scale": "Finance & CapEx", "labor_medium_scale": "Finance & CapEx",
        "labor_large_scale": "Finance & CapEx",
        "npv_discount_rate": "Finance & CapEx", "npv_years": "Finance & CapEx",
        "hours_per_year": "Schedule",
    },
}

SECTION_ORDER = [
    "Product", "Fermentation", "Yields",
    "Conservative PHA Basis", "Optimized PHA Basis",
    "SCP Product", "Product & Extraction", "Market Prices",
    "Feedstocks & Utilities", "Utilities", "Nitrogen",
    "Downstream & Pretreatment", "Finance & CapEx", "Schedule", "Other Inputs",
]

# ═══════════════════════════════════════════════════════════════════════════════
#  REFERENCE LIBRARY — verified DOI / publisher URLs where possible
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCE_LIBRARY: Dict[str, Dict[str, str]] = {
    "framework_2026": {
        "title": "PhycoVax Inc. TEA Question Framework (March 2026)",
        "kind": "Internal framework",
        "why": "Primary internal source for scenario structure, capacities, and baseline economics.",
        "used": "Used for scenario structure and the imported TEA model architecture. v4 replaces generic capacity tiers with Fairfield site-specific phases (400, 1,200, 1,800 t/y CDW).",
        "url": "",
        "url_note": "Internal / confidential document.",
    },
    "fairfield_handoff_v7": {
        "title": "Leatherback Systems, Inc. -- Fairfield Biofoundry Site-Specific Technoeconomic Analysis (Fairfield_TEA_v7_Final, April 5, 2026)",
        "kind": "Internal / confidential site handoff",
        "why": "Primary locked handoff document for the Fairfield Biofoundry. Prepared jointly by Leatherback Systems (Thomas Grimm, Founder/CEO; MJ Zeng, Co-Founder) and Dr. Justin Panich (Exponential Phase LLC). Defines the full Scenario 1 (Jelly Belly COD + invertase) and Scenario 2 (Jelly Belly COD + delactosed permeate, DLP) parameter set, including feedstock costs, pretreatment costs, utilities, nitrogen, labor ramp, and the confirmed AB InBev brewery PPA electricity rate. The document is the single authoritative source for all cost inputs marked CONFIRMED in Table 19 (Section 5.3 -- Parameters for Dr. Justin Panich -- Final Formal Inputs) and for the per-run OPEX cost build in Table 11 (Section 3 -- Per-Run OPEX, All Three Phases, Scenario 1).",
        "used": "All cost-side inputs in the v10 engine were back-calculated from the Scenario 1 per-run OPEX table in the handoff so that the engine reproduces the handoff cost structure at Phase III (14,000 kg CDW/day basis). Specifically: Jelly Belly COD at $0.11/kg fermentable sugar; Scenario 1 pretreatment at $0.038/kg sugar (invertase $0.015 + pH adjust $0.004 + filtration $0.007 + HTST $0.012); DLP at $0.12-0.13/kg sugar with DLP pretreatment at pH + dilution only (taken as $0.004/kg sugar); electricity at $0.12/kWh, sourced from the AB InBev Fairfield PPA and confirmed by Thomas Grimm (vs the California industrial average of approximately $0.19/kWh); electricity intensity implied at ~1.77 kWh/kg CDW; steam $0.160/kg CDW; bulk downstream $0.420/kg CDW; CIP $0.177/kg CDW; PHA extraction $0.638/kg sellable PHA; nitrogen at a standard cost of $0.068/kg CDW with a 50% reduction in Scenario 1 and ~75% blended reduction in Scenario 2 driven by gelatin-amino-acid nitrogen in the Jelly Belly COD and the near-zero native nitrogen content of DLP; fixed labor at $0.45M, $1.10M, and $2.00M for Phases I / II / III respectively (25% / 60% / 100% FTE ramp); and a discount rate of 9%. Continuous operation with 24-hour HRT is the handoff-confirmed base case; fed-batch is explicitly excluded. Upside / downside are limited to plus or minus 20% CDW titer only, per the handoff instruction.",
        "url": "",
        "url_note": "Confidential internal document (Fairfield_TEA_v7_Final). All cost inputs in the v10 engine trace to this source; where the handoff referenced a peer-reviewed paper (e.g. Orita 2012 for glucose utilisation by NCIMB 11599, Wang et al. 2022 for DLP pricing), that paper is also cited in the reference library as a supporting external anchor.",
    },
    "phycovax_costs_davis": {
        "title": "PhycoVax Inc. -- Leatherback BioHub Techno-Economic Analysis: Sugar Feedstocks vs. Dairy Waste Streams (Helen Wahlgren, Director of Business Development, PhycoVax Inc., March 27, 2026)",
        "kind": "Internal / confidential DLP feedstock memo",
        "why": "Companion memo prepared for the Berkeley Labs collaboration review (CEO Thomas Grimm, Chief Scientist Dr. Roshan Shrestha). Independent internal verification of the DLP-from-Hilmar feedstock price at $0.13/kg lactose equivalent (Table 9, cross-referenced against Wang et al. 2022 Processes 10:17), and of the broader Central Valley dairy-waste feedstock pricing landscape (whey permeate $0.37/kg, whey sugar / lactose powder $0.77/kg, HFCS $0.38-0.45/kg, corn dextrose $0.585/kg, US sugar beet $0.50-0.56/kg).",
        "used": "Used to cross-check the DLP sugar price band in the Fairfield handoff. The PhycoVax memo's $0.13/kg anchor sits inside the Fairfield handoff $0.12-0.13/kg band; the v10 engine uses the midpoint $0.125/kg, which is consistent with both internal sources.",
        "url": "",
        "url_note": "Confidential internal document (PhycoVax_costs_davis). Feedstock cost inputs are cross-referenced with this memo; dark-fermentation and IRA 45V content is outside the Fairfield SCP/PHA scope and is not used by the v10 engine.",
    },
    "wang_2022": {
        "title": "Wang K, Hobby AM, Chen Y, Chio A, Jenkins BM, Zhang R. 2022, Processes 10(1):17 -- Techno-economic analysis on an industrial-scale production system of polyhydroxyalkanoates (PHA) from cheese by-products by halophiles",
        "kind": "Literature / TEA",
        "why": "Peer-reviewed industrial-scale TEA from UC Davis (Wang et al.) co-authored with Hilmar Cheese Company engineering staff. Analyzes PHA (PHBV) production from cheese by-product streams using Haloferax mediterranei at 168.7 MT/day lactose feed, producing 9,700 MT/year PHBV with 0.2 g PHBV/g lactose yield and 87% overall process efficiency. Reports DLP unit price as the dominant breakeven-price driver (breakeven <$4/kg PHA at favorable DLP terms with enzyme reuse and spent-medium recycling).",
        "used": "Used qualitatively as the external literature anchor for the order-of-magnitude DLP sugar-cost (~$0.125/kg sugar) and DLP pretreatment-cost (~$0.004/kg sugar) bands in the v10 engine. The DLP supplier in the Wang 2022 paper (Hilmar Cheese Company, Hilmar CA) is the same supplier named in the Leatherback Fairfield site handoff Scenario 2 definition, which is why this paper was selected as the external reference. No single hard-coded scalar is copied directly; the engine's DLP defaults sit inside the pricing envelope established by the paper.",
        "url": "https://doi.org/10.3390/pr10010017",
        "url_note": "Direct MDPI DOI. The earlier entry pointed to a Google Scholar search because the specific paper had not been located; this is now the published article.",
    },
    "pubmed_40669633": {
        "title": "PubMed 40669633 (2025) -- whey permeate / DSM545",
        "kind": "Literature",
        "why": "Whey permeate / DSM545 performance and DLP yield framing.",
        "used": "Used to justify the DLP titer/yield framing and recommended bands in the guarded dashboard, rather than one exact fixed scalar.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/40669633/",
        "url_note": "",
    },
    "dalsasso_2019": {
        "title": "Dalsasso RR, Pavan FA, Bordignon SE, de Aragão GMF, Poletto P. 2019, Process Biochemistry 85:12-18 -- Polyhydroxybutyrate (PHB) production by Cupriavidus necator from sugarcane vinasse and molasses as mixed substrate",
        "kind": "Literature",
        "why": "Peer-reviewed experimental study reporting PHB production by C. necator DSM 545 on sugarcane molasses + vinasse as a mixed substrate. Reports 11.7 g/L PHB, 56% PHB content of CDW, mu_max 0.36/h, and PHB productivity 0.42 g/L/h, which are the direct empirical basis for the conservative molasses titer framing.",
        "used": "Used specifically for the conservative molasses PHB titer framing around 11.7 g/L PHB and 56% PHB content, and more generally for molasses-based PHA plausibility.",
        "url": "https://doi.org/10.1016/j.procbio.2019.07.007",
        "url_note": "DOI corrected from an earlier entry that pointed to a Frontiers review citing Dalsasso rather than to the original Process Biochemistry paper.",
    },
    "ishizaki_2001": {
        "title": "Ishizaki et al. (closest verified: Tanaka & Ishizaki 1995)",
        "kind": "Literature",
        "why": "Autotrophic H2/CO2 yield basis for 3.0 kg DCW / kg H2.",
        "used": "Used for the H2/CO2 biomass-yield anchor of about 3.0 kg DCW per kg H2 in SCP/PHA/autotrophic framing.",
        "url": "https://doi.org/10.1002/bit.260450312",
        "url_note": "This is Tanaka & Ishizaki 1995 in Biotech. Bioeng. Confirm the exact 2001 paper with your team.",
    },
    "matassa_2016": {
        "title": "Matassa, Boon, Pikaar & Verstraete 2016, Microb. Biotechnol. 9(5):568-575 — Microbial protein: future sustainable food supply route with low environmental footprint",
        "kind": "Literature (open access)",
        "why": "Review of H2-oxidizing-bacterium (HOB) microbial protein as a sustainable food route. Covers autotrophic biomass yield on H2, protein content, and the environmental-footprint case for bacterial SCP.",
        "used": "Used alongside Tanaka & Ishizaki 1995 as a support reference for the autotrophic H2/CO2 biomass-yield framing near 3 kg DCW per kg H2. Independently verified via DOI 10.1111/1751-7915.12369 (title confirmed).",
        "url": "https://doi.org/10.1111/1751-7915.12369",
        "url_note": "",
    },
    "imarc_molasses_2025": {
        "title": "IMARC Group molasses pricing (US, Q2-Q3 2025)",
        "kind": "Market",
        "why": "Molasses sugar-price default ($0.155/kg sugar).",
        "used": "Used for the molasses sugar price default of about $0.155 per kg sugar.",
        "url": "https://www.imarcgroup.com/molasses-pricing-report",
        "url_note": "",
    },
    "imarc_ammonium_2025": {
        "title": "IMARC Group ammonium sulfate pricing (2025)",
        "kind": "Market",
        "why": "Supports (NH4)2SO4 cost band ($0.42/kg default).",
        "used": "Used for the ammonium sulfate default near $0.42/kg and the guarded recommended band around $0.30-0.50/kg.",
        "url": "https://www.imarcgroup.com/ammonium-sulfate-pricing-report",
        "url_note": "",
    },
    "kim_1994": {
        "title": "Kim, Lee, Lee, Chang, Chang & Woo 1994, Biotechnol. Bioeng. 43(9):892-898",
        "kind": "Literature",
        "why": "Glucose-based fed-batch of Alcaligenes eutrophus (now Cupriavidus necator) with on-line glucose concentration control. Reported 121 g/L CDW and 76% PHB content (~92 g/L PHB). One of the two canonical high-cell-density fed-batch anchors cited against bacterial PHA.",
        "used": "v8 direct anchor for the fed-batch-mode PHB content default (68%) and the lower bound of the 60-250 g/L fed-batch CDW slider range. The fed-batch base case is set below the reported 121 g/L / 76% PHB endpoint to reflect an operationally achievable mid-range rather than a laboratory stretch case.",
        "url": "https://doi.org/10.1002/bit.260430908",
        "url_note": "",
    },
    "ryu_1997": {
        "title": "Ryu, Hahn, Chang, Chang & Lee 1997, Biotechnol. Bioeng. 55(1):28-32",
        "kind": "Literature",
        "why": "Phosphate-limited fed-batch of Alcaligenes eutrophus at high aeration. Reported 281 g/L CDW and 232 g/L PHB (~67% PHB content). Upper literature bound for C. necator fed-batch CDW; the textbook reference for a stretched, high-OTR fed-batch case.",
        "used": "v8 direct anchor for the upper end of the 60-250 g/L fed-batch CDW slider range and the fed-batch-mode PHB content default (68%). The fed-batch base case intentionally sits below the Ryu endpoint to leave a clear upside band available via the slider.",
        "url": "https://doi.org/10.1002/(SICI)1097-0290(19970705)55:1%3C28::AID-BIT4%3E3.0.CO;2-Z",
        "url_note": "",
    },
    "budde_2011": {
        "title": "Budde, Riedel, Willis, Rha & Sinskey 2011, Appl. Environ. Microbiol. 77(9):2847-2854",
        "kind": "Literature",
        "why": "Fed-batch of engineered Ralstonia eutropha (C. necator) producing P(HB-co-HHx) from plant oil at laboratory and pilot scale. Demonstrates that high-cell-density fed-batch for PHA production translates from bench to commercial-scale bioreactors, typically in the 100-160 g/L CDW / 60-70% PHB band at pilot scale.",
        "used": "v8 scale-up anchor for the fed-batch base case (150 g/L CDW, 68% PHB, 76 h cycle, 68% duty cycle). Used to defend that the chosen fed-batch base is within the demonstrated envelope for CMO-scale PHA fermentation, not a laboratory-only result.",
        "url": "https://doi.org/10.1128/AEM.02429-10",
        "url_note": "",
    },
    "kapritchkoff_2006": {
        "title": "Kapritchkoff, Viotti, Alli, Zuccolo, Pradella, Maiorano, Miranda & Bonomi 2006, J. Biotechnol. 122(4):453-462 — Enzymatic recovery and purification of polyhydroxybutyrate produced by Ralstonia eutropha",
        "kind": "Literature",
        "why": "Direct experimental study of enzymatic (pancreatin, bromelain, trypsin) recovery of PHB from R. eutropha. Reports reagent loadings, recovery yields (typically 85-90%), and molecular-weight retention that are the real empirical basis for enzymatic-DSP cost envelopes. This is the closest-fit literature anchor for the v9 Mechanical + enzymatic pathway; the earlier draft cited Kessler & Witholt 2001 in error (that paper reviews PHA regulatory metabolism, not downstream processing).",
        "used": "v9 anchor for the Mechanical + enzymatic DSP pathway defaults ($0.25/kg PHA extraction, $0.30/kg CDW downstream). Verified via DOI 10.1016/j.jbiotec.2005.09.009 (title and content confirmed).",
        "url": "https://doi.org/10.1016/j.jbiotec.2005.09.009",
        "url_note": "Replaces an earlier incorrect citation to Kessler & Witholt 2001, which covers PHA regulatory metabolism rather than downstream recovery.",
    },
    "hahn_1994": {
        "title": "Hahn SK, Chang YK, Kim BS, Chang HN. 1994, Biotechnol. Bioeng. 44(2):256-261 — Communication to the editor: Optimization of microbial poly(3-hydroxybutyrate) recovery using dispersions of sodium hypochlorite solution and chloroform",
        "kind": "Literature",
        "why": "Benchmarks alkaline digestion (NaOH-based) versus hypochlorite and solvent recovery for PHB. Reports reagent consumption, Mw retention, and extraction yield trade-offs that anchor the NaOH hot-alkali pathway defaults.",
        "used": "v9 anchor for the NaOH hot-alkali DSP pathway defaults ($0.45/kg PHA extraction, $0.38/kg CDW downstream, $1.5M Phase III CapEx adder for alkali-resistant wetted parts).",
        "url": "https://doi.org/10.1002/bit.260440215",
        "url_note": "",
    },
    "jacquel_2008": {
        "title": "Jacquel, Lo, Wei, Wu & Wang 2008, Biochem. Eng. J. 39(1):15-27 — Isolation and purification of bacterial poly(3-hydroxyalkanoates)",
        "kind": "Literature (review)",
        "why": "Peer-reviewed review of PHA recovery methods: chlorinated solvents, hypochlorite, alkaline digestion, SDS/surfactant, and enzymatic routes. Provides side-by-side comparisons of reagent load, Mw retention, purity, and yield that are the standard cited basis for non-chlorinated DSP cost estimates.",
        "used": "v9 secondary anchor (alongside Kapritchkoff 2006) for the Mechanical + enzymatic DSP pathway; supports the $0.25/kg PHA extraction and $0.30/kg CDW downstream defaults. Verified via DOI 10.1016/j.bej.2007.11.029.",
        "url": "https://doi.org/10.1016/j.bej.2007.11.029",
        "url_note": "Replaces an earlier citation to Yu & Chen 2007 (Process Biochemistry), which could not be independently verified at the stated DOI/pages.",
    },
    "doi_1988": {
        "title": "Doi, Tamaki, Kunioka & Soga 1988, Appl. Microbiol. Biotechnol. 28(4-5):330-334 — Production of copolyesters of 3-hydroxybutyrate and 3-hydroxyvalerate by Alcaligenes eutrophus from butyric and pentanoic acids",
        "kind": "Literature",
        "why": "Original production study for PHBV in Alcaligenes eutrophus (now Cupriavidus necator), establishing the co-feed requirement (propionate, valerate) for 3-HV incorporation and the approximate mass ratios of co-substrate fed per unit HV incorporated.",
        "used": "v9 anchor for the propionate / valerate co-substrate mass-ratio defaults (2.5 and 1.5 kg co-substrate per kg HV respectively). Establishes the biology constraint that NCIMB 11599 cannot produce PHBV from glucose alone.",
        "url": "https://doi.org/10.1007/BF00268190",
        "url_note": "",
    },
    "madison_huisman_1999": {
        "title": "Madison & Huisman 1999, Microbiol. Mol. Biol. Rev. 63(1):21-53 — Metabolic engineering of poly(3-hydroxyalkanoates): from DNA to plastic",
        "kind": "Literature",
        "why": "Comprehensive review of PHA biology, including propionate / valerate / levulinate co-feeding strategies and the respiration-yield penalty on co-substrate incorporation. Used to anchor upper bounds on HV content achievable with each co-substrate.",
        "used": "v9 anchor for the per-co-substrate HV-content ceilings and default HV targets (propionate default 10 mol%, valerate default 12 mol%, levulinate default 8 mol%).",
        "url": "https://doi.org/10.1128/MMBR.63.1.21-53.1999",
        "url_note": "",
    },
    "tianan_kaneka_2024": {
        "title": "Tianan Biologic Materials (Enmat) / Kaneka Corporation (Aonilex) / Danimer Scientific (Nodax) PHBV / PHBH product-line disclosures (2023-2025), with peer-reviewed anchor Rosenboom, Langer & Traverso 2022 Nat. Rev. Mater. 7:117-137",
        "kind": "Commercial disclosure + peer-reviewed review",
        "why": "Publicly verifiable specialty-bioplastic price ranges for PHBV (Tianan Enmat Y1000P at 1-2% HV) and PHBH (Kaneka Aonilex), plus Danimer Nodax third-party pricing surveys. The Helian Polymers authorized European distributor for Tianan lists Enmat Y1000P pellets at EUR 40/kg (10 kg tier) sliding to EUR 12.50/kg (250 kg tier) for powder, which cross-checks against the $6-8/kg commercial PHBV band used in the model. Rosenboom et al. 2022 is the peer-reviewed secondary anchor: their Nature Reviews Materials bioplastics market overview reports commercial PHA pellet pricing in the 2-8 USD/kg range and documents the PHBV premium over PHB.",
        "used": "v9/v10 anchors for the piecewise-linear PHBV auto-scaling price model: $5.50/kg at 5% HV, $7/kg at 10%, $9/kg at 15%, $12/kg at 20%. The price-vs-HV slope reflects co-substrate cost and industrial-grade scarcity, not a single published price table.",
        "url": "https://shop.helianpolymers.com/collections/tianan-biologic",
        "url_note": "Earlier entry pointed to https://www.tianan-enmat.com/ which throws an SSL certificate warning in modern browsers and is not safe to cite in investor-facing deliverables. Replaced with the authorized European distributor (Helian Polymers) product page, which lists Enmat grades and public per-kg prices. The peer-reviewed Rosenboom 2022 Nat. Rev. Mater. anchor (DOI 10.1038/s41578-021-00407-8) is the preferred citation for the underlying commercial price band.",
    },
    "finnigan_2019": {
        "title": "Finnigan, Wall, Wilde, Stephens, Taylor & Freedman 2019, Curr. Dev. Nutr. 3(6):nzz021 — Mycoprotein: The future of nutritious nonmeat protein, a symposium review",
        "kind": "Literature (symposium review)",
        "why": "Symposium review of Quorn-brand mycoprotein covering nutritional profile (~45% crude protein on dry basis, complete amino-acid profile, fibre content) and the human-grade microbial-protein category. The paper does NOT publish a delivered ingredient-grade selling price; the $6-10/kg band cited in the v10 HGP narrative is a 2024-2025 trade-survey figure for ingredient-grade mycoprotein, not a Finnigan 2019 number.",
        "used": "v10 protein-content and category anchor for human-grade microbial protein. The $6-10/kg ingredient-grade price band is sourced from independent trade surveys, not from this paper. Verified via DOI 10.1093/cdn/nzz021 (this is the correct journal and identifier; an earlier draft listed Trends in Food Science & Technology, which was incorrect).",
        "url": "https://doi.org/10.1093/cdn/nzz021",
        "url_note": "Replaces an earlier incorrect citation to Trends Food Sci. Technol. 94:1-5; that DOI does not resolve to a Finnigan paper.",
    },
    "ritala_2017": {
        "title": "Ritala, Hakkinen, Toivari & Wiebe 2017, Front. Microbiol. 8:2009 — Single cell protein — state-of-the-art, industrial landscape and patents 2001-2016",
        "kind": "Literature review (open access)",
        "why": "Open-access review covering bacterial, yeast, fungal, and algal single-cell protein. Documents crude-protein contents (55-75% dry basis for bacterial SCP), amino-acid profiles, and the industrial / patent landscape for microbial protein as food.",
        "used": "v10 anchor for the HGP crude-protein content (55-75% range, default 63%). The current regulatory-status language in the sidebar and main-page banner (no C. necator-derived SCP is GRAS-/novel-food-cleared; multi-year dossier timelines) is sourced from current regulatory-agency positions and recent precedent (Solein Singapore 2022, US self-affirmed GRAS 2024), not from this paper. An earlier draft cited Ritala 2017 as a regulatory-status source; that attribution has been narrowed here to protein-content only.",
        "url": "https://doi.org/10.3389/fmicb.2017.02009",
        "url_note": "",
    },
    "solar_foods_2024": {
        "title": "Solar Foods Oyj investor and regulatory disclosures for Solein, 2022-2024",
        "kind": "Commercial / regulatory disclosure",
        "why": "Public Solein disclosures cover: (a) commercial-scale production-cost target of ~EUR 5-7 per kg dry protein at the Factory 01 nameplate scale (investor presentations, not a delivered selling price); (b) regulatory clearances obtained to date — Singapore Food Agency novel-food approval (2022) and US FDA-acknowledged self-affirmed GRAS (2024). Solein is NOT yet EFSA novel-food approved as of the model date; the EFSA dossier is in process. Solein remains the closest commercial analog to a C. necator-derived HGP whole-cell mash.",
        "used": "v10 supporting anchor for the HGP production-cost framing (single-digit USD/kg dry protein at scale) and for the regulatory caveat that bacterial / single-cell HGP products typically require multi-year novel-food review. Used for context only — Solein's specific delivered selling price is not publicly fixed and is not copied directly into the model.",
        "url": "https://solarfoods.com/",
        "url_note": "The earlier draft of this entry stated 'EFSA novel-food clearance in 2024' and quoted a $5-8/kg selling price; both were incorrect. Solein's 2024 US clearance was self-affirmed GRAS (FDA had no questions), and Solar Foods' public numbers are production-cost targets, not delivered selling prices.",
    },
    "hgp_dsp_engineering_estimate": {
        "title": "HGP DSP cost build — internal engineering estimate (April 2026)",
        "kind": "Internal engineering estimate",
        "why": "The v10 HGP DSP cost line ($1.80/kg sellable HGP) is not lifted from a single published TEA. It is a bottom-up engineering estimate for a spray-dried whole-cell-mash flowsheet (harvest -> thermal lysis / inactivation -> TFF endotoxin reduction -> food-grade spray dryer -> sanitary packaging -> release QA), informed by: (a) the Quorn / Solein public flowsheets for spray-dried whole-cell ingredient; (b) Ritala et al. 2017 Front. Microbiol. (microbial-protein DSP review); (c) Jacquel et al. 2008 Biochem. Eng. J. for the non-chlorinated DSP cost envelope; (d) fermentation-industry vendor quotes for sanitary spray-drying CapEx bands (~$8-15M at Phase III scale). The $1.80/kg number should be treated as a Phase II / III engineering-stage estimate, not a literature-cited scalar.",
        "used": "v10 HGP DSP cost-line build ($1.80/kg sellable HGP; slider range $0.50-$5.00/kg). Decomposed in the memo as: endotoxin / LPS removal ~$1.05/kg, food-grade spray drying ~$0.50/kg, release QA and regulatory overhead ~$0.25/kg.",
        "url": "",
        "url_note": "Replaces an earlier citation to 'Van Loosdrecht et al. 2016' that could not be independently verified and whose stated scope (protein recovery for food-grade HGP) does not match the Experimental Methods in Wastewater Treatment volume. The underlying cost number is unchanged; only the sourcing framing has been corrected.",
    },
    "calysta_feedkind_2023": {
        "title": "Calysta FeedKind commercial disclosures and regulatory filings, 2023-2025",
        "kind": "Commercial disclosure",
        "why": "Calysta produces feed-grade single-cell protein from Methylococcus capsulatus (FeedKind). Public disclosures cover the downstream flowsheet (centrifuge + spray dry + pelletize) and feed-grade regulatory posture (US FDA AAFCO-listed for aquafeed; EU authorisation for salmonids). FeedKind provides the most directly comparable modern bacterial-SCP feed-grade cost/price anchor.",
        "used": "v10 feed-grade anchor only. Informs the v7/v10 feed-grade SCP price of $2.00/kg used as the baseline when HGP is off, and supports the centrifuge + spray-dry flowsheet for SCP DSP. Calysta has NOT publicly disclosed a human-grade / 'FeedKind-HP' selling price, so it is NOT used as an anchor for the v10 HGP selling-price band.",
        "url": "https://calysta.com/",
        "url_note": "An earlier draft cited a Calysta FeedKind-HP $3-6/kg lower anchor for the HGP price band; that number could not be verified against public Calysta disclosures and has been removed. FeedKind regulatory status is animal feed, not human food.",
    },
    "pohlmann_2006": {
        "title": "Pohlmann, Fricke, Reinecke, Kusian, Liesegang, Cramm, Eitinger, Ewering, Potter, Schwartz, Strittmatter, Voss, Gottschalk, Steinbuchel, Friedrich & Bowien 2006, Nat. Biotechnol. 24(10):1257-1262 — Genome sequence of the bioplastic-producing 'Knallgas' bacterium Ralstonia eutropha H16",
        "kind": "Genome reference",
        "why": "Definitive genome paper for C. necator H16 (formerly R. eutropha / Ralstonia eutropha). Locates and sequences the phaCAB operon (phaC class-I PHA synthase, phaA beta-ketothiolase, phaB acetoacetyl-CoA reductase) and related PHA-locus genes. The paper establishes the genomic substrate on which phaCAB knockouts are engineered; it does not itself report a phaC-deletion experiment.",
        "used": "v10 genome-level anchor for the phaCAB operon in the HGP-alone narrative. The functional polymer-negative phenotype of phaC-deletion strains is cited to Peoples & Sinskey 1989 and Slater et al. 1988 rather than to Pohlmann 2006.",
        "url": "https://doi.org/10.1038/nbt1244",
        "url_note": "",
    },
    "peoples_sinskey_1989": {
        "title": "Peoples & Sinskey 1989, J. Biol. Chem. 264(26):15298-15303 — Poly-beta-hydroxybutyrate (PHB) biosynthesis in Alcaligenes eutrophus H16: identification and characterization of the PHB polymerase gene (phbC)",
        "kind": "Literature (primary experimental)",
        "why": "Original identification and characterization of the phbC/phaC polymerase gene in A. eutrophus H16 (now C. necator H16). Reports that phaC-insertion / deletion mutants have no detectable PHB polymerase activity and do not accumulate PHB. This is the primary experimental anchor for the claim that a phaCAB knockout strain accumulates ~0% PHA.",
        "used": "v10 primary experimental anchor for the HGP-alone default of 0% residual PHB under a phaCAB knockout. Verified via DOI 10.1016/S0021-9258(19)84825-1 (paper content confirmed).",
        "url": "https://doi.org/10.1016/S0021-9258(19)84825-1",
        "url_note": "Replaces an earlier secondary citation of Budde 2011 as a 'phaCAB-KO phenotype' anchor; Budde 2011 actually reports PHB production in engineered emulsified-oil medium rather than a phaC-deletion knockout, so it is retained only as a fed-batch scale-up anchor (see separate budde_2011 entry).",
    },
    "slater_1988": {
        "title": "Slater, Voige & Dennis 1988, J. Bacteriol. 170(10):4431-4436 — Cloning and expression in Escherichia coli of the Alcaligenes eutrophus H16 poly-beta-hydroxybutyrate biosynthetic pathway",
        "kind": "Literature (primary experimental)",
        "why": "Companion primary reference to Peoples & Sinskey 1989. Clones the A. eutrophus PHB pathway into E. coli and establishes that phaC is the committed polymerase step; loss-of-function at phaC blocks polymer accumulation. Together with Peoples & Sinskey 1989 this defines the phaCAB-KO polymer-negative phenotype.",
        "used": "v10 supporting anchor for the HGP-alone 0% residual-PHB default (alongside Peoples & Sinskey 1989 and Pohlmann 2006).",
        "url": "https://doi.org/10.1128/jb.170.10.4431-4436.1988",
        "url_note": "",
    },
    "braunegg_1998": {
        "title": "Braunegg, Lefebvre & Genser 1998, J. Biotechnol. 65(2-3):127-161 — Polyhydroxyalkanoates, biopolyesters from renewable resources: Physiological and engineering aspects",
        "kind": "Literature review",
        "why": "Comprehensive review of PHA physiology in Cupriavidus / Ralstonia / Alcaligenes-class bacteria. Documents basal PHA accumulation under N-replete growth (5-15% of CDW) vs. accumulation phase under N-limitation (up to 80%). Provides the wild-type upper-bound on the HGP-alone residual-PHB slider (used when the phaCAB-KO strain is not yet available or is phenotypically leaky).",
        "used": "v10 upper-bound anchor on the HGP-alone residual-PHB slider (0-15% CDW) representing wild-type N-replete behavior, as an alternative to the phaCAB-KO default of 0%.",
        "url": "https://doi.org/10.1016/S0168-1656(98)00126-6",
        "url_note": "",
    },
    "khanna_2005": {
        "title": "Khanna & Srivastava 2005, Process Biochem. 40(2):607-619 — Recent advances in microbial polyhydroxyalkanoates",
        "kind": "Literature review",
        "why": "Secondary anchor for basal-PHA accumulation under growth-phase (N-replete) fermentation of C. necator and related organisms, and for the transition-point between growth-phase and accumulation-phase operation. Used alongside Braunegg 1998 to bound the HGP-alone wild-type residual-PHB range.",
        "used": "v10 secondary anchor for the wild-type portion of the HGP-alone residual-PHB slider (0-15% CDW); corroborates the 5-15% literature band for N-replete growth in the absence of a phaCAB knockout.",
        "url": "https://doi.org/10.1016/j.procbio.2004.01.053",
        "url_note": "",
    },
    "pem_benchmark": {
        "title": "NREL -- PEM electrolysis overview (~48-60 kWh/kg H2)",
        "kind": "Engineering benchmark",
        "why": "Contextual range for H2 electrolysis energy.",
        "used": "Used for the electrolysis energy recommended range of roughly 48-60 kWh per kg H2.",
        "url": "https://www.nrel.gov/hydrogen/electrolysis.html",
        "url_note": "Introductory overview, not a fixed kWh/kg H2 guarantee.",
    },
}

PARAMETER_REFERENCE_IDS: Dict[str, List[str]] = {
    "yield_h2": ["ishizaki_2001", "matassa_2016"],
    "yield_h2_con": ["ishizaki_2001", "matassa_2016"],
    "yield_h2_opt": ["ishizaki_2001", "matassa_2016"],
    "yield_dlp": ["wang_2022", "pubmed_40669633"],
    "yield_dlp_con": ["wang_2022", "pubmed_40669633"],
    "yield_dlp_opt": ["wang_2022", "pubmed_40669633"],
    "yield_molasses": ["dalsasso_2019"],
    "yield_molasses_con": ["dalsasso_2019"],
    "yield_molasses_opt": ["dalsasso_2019"],
    "titer_molasses_con": ["dalsasso_2019"],
    "titer_molasses_opt": ["dalsasso_2019"],
    "titer_dlp_con": ["pubmed_40669633"],
    "titer_dlp_opt": ["pubmed_40669633"],
    "electrolysis_kwh_per_kg_h2": ["pem_benchmark"],
    "dlp_price_per_kg_sugar": ["wang_2022", "pubmed_40669633"],
    "molasses_price_per_kg_sugar": ["imarc_molasses_2025"],
    "nh4so4_price_per_kg": ["imarc_ammonium_2025"],
}


def _dedupe(seq: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in seq:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  SCENARIO LABEL & REFERENCE-TRACE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def scenario_label(model_key: str, r: Any) -> str:
    if model_key == "scp":
        return f"{int(r.capacity_tpy):,} t/y | {_display_text(r.feed.value)} | {_display_text(r.mode.value)}"
    if model_key == "pha":
        return (f"{int(r.capacity_tpy):,} t/y | {_display_text(r.feed.value)} | {_display_text(r.mode.value)} | "
                f"{_display_text(r.product.value)} | {_display_text(r.titer_scenario.value)}")
    return (f"{int(r.capacity_tpy_cdw):,} t/y CDW | {_display_text(r.feed.value)} | {_display_text(r.mode.value)} | "
            f"{_display_text(r.polymer.value)} | {_display_text(r.titer_scenario.value)}")


def scenario_reference_ids(model_key: str, r: Any, assumption_kwargs: Dict[str, Any], defaults: Any) -> List[str]:
    ids = [
        "framework_2026",
        "fairfield_handoff_v7",
        "phycovax_costs_davis",
        "imarc_ammonium_2025",
    ]
    if model_key in {"pha", "bio"}:
        ids.extend([
            "kim_1994", "ryu_1997", "budde_2011",
            "kapritchkoff_2006", "hahn_1994", "jacquel_2008",
            "doi_1988", "madison_huisman_1999", "tianan_kaneka_2024",
        ])
    feed_name = r.feed.value
    if "H_2/CO_2" in feed_name or "H2" in feed_name:
        ids.extend(["ishizaki_2001", "matassa_2016", "pem_benchmark"])
    if feed_name == "DLP":
        ids.extend(["wang_2022", "pubmed_40669633"])
    if feed_name == "Molasses":
        ids.extend(["dalsasso_2019", "imarc_molasses_2025"])
    if feed_name == "Fructose" and model_key in {"pha", "bio"}:
        ids.append("ryu_1997")
    for name, value in assumption_kwargs.items():
        if changed(value, getattr(defaults, name)):
            ids.extend(PARAMETER_REFERENCE_IDS.get(name, []))
    return _dedupe(ids)


def scenario_specific_notes(model_key: str, r: Any, assumption_kwargs: Dict[str, Any], defaults: Any) -> List[str]:
    notes = []
    if model_key == "scp":
        notes.append(f"SCP model math for {_display_text(r.feed.value)} under {_display_text(r.mode.value)} fermentation.")
    elif model_key == "pha":
        notes.append(
            f"PHA model math for {_display_text(r.feed.value)}, {_display_text(r.mode.value)}, "
            f"{_display_text(r.product.value)}, {_display_text(r.titer_scenario.value)}."
        )
    else:
        notes.append(
            f"Biorefinery math for {_display_text(r.feed.value)}, {_display_text(r.mode.value)}, "
            f"{_display_text(r.polymer.value)}, {_display_text(r.titer_scenario.value)}."
        )
    untethered = []
    for name, value in assumption_kwargs.items():
        if changed(value, getattr(defaults, name)):
            basis = MODEL_META.get(model_key, {}).get(name, {}).get("basis", "untethered")
            if basis in {"scenario", "untethered"}:
                untethered.append(MODEL_META.get(model_key, {}).get(name, {}).get("label", humanize(name)))
    if untethered:
        notes.append("Scenario-only edits (not literature-locked): " + ", ".join(f"**{x}**" for x in untethered))
    return notes


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR ASSUMPTION RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_assumptions(model_key: str, defaults: Any) -> Tuple[Dict[str, Any], List[str], List[str], List[Dict[str, Any]], List[str]]:
    meta = MODEL_META.get(model_key, {})
    section_map = SECTION_MAP.get(model_key, {})
    values: Dict[str, Any] = {}
    warnings: List[str] = []
    scenario_notes: List[str] = []
    audit_rows: List[Dict[str, Any]] = []
    skipped: List[str] = []
    rendered_sections: set[str] = set()

    # capex_threshold is an internal filter (items ≤ threshold get included as minor CapEx).
    # It is not a cost the user should tweak directly; hide it and keep it at its default.
    _HIDDEN = {"capex_threshold"}

    editable = []
    for f in fields(defaults):
        if f.name in _HIDDEN:
            continue
        dv = getattr(defaults, f.name)
        if isinstance(dv, (int, float, bool)):
            editable.append((f.name, dv))
        else:
            skipped.append(f.name)

    grouped: Dict[str, List[Tuple[str, Any]]] = {}
    for name, dv in editable:
        grouped.setdefault(section_map.get(name, "Other Inputs"), []).append((name, dv))

    for section in SECTION_ORDER:
        items = grouped.get(section, [])
        if not items:
            continue
        rendered_sections.add(section)
        with st.sidebar.expander(section, expanded=section in {"Fermentation", "Optimized PHA Basis", "Product"}):
            if section == "Finance & CapEx":
                fin = FINANCE_DEFAULTS[model_key]
                st.caption(
                    "Fairfield site model: the acquisition cost is a fixed $45 M "
                    "regardless of utilization (exponent = 0). "
                    "Retrofit / added CapEx is optional on top."
                )
                values["base_installed_capex_ref"] = st.slider(
                    "Facility acquisition cost ($M)",
                    min_value=0.0,
                    max_value=250.0,
                    value=float(st.session_state.get("base_installed_capex_ref", fin["base_installed_capex_ref"] / 1e6)),
                    step=1.0,
                    format="$%.1fM",
                    key="base_installed_capex_ref",
                    help=(
                        "Total acquisition cost for the Fairfield brewery. "
                        "This is a fixed lump sum — it does not scale with utilization."
                    ),
                ) * 1e6
                values["added_capex_ref"] = st.slider(
                    "Retrofit / added CapEx ($M)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(st.session_state.get("added_capex_ref", fin["added_capex_ref"] / 1e6)),
                    step=0.5,
                    format="$%.1fM",
                    key="added_capex_ref",
                    help=(
                        "Additional capital for DLP handling, PHA extraction equipment, "
                        "SCP drying, or other retrofits not included in the acquisition."
                    ),
                ) * 1e6
                values["capex_scaling_exponent"] = st.slider(
                    "CapEx scaling exponent",
                    min_value=0.00,
                    max_value=1.00,
                    value=float(st.session_state.get("capex_scaling_exponent", fin["capex_scaling_exponent"])),
                    step=0.05,
                    format="%.2f",
                    key="capex_scaling_exponent",
                    help=(
                        "0.00 = fixed acquisition (does not scale with capacity). "
                        "0.60 = classic six-tenths rule for greenfield builds."
                    ),
                )
                values["target_sell_price"] = st.slider(
                    _target_price_label(model_key),
                    min_value=0.50,
                    max_value=20.0,
                    value=st.session_state.get("target_sell_price", 3.0),
                    step=0.25,
                    format="$%.2f/kg",
                    key="target_sell_price",
                    help=_target_price_help(model_key),
                )
            for name, dv in items:
                spec = meta.get(name, {})
                label = spec.get("label", humanize(name))
                note = spec.get("note")
                key = f"{model_key}_{name}"

                if isinstance(dv, bool):
                    value = st.checkbox(label, value=dv, help=note, key=key)
                elif name.startswith("labor_"):
                    value = st.slider(label, min_value=250_000.0, max_value=10_000_000.0,
                                      value=float(dv), step=250_000.0, format="$%.0f",
                                      help=(note or "Scenario input."), key=key)
                elif name == "npv_discount_rate":
                    vpct = st.slider(label + " (%)", min_value=1, max_value=30,
                                     value=int(round(float(dv) * 100)), step=1,
                                     help=(note or "Finance assumption."), key=key)
                    value = vpct / 100.0
                else:
                    wa: Dict[str, Any] = {"label": label, "value": dv, "step": step_for(dv), "help": note, "key": key}
                    if isinstance(dv, float):
                        wa["format"] = "%.4f" if abs(dv) < 1 else "%.3f"
                    value = st.number_input(**wa)

                values[name] = value
                basis = spec.get("basis", "untethered")
                rec = spec.get("recommended")
                status = "Default"
                if changed(value, dv):
                    status = "Edited"
                if rec and not isinstance(value, bool):
                    lo, hi = rec
                    if float(value) < lo or float(value) > hi:
                        status = "Outside range"
                        warnings.append(f"`{label}` = {value:g} is outside the recommended range {lo:g} -- {hi:g}.")
                elif basis in {"scenario", "untethered"} and changed(value, dv):
                    scenario_notes.append(f"`{label}` edited from default; not locked to a literature range.")
                audit_rows.append({"Parameter": label, "Value": value, "Basis": basis,
                                   "Recommended range": f"{rec[0]:g} -- {rec[1]:g}" if rec else "No fixed band",
                                   "Status": status})

    for section, items in grouped.items():
        if section in rendered_sections:
            continue
        with st.sidebar.expander(section, expanded=False):
            for name, dv in items:
                spec = meta.get(name, {})
                label = spec.get("label", humanize(name))
                key = f"{model_key}_{name}"
                if isinstance(dv, bool):
                    values[name] = st.checkbox(label, value=dv, key=key)
                else:
                    values[name] = st.number_input(label, value=dv, step=step_for(dv), key=key)

    # Re-inject hidden defaults so the model still receives them
    for f in fields(defaults):
        if f.name in _HIDDEN and f.name not in values:
            values[f.name] = getattr(defaults, f.name)

    return values, warnings, scenario_notes, audit_rows, skipped


def add_derived_warnings(model_key: str, vals: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if model_key == "scp":
        t = float(vals["titer_g_per_L"])
        if t < 50 or t > 120:
            out.append(f"SCP titer ({t:g} g/L) outside 50--120 g/L nominal band.")
        if float(vals["working_volume_fraction"]) > 0.95:
            out.append("Working volume > 0.95 is unusually aggressive.")
    if model_key in {"pha", "bio"}:
        fac = float(vals["fedbatch_titer_factor"])
        for feed, titer, frac in [
            ("H2/CO2", vals["titer_h2_opt"], vals["phb_frac_h2_opt"]),
            ("Fructose", vals["titer_fructose_opt"], vals["phb_frac_fructose_opt"]),
            ("DLP", vals["titer_dlp_opt"], vals["phb_frac_dlp_opt"]),
            ("Molasses", vals["titer_molasses_opt"], vals["phb_frac_molasses_opt"]),
        ]:
            frac = float(frac)
            if frac <= 0:
                continue
            cdw = float(titer) / frac * fac
            if cdw < 50 or cdw > 120:
                out.append(f"{feed} opt. implies ~{cdw:.0f} g/L fed-batch CDW (outside 50--120 g/L).")
        if float(vals["extraction_recovery"]) > 0.95:
            out.append("PHA extraction recovery > 0.95 is optimistic.")
    if model_key == "bio" and float(vals["phb_market_price"]) < 1.5:
        out.append("PHB market price below PLA-parity ($1.50).")
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  RESULTS TABLE & KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def build_results_table(model_key: str, results: List[Any]) -> List[Dict[str, Any]]:
    if model_key == "scp":
        return [{"Capacity (t/y)": r.capacity_tpy, "Mode": _display_text(r.mode.value), "Feed": _display_text(r.feed.value),
                 "MSP ($/kg)": round(r.msp, 4), "Annual SCP (t/y)": round(r.annual_product_kg / 1e3, 1),
                 "Total cost (M$/yr)": round(r.total_annual_cost / 1e6, 3),
                 "Labor (M$/yr)": round(r.labor_cost / 1e6, 2),
                 "Substrate (M$/yr)": round(r.substrate_cost / 1e6, 3),
                 "Reactor (m3)": round(r.reactor_volume_m3, 1), "Downstream": _display_text(r.downstream),
                 } for r in sorted(results, key=lambda r: (r.capacity_tpy, r.mode.value, r.feed.value))]
    if model_key == "pha":
        return [{"Capacity (t/y)": r.capacity_tpy, "Mode": _display_text(r.mode.value), "Feed": _display_text(r.feed.value),
                 "Product": _display_text(r.product.value), "Scenario": _display_text(r.titer_scenario.value),
                 "MSP ($/kg)": round(r.msp, 4), "Annual PHA (t/y)": round(r.annual_product_kg / 1e3, 1),
                 "Total cost (M$/yr)": round(r.total_annual_cost / 1e6, 3),
                 "Labor (M$/yr)": round(r.labor_cost / 1e6, 2),
                 "Titer (g/L)": round(r.effective_titer_gL, 1),
                 "Reactor (m3)": round(r.reactor_volume_m3, 1), "Extraction": _display_text(r.extraction_method),
                 } for r in sorted(results, key=lambda r: (r.capacity_tpy, r.mode.value, r.feed.value,
                                                            r.product.value, r.titer_scenario.value))]
    return [{"CDW cap. (t/y)": r.capacity_tpy_cdw, "Mode": _display_text(r.mode.value), "Feed": _display_text(r.feed.value),
             "Polymer": _display_text(r.polymer.value), "Titer scenario": _display_text(r.titer_scenario.value),
             "PHA MSP standalone": round(r.pha_msp_standalone, 4),
             "PHA MSP w/ SCP": round(r.pha_msp_with_scp_credit, 4),
             "SCP MSP w/ PHA": round(r.scp_msp_with_pha_credit, 4),
             "Advantage": round(r.biorefinery_advantage, 4),
             "Annual PHA (t/y)": round(r.annual_pha_product_kg / 1e3, 1),
             "Annual SCP (t/y)": round(r.annual_scp_product_kg / 1e3, 1),
             "Total cost (M$/yr)": round(r.total_annual_cost / 1e6, 3),
             "PHB titer (g/L)": round(r.effective_phb_titer_gL, 1),
             "Extraction": _display_text(r.extraction_method),
             } for r in sorted(results, key=lambda r: (r.capacity_tpy_cdw, r.mode.value, r.feed.value,
                                                        r.polymer.value, r.titer_scenario.value))]


def render_key_metrics(
    model_key: str,
    results: List[Any],
    target_cap: float | None = None,
    target_label: str | None = None,
) -> None:
    if model_key == "scp":
        all_caps = sorted(set(r.capacity_tpy for r in results))
    elif model_key == "pha":
        all_caps = sorted(set(r.capacity_tpy for r in results))
    else:
        all_caps = sorted(set(r.capacity_tpy_cdw for r in results))
    _ref_cap = target_cap if target_cap is not None else (all_caps[len(all_caps) // 2] if all_caps else 1_200.0)
    _phase_lbl = target_label or f"{_ref_cap:,.0f} t/y"

    def _same_cap(a: float, b: float) -> bool:
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-6)

    if model_key == "scp":
        _section(f"Lowest SCP MSP at {_phase_lbl}")
        pool = [r for r in results if _same_cap(r.capacity_tpy, _ref_cap)]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.msp)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("MSP ($/kg)", f"${best.msp:.3f}")
        c2.metric("Feedstock", _display_text(best.feed.value))
        c3.metric("Mode", _display_text(best.mode.value))
        c4.metric("Annual SCP (t/y)", f"{best.annual_product_kg / 1e3:,.0f}")
        c5.metric("Reactor (m³)", f"{best.reactor_volume_m3:,.0f}")
    elif model_key == "pha":
        _section(f"Lowest PHA MSP at {_phase_lbl}")
        pool = [r for r in results if _same_cap(r.capacity_tpy, _ref_cap)]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.msp)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("MSP ($/kg)", f"${best.msp:.3f}")
        c2.metric("Feedstock", _display_text(best.feed.value))
        c3.metric("Mode", _display_text(best.mode.value))
        c4.metric("Product", _display_text(best.product.value))
        c5.metric("Scenario", _display_text(best.titer_scenario.value))
        c6.metric("Annual PHA (t/y)", f"{best.annual_product_kg / 1e3:,.0f}")
    else:
        _section(f"Lowest PHA MSP with SCP credit at {_phase_lbl}")
        pool = [r for r in results if _same_cap(r.capacity_tpy_cdw, _ref_cap)]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.pha_msp_with_scp_credit)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("PHA MSP w/ SCP", f"${best.pha_msp_with_scp_credit:.3f}")
        c2.metric("PHA standalone", f"${best.pha_msp_standalone:.3f}")
        c3.metric("SCP MSP w/ PHA", f"${best.scp_msp_with_pha_credit:.3f}")
        c4.metric("Feedstock", _display_text(best.feed.value))
        c5.metric("Polymer", _display_text(best.polymer.value))
        c6.metric("Scenario", _display_text(best.titer_scenario.value))


# ═══════════════════════════════════════════════════════════════════════════════
#  CAPITAL PAYBACK FIGURE
# ═══════════════════════════════════════════════════════════════════════════════

def _best_scenario_per_capacity(model_key: str, results: List[Any]) -> Dict[float, Any]:
    if model_key == "scp":
        caps = sorted(set(r.capacity_tpy for r in results))
        return {c: min([r for r in results if r.capacity_tpy == c], key=lambda r: r.msp) for c in caps}
    if model_key == "pha":
        caps = sorted(set(r.capacity_tpy for r in results))
        return {c: min([r for r in results if r.capacity_tpy == c], key=lambda r: r.msp) for c in caps}
    caps = sorted(set(r.capacity_tpy_cdw for r in results))
    return {c: min([r for r in results if r.capacity_tpy_cdw == c],
                   key=lambda r: r.pha_msp_with_scp_credit) for c in caps}


def _annual_revenue(model_key: str, r: Any, sell_price: float, scp_price: float = 2.0) -> float:
    if model_key == "bio":
        return r.annual_pha_product_kg * sell_price + r.annual_scp_product_kg * scp_price
    return r.annual_product_kg * sell_price


def _result_capacity(model_key: str, r: Any) -> float:
    if model_key == "bio":
        return float(r.capacity_tpy_cdw)
    return float(r.capacity_tpy)


def _scaled_capex_from_reference(capacity: float, ref_capex: float, ref_capacity: float, exponent: float) -> float:
    if capacity <= 0 or ref_capacity <= 0 or ref_capex <= 0:
        return 0.0
    return ref_capex * (capacity / ref_capacity) ** exponent


def _base_purchase_capex(r: Any) -> float:
    """Initial purchase cost already embedded in the base model's included minor CapEx."""
    included = getattr(r, "capex_included", [])
    total = 0.0
    for item in included:
        if len(item) >= 2:
            total += float(item[1])
    return total


def _annual_finance_profit(
    model_key: str,
    r: Any,
    sell_price: float,
    scp_price: float = 2.0,
) -> float:
    """Annual project cash flow used for payback/IRR.

    Start from revenue minus total annual cost, then add back annualized CapEx charges
    because those are financing/depreciation-style placeholders rather than cash OPEX.
    """
    revenue = _annual_revenue(model_key, r, sell_price, scp_price)
    minor_capex_annual = float(getattr(r, "minor_capex_annual", 0.0))
    major_installed_capex_annual = float(getattr(r, "major_installed_capex_annual_v3", 0.0))
    return revenue - (float(r.total_annual_cost) - minor_capex_annual - major_installed_capex_annual)


def _empty_finance_figure(title: str, message: str) -> plt.Figure:
    """Return a full-size placeholder figure for invalid finance inputs."""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis("off")
    ax.set_title(title, fontsize=15, pad=18)
    ax.text(
        0.5,
        0.52,
        message,
        ha="center",
        va="center",
        fontsize=13,
        color="#334155",
        linespacing=1.5,
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8fafc", edgecolor="#cbd5e1"),
        transform=ax.transAxes,
    )
    return fig


def fig_capital_payback(model_key: str, results: List[Any],
                        sell_price: float,
                        discount_rate: float, scp_price: float = 2.0) -> plt.Figure:
    best_map = _best_scenario_per_capacity(model_key, results)
    total_project_capex = (
        sum(float(getattr(best, "total_project_capex_purchase_v3", 0.0)) for best in best_map.values())
        / max(len(best_map), 1)
    )

    if total_project_capex <= 0:
        return _empty_finance_figure(
            "Capital Payback",
            "No project CapEx was detected.\n\n"
            "Set a base installed CapEx in `Finance & CapEx` to calculate payback.",
        )

    prices = np.linspace(0.3, 20.0, 300)
    colors = ["#0ea5e9", "#f97316", "#10b981", "#8b5cf6", "#ef4444"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)

    # ── Left panel: simple payback vs. selling price, one line per capacity ──
    for idx, (cap, best) in enumerate(best_map.items()):
        project_capex = float(getattr(best, "total_project_capex_purchase_v3", 0.0))
        paybacks = []
        for p in prices:
            profit = _annual_finance_profit(model_key, best, p, scp_price)
            paybacks.append(project_capex / profit if profit > 0 else np.nan)
        _plbl = PHASE_LABELS.get(cap, f"{cap:,.0f} t/y")
        ax1.plot(prices, paybacks, color=colors[idx % len(colors)],
                 linewidth=2, label=_plbl)

    ax1.axhline(5, color="#22c55e", ls="--", lw=1, alpha=0.6)
    ax1.axhline(10, color="#f59e0b", ls="--", lw=1, alpha=0.6)
    ax1.axhline(15, color="#ef4444", ls="--", lw=1, alpha=0.6)
    ax1.text(prices[-1] * 0.98, 5.3, "5 yr", ha="right", fontsize=8, color="#22c55e")
    ax1.text(prices[-1] * 0.98, 10.3, "10 yr", ha="right", fontsize=8, color="#f59e0b")
    ax1.text(prices[-1] * 0.98, 15.3, "15 yr", ha="right", fontsize=8, color="#ef4444")
    ax1.axvline(sell_price, color="grey", ls=":", lw=1, alpha=0.8)
    ax1.set_xlabel(_swept_price_axis_label(model_key))
    ax1.set_ylabel("Simple payback period (years)")
    ax1.set_ylim(0, 25)
    ax1.set_title(f"Simple Payback vs. {_swept_price_title_label(model_key)}")
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(axis="y", alpha=0.3)

    # ── Right panel: cumulative discounted cash flow at chosen price, Phase II ──
    _all_caps = sorted(best_map.keys())
    target_cap = _all_caps[len(_all_caps) // 2] if _all_caps else 1_200.0
    best_3500 = best_map.get(target_cap, list(best_map.values())[len(best_map) // 2])
    project_capex_3500 = float(getattr(best_3500, "total_project_capex_purchase_v3", 0.0))
    annual_profit = _annual_finance_profit(model_key, best_3500, sell_price, scp_price)
    years = np.arange(0, 21)
    cumulative = np.zeros(len(years))
    cumulative[0] = -project_capex_3500
    for t in range(1, len(years)):
        cumulative[t] = cumulative[t - 1] + annual_profit / (1 + discount_rate) ** t

    ax2.plot(years, cumulative / 1e6, color="#0ea5e9", linewidth=2.5)
    ax2.fill_between(years, cumulative / 1e6, 0,
                     where=(cumulative < 0), color="#ef4444", alpha=0.10)
    ax2.fill_between(years, cumulative / 1e6, 0,
                     where=(cumulative >= 0), color="#22c55e", alpha=0.10)
    ax2.axhline(0, color="black", lw=0.8, alpha=0.4)

    # mark discounted payback year
    crossings = np.where(np.diff(np.sign(cumulative)))[0]
    if len(crossings) > 0:
        cross_yr = crossings[0]
        if cumulative[cross_yr + 1] != cumulative[cross_yr]:
            frac = -cumulative[cross_yr] / (cumulative[cross_yr + 1] - cumulative[cross_yr])
            exact_yr = cross_yr + frac
        else:
            exact_yr = float(cross_yr)
        ax2.axvline(exact_yr, color="#22c55e", ls="--", lw=1)
        ax2.annotate(f"Payback {exact_yr:.1f} yr", xy=(exact_yr, 0),
                     xytext=(exact_yr + 1.5, cumulative.max() / 1e6 * 0.3 if cumulative.max() > 0 else -project_capex_3500 / 1e6 * 0.3),
                     fontsize=9, color="#22c55e",
                     arrowprops=dict(arrowstyle="->", color="#22c55e", lw=1.2))
    elif annual_profit <= 0:
        ax2.text(10, -project_capex_3500 / 1e6 * 0.5, "Never pays back\nat this price",
                 ha="center", fontsize=11, color="#ef4444", weight="bold")

    ax2.set_xlabel("Year")
    ax2.set_ylabel("Cumulative discounted cash flow (M$)")
    _dcf_lbl = PHASE_LABELS.get(target_cap, f"{target_cap:,.0f} t/y")
    ax2.set_title(f"Discounted CF at {_selected_price_context(model_key, sell_price, scp_price)}, {_dcf_lbl}")
    ax2.grid(axis="y", alpha=0.3)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  IRR (Internal Rate of Return) FIGURE
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_irr(capex: float, annual_profit: float, n_years: int) -> float:
    """Newton-Raphson solver for IRR given uniform annual cash flows.

    Solves: 0 = -capex + sum_{t=1}^{N} annual_profit / (1+r)^t
    Returns NaN if no solution found or profit <= 0.
    """
    if annual_profit <= 0 or capex <= 0:
        return float("nan")
    r = 0.10  # initial guess
    for _ in range(200):
        npv = -capex + sum(annual_profit / (1 + r) ** t for t in range(1, n_years + 1))
        dnpv = sum(-t * annual_profit / (1 + r) ** (t + 1) for t in range(1, n_years + 1))
        if abs(dnpv) < 1e-14:
            break
        r_new = r - npv / dnpv
        if r_new < -0.5:
            r_new = -0.49
        if r_new > 10.0:
            r_new = 10.0
        if abs(r_new - r) < 1e-9:
            r = r_new
            break
        r = r_new
    check = -capex + sum(annual_profit / (1 + r) ** t for t in range(1, n_years + 1))
    return r if abs(check) < capex * 1e-6 else float("nan")


def fig_irr_analysis(model_key: str, results: List[Any],
                     sell_price: float,
                     n_years: int, scp_price: float = 2.0) -> plt.Figure:
    best_map = _best_scenario_per_capacity(model_key, results)
    total_project_capex = (
        sum(float(getattr(best, "total_project_capex_purchase_v3", 0.0)) for best in best_map.values())
        / max(len(best_map), 1)
    )
    if total_project_capex <= 0:
        return _empty_finance_figure(
            "IRR Analysis",
            "IRR requires an upfront project investment.\n\n"
            "Set a base installed CapEx in `Finance & CapEx` to model total project IRR.",
        )

    prices = np.linspace(0.5, 20.0, 250)
    colors = ["#0ea5e9", "#f97316", "#10b981", "#8b5cf6", "#ef4444"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
    finite_left = False
    finite_right = False

    # ── Left panel: IRR vs. selling price, one line per capacity ──
    for idx, (cap, best) in enumerate(best_map.items()):
        project_capex = float(getattr(best, "total_project_capex_purchase_v3", 0.0))
        irrs = []
        for p in prices:
            profit = _annual_finance_profit(model_key, best, p, scp_price)
            irrs.append(_compute_irr(project_capex, profit, n_years) * 100)
        finite_left = finite_left or np.isfinite(irrs).any()
        _clbl = PHASE_LABELS.get(cap, f"{cap:,.0f} t/y")
        ax1.plot(prices, irrs, color=colors[idx % len(colors)],
                 linewidth=2, label=_clbl)

    ax1.axhline(8, color="#f59e0b", ls="--", lw=1, alpha=0.6)
    ax1.axhline(15, color="#22c55e", ls="--", lw=1, alpha=0.6)
    ax1.axhline(25, color="#0ea5e9", ls="--", lw=1, alpha=0.6)
    ax1.text(prices[-1] * 0.98, 8.8, "8% hurdle", ha="right", fontsize=8, color="#f59e0b")
    ax1.text(prices[-1] * 0.98, 15.8, "15% strong", ha="right", fontsize=8, color="#22c55e")
    ax1.text(prices[-1] * 0.98, 25.8, "25% excellent", ha="right", fontsize=8, color="#0ea5e9")
    ax1.axvline(sell_price, color="grey", ls=":", lw=1, alpha=0.8)
    ax1.set_xlabel(_swept_price_axis_label(model_key))
    ax1.set_ylabel("IRR (%)")
    ax1.set_ylim(-10, 80)
    ax1.set_title(f"IRR vs. {_swept_price_title_label(model_key)}")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(axis="y", alpha=0.3)

    # ── Right panel: IRR vs. CapEx at user's selling price, one line per cap ──
    max_capex_now = max(float(getattr(best, "total_project_capex_purchase_v3", 0.0)) for best in best_map.values())
    capex_range = np.linspace(max(1e6, 0.2 * max_capex_now), max(50e6, 2.5 * max_capex_now), 250)
    for idx, (cap, best) in enumerate(best_map.items()):
        profit = _annual_finance_profit(model_key, best, sell_price, scp_price)
        irrs = [_compute_irr(cx, profit, n_years) * 100 for cx in capex_range]
        finite_right = finite_right or np.isfinite(irrs).any()
        _clbl2 = PHASE_LABELS.get(cap, f"{cap:,.0f} t/y")
        ax2.plot(capex_range / 1e6, irrs, color=colors[idx % len(colors)],
                 linewidth=2, label=_clbl2)

    ax2.axhline(8, color="#f59e0b", ls="--", lw=1, alpha=0.6)
    ax2.axhline(15, color="#22c55e", ls="--", lw=1, alpha=0.6)
    _irr_caps = sorted(best_map.keys())
    _irr_mid = _irr_caps[len(_irr_caps) // 2] if _irr_caps else 1_200.0
    current_ref = best_map.get(_irr_mid, list(best_map.values())[len(best_map) // 2])
    current_capex = float(getattr(current_ref, "total_project_capex_purchase_v3", 0.0))
    ax2.axvline(current_capex / 1e6, color="grey", ls=":", lw=1, alpha=0.8)
    ax2.set_xlabel("Total installed CapEx (M$)")
    ax2.set_ylabel("IRR (%)")
    ax2.set_ylim(-10, 80)
    ax2.set_title(f"IRR vs. CapEx at {_selected_price_context(model_key, sell_price, scp_price)}")
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(axis="y", alpha=0.3)

    if not finite_left:
        ax1.cla()
        ax1.axis("off")
        ax1.set_title("IRR vs. Selling Price")
        ax1.text(
            0.5,
            0.5,
            "No valid IRR under the current inputs.\n\n"
            "Try increasing selling price, reducing Added CapEx,\n"
            "or lowering annual operating cost.",
            ha="center",
            va="center",
            fontsize=12,
            color="#334155",
            bbox=dict(boxstyle="round,pad=0.7", facecolor="#f8fafc", edgecolor="#cbd5e1"),
            transform=ax1.transAxes,
        )

    if not finite_right:
        ax2.cla()
        ax2.axis("off")
        ax2.set_title(f"IRR vs. CapEx at {_selected_price_context(model_key, sell_price, scp_price)}")
        ax2.text(
            0.5,
            0.5,
            "No valid IRR across the current CapEx range.\n\n"
            "At this selling price, the project does not clear\n"
            "a positive discounted return for the tested capacities.",
            ha="center",
            va="center",
            fontsize=12,
            color="#334155",
            bbox=dict(boxstyle="round,pad=0.7", facecolor="#f8fafc", edgecolor="#cbd5e1"),
            transform=ax2.transAxes,
        )

    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  FAIRFIELD-SPECIFIC FIGURES
# ═══════════════════════════════════════════════════════════════════════════════

def _msp_metric(model_key: str, r: Any) -> float:
    if model_key == "bio":
        return float(r.pha_msp_with_scp_credit)
    return float(r.msp)


def _best_result_at_capacity(model_key: str, results: List[Any], target_cap: float) -> Any:
    subset = [r for r in results if math.isclose(_result_capacity(model_key, r), float(target_cap), rel_tol=1e-9, abs_tol=1e-6)]
    if not subset:
        subset = results
    if model_key == "bio":
        return min(subset, key=lambda r: r.pha_msp_with_scp_credit)
    return min(subset, key=lambda r: r.msp)


def _sorted_capacity_points(model_key: str, results: List[Any], util_by_cap: Dict[float, float]) -> List[Tuple[float, float, Any]]:
    pts: List[Tuple[float, float, Any]] = []
    for cap, util in util_by_cap.items():
        pts.append((float(cap), float(util), _best_result_at_capacity(model_key, results, cap)))
    pts.sort(key=lambda item: (item[1], item[0]))
    return pts


def _selected_cost_components(r: Any) -> List[Tuple[str, float]]:
    items = [
        ("Substrate", float(getattr(r, "substrate_cost", 0.0))),
        ("Pretreatment", float(getattr(r, "pretreatment_cost", 0.0))),
        ("Nitrogen", float(getattr(r, "nitrogen_cost", 0.0))),
        ("Aeration", float(getattr(r, "aeration_cost", 0.0))),
        ("Harvesting", float(getattr(r, "harvesting_cost", 0.0))),
        ("Downstream", float(getattr(r, "downstream_processing_cost", 0.0))),
        ("Extraction", float(getattr(r, "extraction_cost", 0.0))),
        ("PHA drying", float(getattr(r, "pha_drying_cost", 0.0))),
        ("Propionate", float(getattr(r, "propionate_cost", 0.0))),
        ("SCP processing", float(getattr(r, "scp_processing_cost", 0.0))),
        ("SCP drying", float(getattr(r, "scp_drying_cost", 0.0))),
        ("Labor", float(getattr(r, "labor_cost", 0.0))),
        ("Minor CapEx", float(getattr(r, "minor_capex_annual", 0.0))),
        ("Installed CapEx", float(getattr(r, "major_installed_capex_annual_v3", 0.0))),
    ]
    return [(name, value) for name, value in items if value > 0]


def _fairfield_output_panel(ax: Any, model_key: str, r: Any) -> None:
    if model_key == "bio":
        pha_t = r.annual_pha_product_kg / 1e3
        scp_t = r.annual_scp_product_kg / 1e3
        ax.bar(["PHA", "SCP"], [pha_t, scp_t], color=["#0ea5e9", "#22c55e"], edgecolor="white", linewidth=0.8)
        ax.set_ylabel("Annual product output (t/y)")
        ax.set_title("Annual product output")
        for i, val in enumerate([pha_t, scp_t]):
            ax.text(i, val + max(1.0, val * 0.03), f"{val:,.0f}", ha="center", fontsize=9)
    else:
        out_t = r.annual_product_kg / 1e3
        lbl = "SCP" if model_key == "scp" else "PHA"
        ax.bar([lbl], [out_t], color="#0ea5e9", edgecolor="white", linewidth=0.8)
        ax.set_ylabel("Annual product output (t/y)")
        ax.set_title("Annual product output")
        ax.text(0, out_t + max(1.0, out_t * 0.03), f"{out_t:,.0f}", ha="center", fontsize=9)
    ax.grid(axis="y", alpha=0.25)


def fig_fairfield_utilization_economics(
    model_key: str,
    results: List[Any],
    util_by_cap: Dict[float, float],
    sell_price: float,
    scp_price: float = 2.0,
) -> plt.Figure:
    pts = _sorted_capacity_points(model_key, results, util_by_cap)
    utils = [u for _, u, _ in pts]
    labels = [f"{u:.0f}%" for u in utils]
    msps = [_msp_metric(model_key, r) for _, _, r in pts]
    cashflows = [_annual_finance_profit(model_key, r, sell_price, scp_price) / 1e6 for _, _, r in pts]
    capacities = [cap for cap, _, _ in pts]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.5), constrained_layout=True)

    x = np.arange(len(utils))
    bars = ax1.bar(x, capacities, color="#38bdf8", edgecolor="white", linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Facility utilization (%)")
    ax1.set_ylabel("Implied CDW capacity (t/y)")
    ax1.set_title("Fairfield capacity implied by utilization")
    for bar, cap in zip(bars, capacities):
        ax1.text(bar.get_x() + bar.get_width() / 2, cap + max(5.0, cap * 0.02), f"{cap:,.0f}", ha="center", fontsize=9)
    ax1.grid(axis="y", alpha=0.25)

    ax2b = ax2.twinx()
    ax2.plot(utils, msps, marker="o", color="#0f172a", linewidth=2.4, label="MSP")
    ax2b.bar(utils, cashflows, width=5.5, alpha=0.28, color="#22c55e", label="Cash flow")
    ax2.set_xlabel("Facility utilization (%)")
    ax2.set_ylabel("MSP ($/kg)")
    ax2b.set_ylabel("Annual cash flow (M$/yr)")
    ax2.set_title(f"Economic response to Fairfield ramp at {_selected_price_context(model_key, sell_price, scp_price)}")
    ax2.grid(axis="y", alpha=0.25)
    ax2.axhline(msps[-1] if msps else 0.0, color="#94a3b8", ls=":", lw=0.8, alpha=0.6)

    return fig


def fig_fairfield_selected_summary(
    model_key: str,
    results: List[Any],
    selected_cap: float,
    selected_label: str,
    sell_price: float,
    scp_price: float = 2.0,
) -> plt.Figure:
    r = _best_result_at_capacity(model_key, results, selected_cap)
    revenue = _annual_revenue(model_key, r, sell_price, scp_price) / 1e6
    cost = float(r.total_annual_cost) / 1e6
    cash = _annual_finance_profit(model_key, r, sell_price, scp_price) / 1e6

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.6), constrained_layout=True)
    _fairfield_output_panel(ax1, model_key, r)

    econ_labels = ["Revenue", "Annual cost", "Cash flow"]
    econ_vals = [revenue, cost, cash]
    econ_colors = ["#22c55e", "#ef4444", "#0ea5e9" if cash >= 0 else "#f59e0b"]
    bars = ax2.bar(econ_labels, econ_vals, color=econ_colors, edgecolor="white", linewidth=0.8)
    ax2.set_ylabel("M$/yr")
    ax2.set_title("Annual economics at selected operating point")
    for bar, val in zip(bars, econ_vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + max(0.05, abs(val) * 0.03), f"{val:,.2f}", ha="center", fontsize=9)
    ax2.grid(axis="y", alpha=0.25)

    if model_key == "bio":
        subtitle = (
            f"{selected_label} | {_display_text(r.feed.value)} | {_display_text(r.mode.value)} | "
            f"{_display_text(r.polymer.value)} | {_display_text(r.titer_scenario.value)}"
        )
    elif model_key == "pha":
        subtitle = (
            f"{selected_label} | {_display_text(r.feed.value)} | {_display_text(r.mode.value)} | "
            f"{_display_text(r.product.value)} | {_display_text(r.titer_scenario.value)}"
        )
    else:
        subtitle = f"{selected_label} | {_display_text(r.feed.value)} | {_display_text(r.mode.value)}"
    fig.suptitle(f"Selected Fairfield operating point\n{subtitle}", y=1.02, fontsize=14, fontweight="bold")
    return fig


def fig_fairfield_selected_cost_structure(
    model_key: str,
    results: List[Any],
    selected_cap: float,
    selected_label: str,
) -> plt.Figure:
    r = _best_result_at_capacity(model_key, results, selected_cap)
    comps = _selected_cost_components(r)
    comps.sort(key=lambda item: item[1], reverse=True)
    names = [name for name, _ in comps]
    vals = [value / 1e6 for _, value in comps]

    fig, ax = plt.subplots(figsize=(13.5, 7.0), constrained_layout=True)
    y = np.arange(len(names))
    ax.barh(y, vals, color="#38bdf8", edgecolor="white", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Annual cost contribution (M$/yr)")
    ax.set_title(f"Selected Fairfield annual cost structure — {selected_label}")
    for i, val in enumerate(vals):
        ax.text(val + max(0.02, val * 0.02), i, f"{val:,.2f}", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.25)
    return fig


def fig_fairfield_npv_vs_price(
    model_key: str,
    results: List[Any],
    selected_cap: float,
    selected_label: str,
    current_price: float,
    discount_rate: float,
    n_years: int,
    scp_price: float = 2.0,
) -> plt.Figure:
    r = _best_result_at_capacity(model_key, results, selected_cap)
    prices = np.linspace(0.3, 20.0, 300)
    npvs = []
    for p in prices:
        revenue = _annual_revenue(model_key, r, p, scp_price)
        cash = revenue - float(r.total_annual_cost)
        npv = -float(getattr(r, "total_project_capex_purchase_v3", 0.0)) + sum(
            cash / (1 + discount_rate) ** t for t in range(1, n_years + 1)
        )
        npvs.append(npv / 1e6)

    fig, ax = plt.subplots(figsize=(13.5, 6.7), constrained_layout=True)
    ax.plot(prices, npvs, color="#0ea5e9", linewidth=2.5)
    ax.axhline(0, color="#334155", lw=1.0)
    ax.axvline(current_price, color="#f97316", ls="--", lw=1.0)
    ax.fill_between(prices, npvs, 0, where=(np.array(npvs) >= 0), color="#22c55e", alpha=0.10)
    ax.fill_between(prices, npvs, 0, where=(np.array(npvs) < 0), color="#ef4444", alpha=0.08)
    ax.set_xlabel(_swept_price_axis_label(model_key))
    ax.set_ylabel(f"Project NPV (M$)")
    ax.set_title(f"Fairfield NPV vs selling price — {selected_label}")
    ax.grid(alpha=0.25)
    return fig


def fig_fairfield_irr_vs_price(
    model_key: str,
    results: List[Any],
    selected_cap: float,
    selected_label: str,
    current_price: float,
    n_years: int,
    scp_price: float = 2.0,
) -> plt.Figure:
    r = _best_result_at_capacity(model_key, results, selected_cap)
    capex = float(getattr(r, "total_project_capex_purchase_v3", 0.0))
    if capex <= 0:
        return _empty_finance_figure("Fairfield IRR vs Selling Price", "Set acquisition / retrofit CapEx to calculate IRR.")

    prices = np.linspace(0.3, 20.0, 300)
    irrs = [_compute_irr(capex, _annual_finance_profit(model_key, r, p, scp_price), n_years) * 100 for p in prices]

    fig, ax = plt.subplots(figsize=(13.5, 6.7), constrained_layout=True)
    ax.plot(prices, irrs, color="#8b5cf6", linewidth=2.5)
    ax.axvline(current_price, color="#f97316", ls="--", lw=1.0)
    ax.axhline(8, color="#f59e0b", ls="--", lw=1, alpha=0.7)
    ax.axhline(15, color="#22c55e", ls="--", lw=1, alpha=0.7)
    ax.axhline(25, color="#0ea5e9", ls="--", lw=1, alpha=0.7)
    ax.set_xlabel(_swept_price_axis_label(model_key))
    ax.set_ylabel("Project IRR (%)")
    ax.set_ylim(-10, 80)
    ax.set_title(f"Fairfield IRR vs selling price — {selected_label}")
    ax.grid(alpha=0.25)
    return fig


def fig_fairfield_returns_vs_utilization(
    model_key: str,
    results: List[Any],
    util_by_cap: Dict[float, float],
    sell_price: float,
    discount_rate: float,
    n_years: int,
    scp_price: float = 2.0,
) -> plt.Figure:
    pts = _sorted_capacity_points(model_key, results, util_by_cap)
    utils = [u for _, u, _ in pts]
    npvs = []
    irrs = []
    paybacks = []
    for _, _, r in pts:
        capex = float(getattr(r, "total_project_capex_purchase_v3", 0.0))
        annual_cash = _annual_finance_profit(model_key, r, sell_price, scp_price)
        annual_book = _annual_revenue(model_key, r, sell_price, scp_price) - float(r.total_annual_cost)
        npv = -capex + sum(annual_book / (1 + discount_rate) ** t for t in range(1, n_years + 1))
        npvs.append(npv / 1e6)
        irrs.append(_compute_irr(capex, annual_cash, n_years) * 100)
        paybacks.append(capex / annual_cash if annual_cash > 0 else np.nan)

    fig, axes = plt.subplots(1, 3, figsize=(17.0, 6.2), constrained_layout=True)
    axes[0].plot(utils, npvs, marker="o", color="#0ea5e9", linewidth=2.3)
    axes[0].axhline(0, color="#334155", lw=1.0)
    axes[0].set_title("NPV vs utilization")
    axes[0].set_xlabel("Utilization (%)")
    axes[0].set_ylabel("NPV (M$)")
    axes[0].grid(alpha=0.25)

    axes[1].plot(utils, irrs, marker="o", color="#8b5cf6", linewidth=2.3)
    axes[1].axhline(8, color="#f59e0b", ls="--", lw=1, alpha=0.7)
    axes[1].axhline(15, color="#22c55e", ls="--", lw=1, alpha=0.7)
    axes[1].set_title("IRR vs utilization")
    axes[1].set_xlabel("Utilization (%)")
    axes[1].set_ylabel("IRR (%)")
    axes[1].grid(alpha=0.25)

    axes[2].plot(utils, paybacks, marker="o", color="#f97316", linewidth=2.3)
    axes[2].axhline(5, color="#22c55e", ls="--", lw=1, alpha=0.7)
    axes[2].axhline(10, color="#f59e0b", ls="--", lw=1, alpha=0.7)
    axes[2].set_title("Simple payback vs utilization")
    axes[2].set_xlabel("Utilization (%)")
    axes[2].set_ylabel("Payback (years)")
    axes[2].set_ylim(0, 25)
    axes[2].grid(alpha=0.25)

    fig.suptitle(f"Fairfield project returns at {_selected_price_context(model_key, sell_price, scp_price)}", y=1.02, fontsize=14, fontweight="bold")
    return fig


def fig_fairfield_discounted_cf(
    model_key: str,
    results: List[Any],
    selected_cap: float,
    selected_label: str,
    sell_price: float,
    discount_rate: float,
    scp_price: float = 2.0,
) -> plt.Figure:
    r = _best_result_at_capacity(model_key, results, selected_cap)
    capex = float(getattr(r, "total_project_capex_purchase_v3", 0.0))
    annual_cash = _annual_finance_profit(model_key, r, sell_price, scp_price)
    years = np.arange(0, 21)
    cumulative = np.zeros(len(years))
    cumulative[0] = -capex
    for t in range(1, len(years)):
        cumulative[t] = cumulative[t - 1] + annual_cash / (1 + discount_rate) ** t

    fig, ax = plt.subplots(figsize=(13.5, 6.7), constrained_layout=True)
    ax.plot(years, cumulative / 1e6, color="#0ea5e9", linewidth=2.5)
    ax.fill_between(years, cumulative / 1e6, 0, where=(cumulative < 0), color="#ef4444", alpha=0.10)
    ax.fill_between(years, cumulative / 1e6, 0, where=(cumulative >= 0), color="#22c55e", alpha=0.10)
    ax.axhline(0, color="#334155", lw=1.0)
    crossings = np.where(np.diff(np.sign(cumulative)))[0]
    if len(crossings) > 0:
        cross_yr = crossings[0]
        if cumulative[cross_yr + 1] != cumulative[cross_yr]:
            frac = -cumulative[cross_yr] / (cumulative[cross_yr + 1] - cumulative[cross_yr])
            exact_yr = cross_yr + frac
        else:
            exact_yr = float(cross_yr)
        ax.axvline(exact_yr, color="#22c55e", ls="--", lw=1.0)
        ax.text(exact_yr + 0.2, 0.5, f"Payback {exact_yr:.1f} yr", color="#22c55e", fontsize=9)
    elif annual_cash <= 0:
        ax.text(10, -capex / 1e6 * 0.45, "Never pays back\nat this price", ha="center", color="#ef4444", fontsize=11, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative discounted cash flow (M$)")
    ax.set_title(f"Fairfield discounted cash flow — {selected_label}")
    ax.grid(alpha=0.25)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURE FORMULA EXPLANATIONS (plain English)
# ═══════════════════════════════════════════════════════════════════════════════

FIGURE_FORMULAS: Dict[str, str] = {
    "Fairfield Ramp Economics": (
        "Uses the Fairfield vessel-volume-to-capacity conversion to turn utilization (%) into implied annual capacity.\n\n"
        "Left panel: implied CDW capacity versus utilization.\n"
        "Right panel: MSP and annual cash flow versus utilization at the selected selling price.\n\n"
        "This directly answers how hard the site economics improve as the plant moves from ramp-up toward full use."
    ),
    "Fairfield Selected Scenario": (
        "Shows the chosen Fairfield operating point only.\n\n"
        "Left panel: annual product output at the selected utilization.\n"
        "Right panel: annual revenue, annual total cost, and annual project cash flow at the selected selling price."
    ),
    "Fairfield Selected Cost Structure": (
        "Breaks the selected Fairfield operating point into annual cost buckets in M$/yr.\n\n"
        "This includes operating costs plus annualized installed CapEx from the Fairfield finance layer."
    ),
    "Fairfield NPV vs Selling Price": (
        "For the selected Fairfield operating point, NPV is recalculated across a range of selling prices.\n\n"
        "NPV = -upfront project CapEx + sum of discounted annual profit over the project horizon."
    ),
    "Fairfield IRR vs Selling Price": (
        "For the selected Fairfield operating point, IRR is recalculated across a range of selling prices.\n\n"
        "IRR is the discount rate that drives project NPV to zero."
    ),
    "Fairfield Returns vs Utilization": (
        "Uses the Fairfield utilization points (selected plus 20/60/90% references) and computes project NPV, IRR, and payback at the current selling price.\n\n"
        "This directly answers how much ramp level matters for investor returns."
    ),
    "Fairfield Discounted Cash Flow": (
        "Plots cumulative discounted cash flow over time for the selected Fairfield operating point.\n\n"
        "Starts with upfront project CapEx in year 0, then adds discounted annual project cash flow each year."
    ),
    "MSP Overview": (
        "**Minimum Selling Price (MSP)** = Total Annual Cost / Annual Product Output (kg/yr).\n\n"
        "Total Annual Cost includes operating expenses (feedstock, energy, labor, nitrogen, etc.) "
        "**plus annualized Major CapEx** if set in the sidebar. "
        "The CapEx is annualized using the Capital Recovery Factor: "
        "CRF = r(1+r)^N / ((1+r)^N - 1), where r = discount rate and N = project years.\n\n"
        "MSP is the lowest price per kg you must charge to cover all yearly costs including capital recovery."
    ),
    "Scale Curve (Utilization Ramp)": (
        "Same MSP formula (Total Annual Cost / Annual Output) plotted against capacity (Phase I / II / III).\n\n"
        "At the Fairfield site, the **acquisition cost is fixed at $45 M** regardless of utilization. "
        "Higher utilization spreads that fixed annualized CapEx over more product, reducing MSP. "
        "This is the key driver of the ramp trajectory: reaching Phase III as quickly as possible "
        "is the single most important lever for cost competitiveness."
    ),
    "Cost Structure": (
        "Stacked bar chart decomposing the **total annual operating cost** into cost categories "
        "(substrate, energy, labor, nitrogen, aeration, downstream) at the selected utilization tier.\n\n"
        "Each bar is a different feedstock + fermentation mode combination."
    ),
    "Sensitivity Tornado": (
        "**One-At-a-Time (OAT) perturbation**: each model assumption is varied ±20% while all others "
        "stay at their defaults. The resulting MSP change is plotted as a horizontal bar.\n\n"
        "Longer bars = that input has a bigger impact on MSP. Helps identify which assumptions matter most."
    ),
    "NPV vs Selling Price": (
        "Same NPV formula, swept across a range of selling prices.\n\n"
        "The **x-intercept** (where NPV = 0) gives the breakeven selling price over the project lifetime.\n\n"
        "Annualized installed CapEx (acquisition + retrofit) is folded into the cost basis before NPV is computed."
    ),
    "Conservative vs Optimized": (
        "Compares MSP between **conservative** and **optimized** titer/yield/PHB-fraction assumptions.\n\n"
        "Optimized scenarios use higher titers and yields drawn from fed-batch literature (Kim 1994, Ryu 1997), "
        "so they produce more product per batch, lowering MSP."
    ),
    "PHB vs PHBV": (
        "Compares MSP for two bioplastic types:\n"
        "- **PHB** (homopolymer): simpler fermentation, no co-feed.\n"
        "- **PHBV** (copolymer): requires propionate as a co-feed, slightly lower yield.\n\n"
        "PHBV is more flexible/useful as a material but typically has a higher MSP due to the extra feedstock cost."
    ),
    "Biorefinery Advantage": (
        "**Advantage** = PHA MSP (standalone) - PHA MSP (with SCP credit).\n\n"
        "When you co-produce SCP alongside PHA, selling the SCP offsets some operating costs, "
        "reducing the price you need to charge for PHA. A positive advantage means the biorefinery is cheaper."
    ),
    "Revenue per Batch": (
        "**Batch Revenue** = (PHA produced per batch x PHA market price) + (SCP produced per batch x SCP market price).\n\n"
        "Shows gross income from each fermentation cycle before subtracting any costs."
    ),
    "Process Flow Diagram": (
        "Visual schematic of the biorefinery process -- not a financial calculation.\n\n"
        "Shows the flow from feedstock intake through fermentation, cell separation, "
        "PHA extraction, and SCP drying to the final two products."
    ),
    "Capital Payback": (
        "**Left panel -- Simple Payback**:\n"
        "Payback Period = Total Project CapEx / Annual Project Cash Flow.\n\n"
        "Total Project CapEx = minor CapEx from model + acquisition + retrofit.\n"
        "Annual Project Cash Flow = Revenue - cash operating cost.\n"
        "Annualized CapEx is added back to avoid double counting.\n\n"
        "At Fairfield, the **$45 M acquisition is fixed** — payback depends entirely on how quickly "
        "the facility reaches full utilization and generates revenue.\n\n"
        "In **Biorefinery** mode, the swept price is the **PHA selling price**. SCP revenue uses the `SCP market price` assumption.\n\n"
        "**Right panel -- Discounted Cash Flow**:\n"
        "Starts at -Total CapEx in year 0, adds discounted annual cash flow each year: "
        "CF(t) = Cash Flow / (1 + r)^t.\n"
        "The **payback year** is where the cumulative line crosses zero. "
        "Red shading = in the red; green = recovered.\n\n"
        "*Discount rate = 9 % by default (Fairfield site assumption).*"
    ),
    "IRR Analysis": (
        "**Internal Rate of Return (IRR)** is the discount rate that makes the Net Present Value "
        "of the project exactly zero:\n\n"
        "0 = -Total Project CapEx + Sum over t=1..N of (Annual Project Cash Flow / (1 + IRR)^t)\n\n"
        "In plain terms: IRR is the **annual percentage return** the project earns on the initial investment. "
        "A higher IRR is better.\n\n"
        "Total Project CapEx = minor CapEx + Fairfield acquisition + any retrofit.\n"
        "Annual Project Cash Flow = Revenue - cash operating cost, with annualized CapEx added back "
        "to avoid double counting.\n\n"
        "In **Biorefinery** mode, the swept price is the **PHA selling price**; SCP revenue remains tied to the separate `SCP market price` assumption.\n\n"
        "**Left panel**: IRR vs. selling price -- shows how the return improves as you charge more per kg. "
        "Reference lines at 8% (minimum hurdle for many investors), 15% (strong), and 25% (excellent).\n\n"
        "**Right panel**: IRR vs. total CapEx at your chosen selling price -- shows how returns "
        "fall as the upfront investment grows. Helps answer: *how much can I spend on equipment "
        "and still earn a good return?*\n\n"
        "Both panels show one line per capacity tier (best scenario at each scale)."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  REFERENCE TRACE PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def render_reference_trace(model_key: str, results: List[Any], assumption_kwargs: Dict[str, Any], defaults: Any) -> None:
    _section("Scenario References")
    st.caption("Pick a scenario to see its relevant literature, market, and framework sources with direct links, plus exactly what each source contributed to the dashboard.")
    options = {scenario_label(model_key, r): r for r in results}
    selected = options[st.selectbox("Scenario", list(options.keys()), key="ref_scenario")]

    refs = scenario_reference_ids(model_key, selected, assumption_kwargs, defaults)
    notes = scenario_specific_notes(model_key, selected, assumption_kwargs, defaults)

    def _esc(s: str) -> str:
        return s.replace("$", r"\$")

    for note in notes:
        st.markdown(f"- {_esc(note)}")

    for ref_id in refs:
        ref = REFERENCE_LIBRARY[ref_id]
        url = (ref.get("url") or "").strip()
        url_note = (ref.get("url_note") or "").strip()
        used = (ref.get("used") or "").strip()
        if url:
            link_md = f"[{ref['title']}]({url})"
        else:
            link_md = f"**{ref['title']}** *(no public URL)*"
        extra = f" -- *{_esc(url_note)}*" if url_note else ""
        st.markdown(f"- {link_md} `{ref['kind']}`{extra}")
        st.markdown(f"  Used in dashboard: {_esc(ref['why'])}")
        if used:
            st.markdown(f"  Exactly used from this source: {_esc(used)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  GROQ LLM CHAT
# ═══════════════════════════════════════════════════════════════════════════════

# Available free-tier Groq models (fast, good quality)
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
]


def _groq_api_key() -> str:
    """Read key from st.secrets (cloud) or environment variable (local)."""
    import os
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


def _build_system_prompt(model_key: str, assumption_kwargs: Dict[str, Any],
                         defaults: Any, results: List[Any]) -> str:
    model_name = {"scp": "SCP (Single-Cell Protein)", "pha": "PHA (Bioplastic)",
                  "bio": "Biorefinery (SCP + PHA)"}[model_key]

    edited = []
    for k, v in assumption_kwargs.items():
        dv = getattr(defaults, k)
        if changed(v, dv):
            edited.append(f"  {k}: {v} (default was {dv})")
    edits_block = "\n".join(edited) if edited else "  (none -- all at defaults)"

    if model_key == "scp":
        _all_chat_caps = sorted(set(r.capacity_tpy for r in results))
    elif model_key == "pha":
        _all_chat_caps = sorted(set(r.capacity_tpy for r in results))
    else:
        _all_chat_caps = sorted(set(r.capacity_tpy_cdw for r in results))
    _chat_cap = _all_chat_caps[len(_all_chat_caps) // 2] if _all_chat_caps else 1_200.0
    _chat_phase = f"{_chat_cap:,.0f} t/y"
    if model_key == "scp":
        pool = [r for r in results if r.capacity_tpy == _chat_cap]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.msp)
        headline = (
            f"Best SCP MSP at {_chat_phase}: ${best.msp:.3f}/kg via "
            f"{_display_text(best.feed.value)}, {_display_text(best.mode.value)}"
        )
    elif model_key == "pha":
        pool = [r for r in results if r.capacity_tpy == _chat_cap]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.msp)
        headline = (
            f"Best PHA MSP at {_chat_phase}: ${best.msp:.3f}/kg via "
            f"{_display_text(best.feed.value)}, {_display_text(best.mode.value)}, "
            f"{_display_text(best.product.value)}, {_display_text(best.titer_scenario.value)}"
        )
    else:
        pool = [r for r in results if r.capacity_tpy_cdw == _chat_cap]
        if not pool:
            pool = results
        best = min(pool, key=lambda r: r.pha_msp_with_scp_credit)
        headline = (f"Best PHA MSP w/ SCP credit at {_chat_phase}: ${best.pha_msp_with_scp_credit:.3f}/kg "
                    f"via {_display_text(best.feed.value)}, {_display_text(best.mode.value)}, "
                    f"{_display_text(best.polymer.value)}, {_display_text(best.titer_scenario.value)}")

    refs_block = "\n".join(
        f"  - {ref['title']} ({ref['kind']}): {ref['why']}"
        + (f" URL: {ref['url']}" if ref.get("url") else "")
        for ref in REFERENCE_LIBRARY.values()
    )

    return f"""You are a technoeconomic analysis (TEA) assistant for PhycoVax Inc.
The user is viewing the **{model_name}** model dashboard.

KEY RESULT:
{headline}

USER-EDITED ASSUMPTIONS (vs. defaults):
{edits_block}

REFERENCE LIBRARY (cite these when relevant):
{refs_block}

RULES:
- Answer questions about the TEA results, assumptions, and references.
- Explain which assumptions are literature-backed vs. scenario-only.
- When suggesting scenarios, always note which inputs are user-controlled vs. literature-locked.
- Be concise but precise. Use numbers from the model.
- If you don't know something, say so rather than guessing.
- v4 is site-specific for the former AB InBev brewery at 3101 Busch Drive, Fairfield CA. The $45M acquisition cost is fixed (scaling exponent 0.0) regardless of utilization. Three phases: Phase I (20%, ~400 t/y CDW), Phase II (60%, ~1200 t/y), Phase III (90%, ~1800 t/y). DLP feedstock from Hilmar Cheese Co. at $0.11/kg sugar. Electricity at $0.12/kWh. Discount rate 9%. Labor ramps conservatively.
"""


def render_chat(model_key: str, assumption_kwargs: Dict[str, Any],
                defaults: Any, results: List[Any]) -> None:
    _section("Ask the TEA Assistant")

    if _Groq is None:
        st.info("Install the Groq SDK (`pip install groq`) to enable the LLM chat.")
        return

    api_key = _groq_api_key()
    if not api_key:
        st.info(
            "Add your Groq API key to enable the TEA chat assistant.\n\n"
            "**Running locally**: set the environment variable `GROQ_API_KEY=gsk_...` "
            "or create `.streamlit/secrets.toml` with `GROQ_API_KEY = \"gsk_...\"`.\n\n"
            "**On Streamlit Community Cloud**: go to your app's Settings → Secrets and add "
            "`GROQ_API_KEY = \"gsk_...\"`.\n\n"
            "Get a free key at [console.groq.com](https://console.groq.com) — no credit card needed.",
            icon="🔑",
        )
        return

    col_model, col_clear, col_info = st.columns([2, 1, 4])
    with col_model:
        groq_model = st.selectbox("Model", GROQ_MODELS, index=0, key="groq_model")
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear chat", key="clear_chat"):
            st.session_state.chat_messages = []
    with col_info:
        st.caption("Powered by [Groq](https://groq.com) — fast, free-tier LLM inference.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    sys_prompt = _build_system_prompt(model_key, assumption_kwargs, defaults, results)

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(_render_chat_text(msg["content"]))

    if user_input := st.chat_input("Ask about the TEA results, assumptions, or references..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(_render_chat_text(user_input))

        api_messages = [{"role": "system", "content": sys_prompt}]
        api_messages.extend(st.session_state.chat_messages)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                client = _Groq(api_key=api_key)
                stream = client.chat.completions.create(
                    model=groq_model,
                    messages=api_messages,
                    stream=True,
                    max_tokens=1024,
                    temperature=0.3,
                )
                for chunk in stream:
                    token = chunk.choices[0].delta.content or ""
                    full_response += token
                    placeholder.markdown(_render_chat_text(full_response, trailing_cursor=True), unsafe_allow_html=True)
                placeholder.markdown(_render_chat_text(full_response), unsafe_allow_html=True)
            except Exception as exc:
                full_response = f"Groq API error: {exc}"
                placeholder.error(full_response)

        st.session_state.chat_messages.append({"role": "assistant", "content": full_response})


# ═══════════════════════════════════════════════════════════════════════════════
#  FAIRFIELD V5 — DEDICATED SITE MODEL
# ═══════════════════════════════════════════════════════════════════════════════

HOURS_PER_YEAR = 8_760.0
CONTINUOUS_HRT_H = 24.0
UPTIME_FRACTION = 0.85

# ── v8 fed-batch defaults ──────────────────────────────────────────────────
# Anchored to Kim 1994 (glucose fed-batch, 121 g/L, 76 % PHB; Biotechnology
# and Bioengineering 43:892), Ryu 1997 (phosphate-limited fed-batch,
# 281 g/L, 67 % PHB; Biotechnology and Bioengineering 55:28), and Budde 2011
# (engineered R. eutropha fed-batch scale-up; Applied and Environmental
# Microbiology 77:2847). Moderate case selected: operationally achievable
# at a CMO today without requiring stretch OTR.
OPERATING_MODE_DEFAULT = "continuous"  # "continuous" | "fed_batch"

FED_BATCH_CDW_GL_DEFAULT = 150.0        # g/L at end of fed-batch cycle
FED_BATCH_PHB_FRAC_DEFAULT = 0.68       # fraction of CDW as PHB
FED_BATCH_CYCLE_H_DEFAULT = 76.0        # total cycle: CIP + SIP + fill + inoc + growth + N-limit + harvest
FED_BATCH_DUTY_FRAC_DEFAULT = 0.68      # fraction of calendar time the vessel is actively producing
FED_BATCH_OTR_RETROFIT_M_DEFAULT = 0.0  # $M, user-controlled; typical brewery-vessel retrofit lands $4-12M

# ── v9 DSP pathway constants ───────────────────────────────────────────────
# Three literature-anchored downstream processing flowsheets. Each pathway
# redefines the two DSP cost lines the engine already uses
# (pha_extraction_cost_per_kg_sellable and downstream_cost_per_kg_cdw) and
# adds a phase-scaled CapEx adder that goes into total_project_capex.
#
#   - NaOCl: Biopol-era hypochlorite digestion. Widely-cited conservative
#     baseline. Cost anchors: Heinrich et al. 2012, Kourmentza 2017 review,
#     Choi-Lee 1999. Mw-degrading.
#   - NaOH: Hot alkaline lysis (Hahn 1994, Choi-Lee 1997). Lower reagent
#     cost than NaOCl, similar equipment profile, modest CapEx bump for
#     alkali-resistant wetted parts. Also Mw-degrading but less so.
#   - Mechanical+enzymatic: High-pressure homogenization + protease /
#     lipase polishing (Kapritchkoff 2006; Jacquel 2008 review; Danimer
#     commercial disclosures). Preserves Mw. Requires high-density
#     biomass to recover
#     reagent cost, so pairs naturally with v8 fed-batch mode. Higher
#     upfront CapEx (HPH skid + enzymatic reactor).
#
# CapEx adders are quoted for the Phase III 400 kL operating point and are
# scaled linearly with installed vessel volume for Phase I (50 kL) and
# Phase II (150 kL).

DSP_PATHWAY_DEFAULT = "mechanical_enzymatic"  # v9 default; set to "naocl" to reproduce v8 baseline

# Each entry: (label, pha_extraction $/kg sellable PHA, downstream $/kg CDW,
# Phase III CapEx adder $, Mw-impact note for caption, short pathway note)
DSP_PATHWAYS: Dict[str, Dict[str, Any]] = {
    "naocl": {
        "label": "NaOCl hypochlorite (Biopol-era baseline)",
        "pha_extraction_per_kg_sellable": 0.638,
        "downstream_per_kg_cdw": 0.420,
        "phase3_capex": 0.0,
        "mw_note": "Mw-degrading. Expect a 30-60% Mw loss vs fermented polymer; acceptable for film/blown-film grades, marginal for fiber.",
        "pathway_note": "Conservative literature baseline. Reproduces v7/v8 numbers when selected. High-salinity wastewater (~30-60 kg NaCl / t PHA) is a real disposal line that is not separately costed; flag as caveat.",
    },
    "naoh": {
        "label": "NaOH hot alkali (Hahn 1994 / Choi-Lee 1997)",
        "pha_extraction_per_kg_sellable": 0.450,
        "downstream_per_kg_cdw": 0.380,
        "phase3_capex": 0.0,
        "mw_note": "Mw-degrading but less than NaOCl (~20-40% Mw loss). Adequate for film, blister-pack, and rigid-container grades.",
        "pathway_note": "Hot alkaline lysis at 60-80 degC. Lower reagent cost than NaOCl. Incremental equipment (alkali-resistant wetted parts) is not auto-added to the model; if modeling retrofit cost, bump the 'Added major CapEx' slider.",
    },
    "mechanical_enzymatic": {
        "label": "Mechanical + enzymatic (modern CMO standard)",
        "pha_extraction_per_kg_sellable": 0.250,
        "downstream_per_kg_cdw": 0.300,
        "phase3_capex": 0.0,
        "mw_note": "Mw-preserving. Delivered molecular weight is 80-95% of the fermented polymer; suitable for injection molding, fiber, and melt-processable grades.",
        "pathway_note": "High-pressure homogenization (~800-1200 bar) to break cell walls, then protease + lipase polishing to remove non-PHA cell matter. Requires high-density biomass (>=100 g/L) to justify the reagent load; raise the S1/S2 CDW titer sliders into that band for a fair comparison to literature homogenization TEAs. Incremental equipment (HPH skid + polishing reactor) is not auto-added to the model; if modeling retrofit cost, bump the 'Added major CapEx' slider.",
    },
}


def _dsp_pathway_capex(pathway_id: str, vessel_volume_L: float) -> float:
    """Phase-volume-scaled CapEx adder for the selected DSP pathway."""
    phase3_capex = float(DSP_PATHWAYS[pathway_id]["phase3_capex"])
    return phase3_capex * (vessel_volume_L / PHASE_VOLUMES_L["Phase III"])


# ── v9 PHBV co-production constants ────────────────────────────────────────
# NCIMB 11599 (Cupriavidus necator H16) does not make PHBV from glucose or
# fructose alone; HV incorporation requires co-feeding a short-chain organic
# acid precursor. The co-substrate cost is usually the dominant economic
# swing in any PHBV TEA.
#
# Defaults are mass-balance literature values (Doi 1988; Madison-Huisman
# 1999; Tianan Biopolymer disclosures; Yee et al. 2018 review):
#
#   - Propionate:  2.5 kg co-substrate per kg HV incorporated, ~$2.25/kg
#                  bulk propionic acid. 5-15 mol% HV is routinely achievable.
#                  Industry-standard choice.
#   - Valerate:    1.5 kg/kg HV, ~$3.75/kg. Higher mass efficiency, more
#                  expensive reagent. 10-30 mol% HV achievable.
#   - Levulinate:  3.5 kg/kg HV, ~$1.75/kg. Cheaper reagent, lower
#                  incorporation efficiency. Typically 5-12 mol% HV.
#
# Auto-scaled PHBV market price (piecewise-linear, $/kg vs mol% HV):
#   5% -> $5.50, 10% -> $7.00, 15% -> $9.00, 20% -> $12.00
# Anchored to Tianan Biopolymer, Kaneka, and Danimer Nodax product-line
# disclosures and 2023-2025 specialty-bioplastic price surveys.

PHBV_ENABLED_DEFAULT = False

COSUBSTRATE_PRESETS: Dict[str, Dict[str, float]] = {
    "propionate": {
        "label": "Propionate (industry standard)",
        "price_per_kg": 2.25,
        "kg_per_kg_hv": 2.5,
        "default_hv_mol_pct": 10.0,
        "max_hv_mol_pct": 15.0,
    },
    "valerate": {
        "label": "Valerate (high incorporation)",
        "price_per_kg": 3.75,
        "kg_per_kg_hv": 1.5,
        "default_hv_mol_pct": 12.0,
        "max_hv_mol_pct": 25.0,
    },
    "levulinate": {
        "label": "Levulinate (cheapest, lower yield)",
        "price_per_kg": 1.75,
        "kg_per_kg_hv": 3.5,
        "default_hv_mol_pct": 8.0,
        "max_hv_mol_pct": 12.0,
    },
}


def phbv_auto_price(hv_mol_pct: float) -> float:
    """Piecewise-linear PHBV selling price as a function of HV mol%.

    Anchors (mol% HV, $/kg):
        (0,  5.00)  -- extrapolation below 5%, pure PHB floor
        (5,  5.50)
        (10, 7.00)
        (15, 9.00)
        (20, 12.00)
        (>20 extrapolated using the 15-20 slope)
    """
    x = float(hv_mol_pct)
    anchors = [(0.0, 5.00), (5.0, 5.50), (10.0, 7.00), (15.0, 9.00), (20.0, 12.00)]
    if x <= anchors[0][0]:
        return anchors[0][1]
    for (x0, y0), (x1, y1) in zip(anchors[:-1], anchors[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    x0, y0 = anchors[-2]
    x1, y1 = anchors[-1]
    return y1 + (y1 - y0) * (x - x1) / (x1 - x0)

# ═══════════════════════════════════════════════════════════════════════════════
#  v10 — Human-grade SCP (HGP) model
# ═══════════════════════════════════════════════════════════════════════════════
# v10 reintroduces human-grade single-cell protein as a modeled product. When
# the HGP toggle is OFF, the model behaves exactly like v9 (feed-grade SCP +
# PHA/PHBV biorefinery). When HGP is ON, the non-PHA fraction of CDW is sold
# as human-grade whole-cell protein mash instead of feed-grade SCP.
#
# Defaults and anchors:
#   HGP selling price  : $8.00/kg (range $3.00 - $12.00)
#     * Ingredient-grade mycoprotein (Quorn): $6-10/kg per 2024-2025
#       food-ingredient trade surveys (Finnigan 2019 Curr. Dev. Nutr.
#       is the nutritional-profile reference for the category; it does
#       not publish a delivered ingredient selling price).
#     * Solar Foods Solein: single-digit USD/kg dry protein production-
#       cost target at Factory 01 nameplate; no fixed public delivered
#       selling price (Solar Foods 2022-2024 investor and regulatory
#       disclosures). Note: Solein holds Singapore novel-food approval
#       and US self-affirmed GRAS (2024); EFSA novel-food review is
#       in progress.
#     * $8/kg sits mid-band and is consistent with the Ritala 2017
#       (Front. Microbiol.) bacterial-SCP review for GRAS-/novel-food-
#       cleared human food ingredients.
#     * Calysta FeedKind is feed-grade only; no public FeedKind-HP
#       selling price has been disclosed, so FeedKind is NOT used as
#       an HGP-price anchor.
#   HGP DSP cost       : $1.80/kg HGP (range $0.50 - $5.00)
#     Internal bottom-up engineering estimate for a spray-dried whole-
#     cell mash flowsheet, informed by Ritala 2017, Jacquel 2008, and
#     public Quorn / Solein flowsheet disclosures. Decomposition:
#     * Endotoxin / LPS removal via thermal inactivation + TFF (and
#       optional polymyxin-B affinity polish): ~$1.05/kg HGP
#     * Food-grade spray drying + sanitary packaging: ~$0.50/kg HGP
#     * Release QA + regulatory overhead: ~$0.25/kg HGP
#     Treat as a Phase II / III engineering-stage estimate, not a
#     literature-cited scalar.
#   HGP whole-cell recovery : 0.85 of non-PHA CDW (range 0.60 - 0.95)
#     * Quorn / Solein-style spray-dried mash typically recovers 80-90 %.
#   Crude-protein content   : 0.63 (range 0.45 - 0.75)
#     * Ritala 2017 review: bacterial SCP 55-75 % CP on dry basis.
#   HGP-alone residual PHB  : 0.00 (range 0.00 - 0.15)
#     * Default assumes a phaCAB knockout strain. The polymer-negative
#       phenotype of phaC-deletion mutants is established by Slater
#       1988 (J. Bacteriol.) and Peoples & Sinskey 1989 (J. Biol.
#       Chem.); the phaCAB operon is mapped in Pohlmann 2006 (Nat.
#       Biotechnol. genome paper). With the KO default the HGP-alone
#       product slate is ~100% protein-rich biomass and there is no
#       residual polymer to process or sell.
#     * The 0-15% slider range is retained so the user can model the
#       wild-type N-replete case (Braunegg 1998, Khanna 2005: 5-15%
#       basal PHB under growth-phase metabolism) if the KO strain is
#       not yet available, or to represent an incomplete-KO phenotype.
#
# Regulatory caveat: C. necator H16 has a mixed regulatory footprint, not a
# blanket clearance. The organism sits on the EFSA QPS list (production purposes
# only) and its PHA polymer has FDA Food Contact Notifications (e.g. Kaneka
# FCN 1835 on P(3HB-co-3HHx)), but the biomass itself does not hold a US GRAS
# notice or an EFSA Novel Food authorisation as a food ingredient. The closest
# commercial precedent (Solar Foods Solein, produced from a Xanthobacter-group
# organism rather than C. necator) holds Singapore novel-food approval (2022)
# and US self-affirmed GRAS (2024); its EFSA Novel Food dossier is in progress.
# A C. necator-biomass HGP product would require its own US GRAS (or
# self-affirmed GRAS) or EFSA Novel Food clearance, each typically 2-3 years of
# review once the toxicology, allergenicity, and compositional packages are in
# hand. HGP economics are pro-forma pending that clearance.

HGP_ENABLED_DEFAULT = False
HGP_PRODUCTION_MODE_DEFAULT = "coproduction"  # "coproduction" or "alone"
HGP_SELLING_PRICE_DEFAULT = 8.00
HGP_DSP_COST_PER_KG_DEFAULT = 1.80
HGP_RECOVERY_FRAC_DEFAULT = 0.85
HGP_CP_DEFAULT = 0.63
HGP_ALONE_PHB_FRAC_DEFAULT = 0.00  # phaCAB knockout; no residual PHA

PHASE_VOLUMES_L: Dict[str, float] = {
    "Phase I": 50_000.0,
    "Phase II": 150_000.0,
    "Phase III": 400_000.0,
}
PHASE_DEFAULT_UTIL: Dict[str, int] = {
    "Phase I": 90,
    "Phase II": 90,
    "Phase III": 90,
}
PHASE_FIXED_LABOR: Dict[str, float] = {
    "Phase I": 450_000.0,
    "Phase II": 1_100_000.0,
    "Phase III": 2_000_000.0,
}

PHA_STANDARD_PRICE = 5.50
PHBV_PRICE = 7.00
PHA_BLEND_STANDARD_SHARE = 0.70
PHA_BLEND_PHBV_SHARE = 0.30
# v7 default feed-grade SCP selling price. Anchored to three independent
# 2024-2025 commercial benchmarks: fishmeal (FRED PFISHUSDM, $1.45-1.79/kg),
# Calysta FeedKind ($1.50-2.00/kg, Rabobank / Aquafeed outlooks), and Unibio
# UniProtein (~$2.00/kg, company disclosures). The $2.00/kg default is the
# upper end of that band, reflecting the functional premium of bacterial SCP
# over commodity fishmeal (consistent composition, no heavy-metal or POP load,
# no marine-ecosystem pressure, shelf-stable).
SCP_TARGET_PRICE = 2.00
SCP_CREDIT_PRICE = 2.00
DISCOUNT_RATE = 0.09
NPV_YEARS = 10

JB_SUGAR_PRICE = 0.11
JB_PRETREAT_COST = 0.038
DLP_SUGAR_PRICE = 0.125
DLP_PRETREAT_COST = 0.004
ELECTRICITY_PRICE = 0.12

STANDARD_N_COST_PER_KG_CDW = 0.068
ELECTRICITY_KWH_PER_KG_CDW = 1.7678571428571428
STEAM_COST_PER_KG_CDW = 0.160
DOWNSTREAM_COST_PER_KG_CDW = 0.420
CIP_COST_PER_KG_CDW = 0.17714285714285716
PHA_EXTRACTION_COST_PER_KG_SELLABLE = 0.638002278279692


@dataclass
class FairfieldScenario:
    id: str
    title: str
    carbon_mix_label: str
    jb_share: float
    dlp_share: float
    yield_kg_per_kg_sugar: float
    titer_gL: float
    phb_content_frac: float
    scp_protein_frac: float
    n_reduction_frac: float
    carbon_recovery_frac: float
    notes: str
    # v8: fed-batch physiology defaults (used when the global operating-mode
    # toggle is set to "fed_batch" and no slider override is supplied).
    fed_batch_titer_gL: float = FED_BATCH_CDW_GL_DEFAULT
    fed_batch_phb_content_frac: float = FED_BATCH_PHB_FRAC_DEFAULT


@dataclass
class FairfieldResult:
    scenario_id: str
    scenario_title: str
    phase: str
    vessel_volume_L: float
    utilization_pct: float
    active_volume_L: float
    annual_cdw_kg: float
    annual_cdw_tpy: float
    annual_pha_kg: float
    annual_scp_kg: float
    annual_total_product_kg: float
    substrate_cost: float
    pretreatment_cost: float
    nitrogen_cost: float
    electricity_cost: float
    steam_cost: float
    extraction_cost: float
    downstream_cost: float
    cip_cost: float
    labor_cost: float
    annual_major_capex: float
    total_annual_cost: float
    total_revenue: float
    annual_cash_flow: float
    project_capex_purchase: float
    pha_msp_standalone: float
    pha_msp_with_scp_credit: float
    simple_payback_years: float
    npv: float
    irr: float
    yield_kg_per_kg_sugar: float
    titer_gL: float
    phb_content_frac: float
    scp_protein_frac: float
    n_reduction_frac: float
    carbon_recovery_frac: float
    jb_share: float
    dlp_share: float
    operating_mode: str = "continuous"
    cycle_h: float = FED_BATCH_CYCLE_H_DEFAULT
    duty_cycle_frac: float = FED_BATCH_DUTY_FRAC_DEFAULT
    otr_retrofit_capex: float = 0.0
    # v9: DSP pathway + PHBV co-production
    dsp_pathway_id: str = DSP_PATHWAY_DEFAULT
    dsp_pathway_capex: float = 0.0
    phbv_enabled: bool = False
    phbv_cosubstrate_id: str = "propionate"
    phbv_hv_mol_pct: float = 10.0
    phbv_cosubstrate_kg: float = 0.0
    phbv_cosubstrate_cost: float = 0.0
    phbv_selling_price: float = 0.0
    # v10: human-grade SCP (HGP)
    hgp_enabled: bool = False
    hgp_production_mode: str = HGP_PRODUCTION_MODE_DEFAULT
    hgp_selling_price: float = 0.0
    hgp_dsp_cost_per_kg: float = 0.0
    hgp_recovery_frac: float = 0.0
    hgp_cp_frac: float = 0.0
    annual_hgp_kg: float = 0.0
    hgp_dsp_cost: float = 0.0


FAIRFIELD_SCENARIOS: Dict[str, FairfieldScenario] = {
    "S1": FairfieldScenario(
        id="S1",
        title="Scenario 1 — Jelly Belly COD only",
        carbon_mix_label="100% Jelly Belly COD + invertase",
        jb_share=1.0,
        dlp_share=0.0,
        yield_kg_per_kg_sugar=0.50,
        titer_gL=60.0,
        phb_content_frac=0.60,
        scp_protein_frac=0.68,
        n_reduction_frac=0.50,
        carbon_recovery_frac=0.90,
        notes="NCIMB 11599, continuous 24 h HRT, 60 g/L CDW / 60% PHB base case (v7 lock). "
              "S1 is the JB-only feed scenario. Product slate (PHA / SCP tonnage) is "
              "identical to S2 by construction; S1 and S2 differ on the cost-side "
              "biology (S1: 50% N-reduction, 90% C-recovery, 100% JB carbon mix).",
    ),
    "S2": FairfieldScenario(
        id="S2",
        title="Scenario 2 — 70/30 Jelly Belly COD + DLP",
        carbon_mix_label="70% Jelly Belly COD + 30% DLP",
        jb_share=0.70,
        dlp_share=0.30,
        yield_kg_per_kg_sugar=0.496,
        titer_gL=60.0,
        phb_content_frac=0.60,
        scp_protein_frac=0.60,
        n_reduction_frac=0.75,
        carbon_recovery_frac=0.92,
        notes="60 g/L CDW / 60% PHB base case (v7 lock). S2 is the 70/30 JB/DLP "
              "blended-feed scenario. Product slate (PHA / SCP tonnage) is "
              "identical to S1 by construction; S1 and S2 differ on the cost-side "
              "biology (S2: 75% N-reduction, 92% C-recovery, 30% DLP carbon mix "
              "with pH/dilution pretreat only and a 15% galactose uptake penalty "
              "applied to the DLP fraction).",
    ),
}


def _fairfield_crf(rate: float = DISCOUNT_RATE, years: int = NPV_YEARS) -> float:
    if rate <= 0 or years <= 0:
        return 0.0
    return rate * (1 + rate) ** years / ((1 + rate) ** years - 1)


def _annual_operating_cycles(
    mode: str = "continuous",
    cycle_h: float = FED_BATCH_CYCLE_H_DEFAULT,
    duty_cycle_frac: float = FED_BATCH_DUTY_FRAC_DEFAULT,
) -> float:
    """Turnover-equivalents per year.

    Continuous: 8,760 h/yr * uptime / HRT. Each turnover moves one vessel
    volume through the bioreactor at the endpoint steady-state titer.

    Fed-batch: 8,760 h/yr * duty_cycle / cycle_h. Each cycle fills the
    vessel once to the endpoint CDW (no further turnover inside the cycle).
    Duty cycle already bakes in CIP, SIP, fill, inoculation, lag, growth,
    production, and harvest downtime.
    """
    if mode == "fed_batch":
        return HOURS_PER_YEAR * float(duty_cycle_frac) / max(1.0, float(cycle_h))
    return HOURS_PER_YEAR * UPTIME_FRACTION / CONTINUOUS_HRT_H


def _annual_cdw_kg_from_phase(
    vessel_volume_L: float,
    utilization_pct: float,
    titer_gL: float,
    *,
    mode: str = "continuous",
    cycle_h: float = FED_BATCH_CYCLE_H_DEFAULT,
    duty_cycle_frac: float = FED_BATCH_DUTY_FRAC_DEFAULT,
) -> Tuple[float, float]:
    """Annual gross cell-dry-weight production, computed from first principles.

    Both modes use CDW = utilized_volume * titer * annual_turnovers, where the
    definition of "turnover" adapts to the operating mode (see
    ``_annual_operating_cycles``).
    """
    utilized_volume_L = vessel_volume_L * (utilization_pct / 100.0)
    turnovers_per_year = _annual_operating_cycles(mode, cycle_h, duty_cycle_frac)
    annual_cdw_kg = utilized_volume_L * (titer_gL / 1000.0) * turnovers_per_year
    return utilized_volume_L, annual_cdw_kg


def _sellable_pha_kg(annual_cdw_kg: float, phb_content_frac: float) -> float:
    return annual_cdw_kg * phb_content_frac * 0.88 * 0.95


def _sellable_scp_kg(annual_cdw_kg: float, phb_content_frac: float) -> float:
    return annual_cdw_kg * (1.0 - phb_content_frac) * 0.85 * 0.92


def _pha_blended_price() -> float:
    return PHA_STANDARD_PRICE * PHA_BLEND_STANDARD_SHARE + PHBV_PRICE * PHA_BLEND_PHBV_SHARE


def _fairfield_single_result(
    phase: str,
    util_pct: float,
    scenario: FairfieldScenario,
    acquisition_cost: float,
    added_major_capex: float,
    overrides: Dict[str, float] | None = None,
) -> FairfieldResult:
    overrides = overrides or {}
    vessel_volume_L = PHASE_VOLUMES_L[phase]
    operating_mode = str(overrides.get("operating_mode", OPERATING_MODE_DEFAULT))
    cycle_h = float(overrides.get("cycle_h", FED_BATCH_CYCLE_H_DEFAULT))
    duty_cycle_frac = float(overrides.get("duty_cycle_frac", FED_BATCH_DUTY_FRAC_DEFAULT))
    otr_retrofit_capex = float(overrides.get("otr_retrofit_capex", 0.0)) if operating_mode == "fed_batch" else 0.0

    # v9: DSP pathway selector drives the two DSP cost lines (extraction
    # $/kg PHA, downstream $/kg CDW) via the pathway-keyed sliders. The
    # incremental equipment CapEx for NaOH or mechanical+enzymatic
    # flowsheets is NOT auto-added here; users who want to model
    # retrofit cost should bump the 'Added major CapEx' sidebar slider.
    # dsp_pathway_capex is retained as a zero placeholder for schema
    # compatibility with v9 result consumers.
    dsp_pathway_id = str(overrides.get("dsp_pathway_id", DSP_PATHWAY_DEFAULT))
    if dsp_pathway_id not in DSP_PATHWAYS:
        dsp_pathway_id = DSP_PATHWAY_DEFAULT
    dsp_pathway_capex = 0.0

    total_project_capex = float(
        overrides.get(
            "project_capex_purchase",
            acquisition_cost + added_major_capex + otr_retrofit_capex,
        )
    )
    discount_rate = float(overrides.get("discount_rate", DISCOUNT_RATE))
    npv_years = int(round(float(overrides.get("npv_years", NPV_YEARS))))
    annual_major_capex = total_project_capex * _fairfield_crf(discount_rate, npv_years)

    titer_gL = float(overrides.get("titer_gL", scenario.titer_gL))
    phb_content_frac = float(overrides.get("phb_content_frac", scenario.phb_content_frac))
    yield_kg_per_kg_sugar = float(overrides.get("yield_kg_per_kg_sugar", scenario.yield_kg_per_kg_sugar))
    n_reduction_frac = float(overrides.get("n_reduction_frac", scenario.n_reduction_frac))
    scp_protein_frac = float(overrides.get("scp_protein_frac", scenario.scp_protein_frac))
    carbon_recovery_frac = float(overrides.get("carbon_recovery_frac", scenario.carbon_recovery_frac))
    jb_share = float(overrides.get("jb_share", scenario.jb_share))
    dlp_share = float(overrides.get("dlp_share", scenario.dlp_share))

    jb_sugar_price = float(overrides.get("jb_sugar_price", JB_SUGAR_PRICE))
    dlp_sugar_price = float(overrides.get("dlp_sugar_price", DLP_SUGAR_PRICE))
    jb_pretreat_cost = float(overrides.get("jb_pretreat_cost", JB_PRETREAT_COST))
    dlp_pretreat_cost = float(overrides.get("dlp_pretreat_cost", DLP_PRETREAT_COST))
    standard_n_cost_per_kg_cdw = float(overrides.get("standard_n_cost_per_kg_cdw", STANDARD_N_COST_PER_KG_CDW))
    electricity_kwh_per_kg_cdw = float(overrides.get("electricity_kwh_per_kg_cdw", ELECTRICITY_KWH_PER_KG_CDW))
    electricity_price = float(overrides.get("electricity_price", ELECTRICITY_PRICE))
    steam_cost_per_kg_cdw = float(overrides.get("steam_cost_per_kg_cdw", STEAM_COST_PER_KG_CDW))
    downstream_cost_per_kg_cdw = float(overrides.get("downstream_cost_per_kg_cdw", DOWNSTREAM_COST_PER_KG_CDW))
    cip_cost_per_kg_cdw = float(overrides.get("cip_cost_per_kg_cdw", CIP_COST_PER_KG_CDW))
    pha_extraction_cost_per_kg_sellable = float(
        overrides.get("pha_extraction_cost_per_kg_sellable", PHA_EXTRACTION_COST_PER_KG_SELLABLE)
    )
    labor_cost = float(overrides.get("labor_cost", PHASE_FIXED_LABOR[phase]))
    pha_blended_price = float(overrides.get("pha_blended_price", _pha_blended_price()))
    scp_target_price = float(overrides.get("scp_target_price", SCP_TARGET_PRICE))
    scp_credit_price = float(overrides.get("scp_credit_price", SCP_CREDIT_PRICE))

    # v9: PHBV co-production. If enabled, the PHA polymer stream is sold as
    # PHBV at the (auto-scaled or manually overridden) PHBV price, and a
    # co-substrate cost line is added to the variable cost stack. If
    # disabled, behavior matches v8 (blended PHB/PHBV price with no
    # co-substrate line).
    phbv_enabled = bool(overrides.get("phbv_enabled", False))
    phbv_cosubstrate_id = str(overrides.get("phbv_cosubstrate_id", "propionate"))
    if phbv_cosubstrate_id not in COSUBSTRATE_PRESETS:
        phbv_cosubstrate_id = "propionate"
    phbv_hv_mol_pct = float(overrides.get("phbv_hv_mol_pct", COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["default_hv_mol_pct"]))
    phbv_cosubstrate_kg_per_kg_hv = float(
        overrides.get("phbv_cosubstrate_kg_per_kg_hv", COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["kg_per_kg_hv"])
    )
    phbv_cosubstrate_price = float(
        overrides.get("phbv_cosubstrate_price", COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["price_per_kg"])
    )
    phbv_selling_price = float(overrides.get("phbv_selling_price", phbv_auto_price(phbv_hv_mol_pct)))

    # v10: human-grade SCP (HGP). When enabled, the non-PHA fraction of CDW
    # is sold as human-grade whole-cell protein mash at the HGP price
    # instead of feed-grade SCP at the SCP price. HGP carries its own DSP
    # cost line (endotoxin removal + food-grade spray drying + QA). In
    # "alone" sub-mode, the fermenter is operated N-replete and PHB content
    # is forced to a basal level so the product slate is dominated by HGP.
    # In "coproduction" sub-mode (default), PHB/PHBV behavior is unchanged
    # from v9 and HGP simply replaces feed-grade SCP as the non-PHA product.
    hgp_enabled = bool(overrides.get("hgp_enabled", False))
    hgp_production_mode = str(overrides.get("hgp_production_mode", HGP_PRODUCTION_MODE_DEFAULT))
    if hgp_production_mode not in ("coproduction", "alone"):
        hgp_production_mode = HGP_PRODUCTION_MODE_DEFAULT
    hgp_selling_price = float(overrides.get("hgp_selling_price", HGP_SELLING_PRICE_DEFAULT))
    hgp_dsp_cost_per_kg = float(overrides.get("hgp_dsp_cost_per_kg", HGP_DSP_COST_PER_KG_DEFAULT))
    hgp_recovery_frac = float(overrides.get("hgp_recovery_frac", HGP_RECOVERY_FRAC_DEFAULT))
    hgp_cp_frac = float(overrides.get("hgp_cp_frac", HGP_CP_DEFAULT))
    if hgp_enabled and hgp_production_mode == "alone":
        phb_content_frac = float(overrides.get("hgp_alone_phb_frac", HGP_ALONE_PHB_FRAC_DEFAULT))

    active_volume_L, annual_cdw_kg = _annual_cdw_kg_from_phase(
        vessel_volume_L, util_pct, titer_gL,
        mode=operating_mode, cycle_h=cycle_h, duty_cycle_frac=duty_cycle_frac,
    )
    annual_pha_kg = _sellable_pha_kg(annual_cdw_kg, phb_content_frac)
    if hgp_enabled:
        annual_scp_kg = 0.0
        annual_hgp_kg = annual_cdw_kg * (1.0 - phb_content_frac) * hgp_recovery_frac
    else:
        annual_scp_kg = _sellable_scp_kg(annual_cdw_kg, phb_content_frac)
        annual_hgp_kg = 0.0
    annual_total_product_kg = annual_pha_kg + annual_scp_kg + annual_hgp_kg

    # mol% HV → mass% HV using 3HB (86.09 g/mol) and 3HV (100.12 g/mol)
    # monomer repeat-unit masses, then mass of co-substrate required.
    if phbv_enabled:
        x_hv = max(0.0, min(0.99, phbv_hv_mol_pct / 100.0))
        hv_mass_frac = (100.12 * x_hv) / max(1e-9, 86.09 * (1.0 - x_hv) + 100.12 * x_hv)
        annual_hv_kg = annual_pha_kg * hv_mass_frac
        phbv_cosubstrate_kg = annual_hv_kg * phbv_cosubstrate_kg_per_kg_hv
        phbv_cosubstrate_cost = phbv_cosubstrate_kg * phbv_cosubstrate_price
    else:
        phbv_cosubstrate_kg = 0.0
        phbv_cosubstrate_cost = 0.0

    sugar_required_kg = annual_cdw_kg / max(1e-9, yield_kg_per_kg_sugar * carbon_recovery_frac)
    substrate_cost = sugar_required_kg * (jb_share * jb_sugar_price + dlp_share * dlp_sugar_price)
    pretreatment_cost = sugar_required_kg * (jb_share * jb_pretreat_cost + dlp_share * dlp_pretreat_cost)
    nitrogen_cost = annual_cdw_kg * standard_n_cost_per_kg_cdw * (1.0 - n_reduction_frac)
    electricity_cost = annual_cdw_kg * electricity_kwh_per_kg_cdw * electricity_price
    steam_cost = annual_cdw_kg * steam_cost_per_kg_cdw
    extraction_cost = annual_pha_kg * pha_extraction_cost_per_kg_sellable
    downstream_cost = annual_cdw_kg * downstream_cost_per_kg_cdw
    cip_cost = annual_cdw_kg * cip_cost_per_kg_cdw

    # v10: HGP DSP cost (endotoxin removal + food-grade spray drying + QA).
    # Only added when HGP is enabled; feed-grade SCP has no separate DSP
    # line beyond the CDW-wide downstream_cost already accounted for.
    hgp_dsp_cost = annual_hgp_kg * hgp_dsp_cost_per_kg if hgp_enabled else 0.0

    total_annual_cost = (
        substrate_cost + pretreatment_cost + nitrogen_cost + electricity_cost
        + steam_cost + extraction_cost + downstream_cost + cip_cost
        + labor_cost + annual_major_capex + phbv_cosubstrate_cost
        + hgp_dsp_cost
    )
    pha_revenue_price = phbv_selling_price if phbv_enabled else pha_blended_price
    # v10: non-PHA revenue stream is HGP (at hgp_selling_price) if enabled,
    # otherwise feed-grade SCP (at scp_target_price).
    non_pha_revenue = (
        annual_hgp_kg * hgp_selling_price if hgp_enabled
        else annual_scp_kg * scp_target_price
    )
    total_revenue = annual_pha_kg * pha_revenue_price + non_pha_revenue
    annual_cash_flow = total_revenue - (total_annual_cost - annual_major_capex)
    # v10 fix: in the HGP-alone / phaCAB-knockout configuration the project
    # does not produce polymer, so PHA minimum-selling-price numbers are not
    # physically meaningful (they are dominated by the 1/annual_pha_kg
    # divide-by-near-zero and produce large negative values when an HGP
    # credit is subtracted). Flag these as NaN so downstream display code
    # can render "N/A" instead of a misleading dollar figure.
    _pha_is_suppressed = (
        hgp_enabled and hgp_production_mode == "alone" and phb_content_frac <= 0.005
    )
    if _pha_is_suppressed or annual_pha_kg <= 1.0:
        pha_msp_standalone = float("nan")
        pha_msp_with_scp_credit = float("nan")
    else:
        pha_msp_standalone = total_annual_cost / annual_pha_kg
        non_pha_credit = (
            annual_hgp_kg * hgp_selling_price if hgp_enabled
            else annual_scp_kg * scp_credit_price
        )
        pha_msp_with_scp_credit = (total_annual_cost - non_pha_credit) / annual_pha_kg
    npv = -total_project_capex + sum(annual_cash_flow / (1 + discount_rate) ** t for t in range(1, npv_years + 1))
    irr = _compute_irr(total_project_capex, annual_cash_flow, npv_years)
    payback = total_project_capex / annual_cash_flow if annual_cash_flow > 0 else float("nan")

    return FairfieldResult(
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        phase=phase,
        vessel_volume_L=vessel_volume_L,
        utilization_pct=util_pct,
        active_volume_L=active_volume_L,
        annual_cdw_kg=annual_cdw_kg,
        annual_cdw_tpy=annual_cdw_kg / 1000.0,
        annual_pha_kg=annual_pha_kg,
        annual_scp_kg=annual_scp_kg,
        annual_total_product_kg=annual_total_product_kg,
        substrate_cost=substrate_cost,
        pretreatment_cost=pretreatment_cost,
        nitrogen_cost=nitrogen_cost,
        electricity_cost=electricity_cost,
        steam_cost=steam_cost,
        extraction_cost=extraction_cost,
        downstream_cost=downstream_cost,
        cip_cost=cip_cost,
        labor_cost=labor_cost,
        annual_major_capex=annual_major_capex,
        total_annual_cost=total_annual_cost,
        total_revenue=total_revenue,
        annual_cash_flow=annual_cash_flow,
        project_capex_purchase=total_project_capex,
        pha_msp_standalone=pha_msp_standalone,
        pha_msp_with_scp_credit=pha_msp_with_scp_credit,
        simple_payback_years=payback,
        npv=npv,
        irr=irr,
        yield_kg_per_kg_sugar=yield_kg_per_kg_sugar,
        titer_gL=titer_gL,
        phb_content_frac=phb_content_frac,
        scp_protein_frac=scp_protein_frac,
        n_reduction_frac=n_reduction_frac,
        carbon_recovery_frac=carbon_recovery_frac,
        jb_share=jb_share,
        dlp_share=dlp_share,
        operating_mode=operating_mode,
        cycle_h=cycle_h,
        duty_cycle_frac=duty_cycle_frac,
        otr_retrofit_capex=otr_retrofit_capex,
        dsp_pathway_id=dsp_pathway_id,
        dsp_pathway_capex=dsp_pathway_capex,
        phbv_enabled=phbv_enabled,
        phbv_cosubstrate_id=phbv_cosubstrate_id,
        phbv_hv_mol_pct=phbv_hv_mol_pct,
        phbv_cosubstrate_kg=phbv_cosubstrate_kg,
        phbv_cosubstrate_cost=phbv_cosubstrate_cost,
        phbv_selling_price=phbv_selling_price,
        hgp_enabled=hgp_enabled,
        hgp_production_mode=hgp_production_mode,
        hgp_selling_price=hgp_selling_price,
        hgp_dsp_cost_per_kg=hgp_dsp_cost_per_kg,
        hgp_recovery_frac=hgp_recovery_frac,
        hgp_cp_frac=hgp_cp_frac,
        annual_hgp_kg=annual_hgp_kg,
        hgp_dsp_cost=hgp_dsp_cost,
    )


def _fairfield_results(
    phase_utils: Dict[str, float],
    acquisition_cost: float,
    added_major_capex: float,
) -> List[FairfieldResult]:
    out: List[FairfieldResult] = []
    for phase, vessel_volume_L in PHASE_VOLUMES_L.items():
        util_pct = float(phase_utils[phase])
        for scenario in FAIRFIELD_SCENARIOS.values():
            out.append(_fairfield_single_result(phase, util_pct, scenario, acquisition_cost, added_major_capex))
    return out


def _fairfield_result(results: List[FairfieldResult], phase: str, scenario_id: str) -> FairfieldResult:
    for r in results:
        if r.phase == phase and r.scenario_id == scenario_id:
            return r
    raise KeyError(f"Missing result for {phase}/{scenario_id}")


def _fairfield_rows(results: List[FairfieldResult]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in results:
        rows.append({
            "Scenario": r.scenario_id,
            "Phase": r.phase,
            "Installed volume (L)": int(r.vessel_volume_L),
            "Utilization (%)": round(r.utilization_pct, 1),
            "Utilized volume (L)": round(r.active_volume_L, 0),
            "CDW (t/y)": round(r.annual_cdw_tpy, 1),
            "PHA sellable (t/y)": round(r.annual_pha_kg / 1000.0, 1),
            "SCP sellable (t/y)": round(r.annual_scp_kg / 1000.0, 1),
            "PHA MSP w/ SCP credit ($/kg)": round(r.pha_msp_with_scp_credit, 3),
            "PHA MSP standalone ($/kg)": round(r.pha_msp_standalone, 3),
            "Revenue (M$/yr)": round(r.total_revenue / 1e6, 3),
            "Cost (M$/yr)": round(r.total_annual_cost / 1e6, 3),
            "Cash flow (M$/yr)": round(r.annual_cash_flow / 1e6, 3),
            "NPV (M$)": round(r.npv / 1e6, 3),
            "IRR (%)": round(r.irr * 100, 2) if np.isfinite(r.irr) else np.nan,
            "Payback (yr)": round(r.simple_payback_years, 2) if np.isfinite(r.simple_payback_years) else np.nan,
        })
    return rows


def _fairfield_guardrail_warnings(
    phase_utils: Dict[str, float],
    s1_inputs: Dict[str, float],
    s2_inputs: Dict[str, float],
    process_inputs: Dict[str, float],
    market_inputs: Dict[str, float],
    operating_mode: str = "continuous",
    hgp_alone: bool = False,
) -> List[str]:
    warnings: List[str] = []

    def _check(label: str, value: float, lo: float, hi: float, note: str = "") -> None:
        if value < lo or value > hi:
            msg = f"`{label}` = {value:g} is outside the recommended Fairfield/literature band {lo:g} -- {hi:g}."
            if note:
                msg += f" {note}"
            warnings.append(msg)

    for phase, util in phase_utils.items():
        _check(f"{phase} utilization (%)", util, 20.0, 95.0, "Very low utilization is a ramp case; 100% continuous use is usually too optimistic.")

    titer_lo, titer_hi = 35.0, 85.0
    phb_lo, phb_hi = 30.0, 72.0
    titer_note_s1 = "S1 base case is locked at 60 g/L; 35 g/L reproduces the v5/v6 conservative Year 1 case and >85 g/L should be treated as a stretch assumption."
    titer_note_s2 = "S2 base case is locked at 60 g/L; values above ~85 g/L move into aggressive high-cell-density territory."
    titer_stretch_threshold = 85.0

    _check("S1 CDW titer (g/L)", s1_inputs.get("titer_gL", 0.0), titer_lo, titer_hi, titer_note_s1)
    _check("S2 CDW titer (g/L)", s2_inputs.get("titer_gL", 0.0), titer_lo, titer_hi, titer_note_s2)
    _check("S1 biomass yield (kg/kg sugar)", s1_inputs["yield_kg_per_kg_sugar"], 0.40, 0.55)
    _check("S2 biomass yield (kg/kg sugar)", s2_inputs["yield_kg_per_kg_sugar"], 0.42, 0.55)
    if hgp_alone:
        _check("S1 PHB content (% CDW, HGP-alone)", s1_inputs.get("phb_content_frac", 0.0) * 100.0, 0.0, 15.0,
               "HGP-alone default assumes a phaCAB knockout strain (0% PHA; polymer-negative phenotype per Slater 1988 and Peoples & Sinskey 1989; phaCAB operon mapped in Pohlmann 2006). "
               "Values up to 15% reflect the wild-type N-replete upper bound (Braunegg 1998).")
        _check("S2 PHB content (% CDW, HGP-alone)", s2_inputs.get("phb_content_frac", 0.0) * 100.0, 0.0, 15.0,
               "HGP-alone default assumes a phaCAB knockout strain (0% PHA; polymer-negative phenotype per Slater 1988 and Peoples & Sinskey 1989; phaCAB operon mapped in Pohlmann 2006). "
               "Values up to 15% reflect the wild-type N-replete upper bound (Braunegg 1998).")
    else:
        _check("S1 PHB content (% CDW)", s1_inputs.get("phb_content_frac", 0.0) * 100.0, phb_lo, phb_hi)
        _check("S2 PHB content (% CDW)", s2_inputs.get("phb_content_frac", 0.0) * 100.0, phb_lo, phb_hi)
    _check("S1 nitrogen reduction (%)", s1_inputs["n_reduction_frac"] * 100.0, 40.0, 60.0)
    _check("S2 nitrogen reduction (%)", s2_inputs["n_reduction_frac"] * 100.0, 65.0, 85.0)
    _check("S1 carbon recovery (%)", s1_inputs["carbon_recovery_frac"] * 100.0, 85.0, 95.0)
    _check("S2 carbon recovery (%)", s2_inputs["carbon_recovery_frac"] * 100.0, 85.0, 97.0)

    _check("Electricity price ($/kWh)", process_inputs["electricity_price"], 0.10, 0.15, "The Fairfield handoff anchored this near $0.12/kWh.")
    _check("Electricity intensity (kWh/kg CDW)", process_inputs["electricity_kwh_per_kg_cdw"], 1.2, 2.0, "This was the handoff estimate for heterotrophic aeration-and-mixing load.")
    _check("Jelly Belly sugar cost ($/kg sugar)", process_inputs["jb_sugar_price"], 0.09, 0.13)
    _check("DLP sugar cost ($/kg sugar)", process_inputs["dlp_sugar_price"], 0.12, 0.13)
    _check("Jelly Belly pretreatment ($/kg sugar)", process_inputs["jb_pretreat_cost"], 0.03, 0.05)
    _check("DLP pretreatment ($/kg sugar)", process_inputs["dlp_pretreat_cost"], 0.0, 0.03)

    _check("Discount rate (%)", market_inputs["discount_rate"] * 100.0, 7.0, 12.0, "The Fairfield handoff requested 9% as the base case.")

    s1_titer = s1_inputs.get("titer_gL", 0.0)
    s2_titer = s2_inputs.get("titer_gL", 0.0)
    if s1_titer > titer_stretch_threshold or s2_titer > titer_stretch_threshold:
        warnings.append(
            "Titer above 85 g/L is allowed for exploration, but should be treated as speculative "
            "unless you have process-specific supporting data."
        )
    if market_inputs["npv_years"] > 15:
        warnings.append("NPV / IRR horizon above 15 years is beyond the original Fairfield 10-year framing and should be treated as a financing sensitivity, not the base case.")

    return warnings


def _build_v5_system_prompt(
    results: List[FairfieldResult],
    focus_phase: str,
    focus_scenario_id: str,
    sidebar_snapshot: Dict[str, Any],
) -> str:
    focus = _fairfield_result(results, focus_phase, focus_scenario_id)
    rows = _fairfield_rows(results)
    preview_rows = rows[:6]
    return f"""You are a technoeconomic analysis assistant for the Leatherback Fairfield TEA dashboard.

The dashboard is Fairfield-only and models:
- Scenario 1: Jelly Belly COD only
- Scenario 2: 70/30 Jelly Belly COD + DLP
- Continuous 24 h HRT
- 85% uptime
- Phase I / II / III volumes of 50,000 L / 150,000 L / 400,000 L

Current focus:
- Phase: {focus_phase}
- Scenario: {focus_scenario_id}
- CDW: {focus.annual_cdw_tpy:,.1f} t/y
- PHA MSP with SCP credit: ${focus.pha_msp_with_scp_credit:,.3f}/kg
- Revenue: ${focus.total_revenue/1e6:,.3f}M/yr
- Cash flow: ${focus.annual_cash_flow/1e6:,.3f}M/yr
- NPV: ${focus.npv/1e6:,.3f}M
- IRR: {focus.irr*100:,.2f}%

Current sidebar values:
{sidebar_snapshot}

Results preview:
{preview_rows}

Capital / CapEx model (IMPORTANT — use this when discussing CapEx):
- The acquisition cost and added major CapEx are modeled as UPFRONT investments, NOT as operating costs.
- They are annualized via a Capital Recovery Factor (CRF) and included in MSP and total annual cost.
- Adding more CapEx raises the annualized capital charge, which raises MSP and reduces NPV.
- NPV = -total_project_capex + sum of annual_cash_flow / (1+discount_rate)^t over npv_years.
- Cash flow = revenue - cash operating costs (cash operating costs exclude the annualized CapEx).
- Adding CapEx INCREASES project_capex_purchase (the negative Year 0 term), which REDUCES NPV.
- Do NOT model CapEx as reducing initial investment costs or as a subsidy — it is an additional cost.

Rules:
- Be concise and numeric.
- Write in plain prose. Do NOT use backtick code spans, LaTeX, or dollar-sign math notation.
- Use plain text like "2.42M/yr" rather than formatted code or math expressions.
- Explain calculations in plain English when asked.
- If discussing assumptions, distinguish user-edited sliders from fixed Fairfield handoff assumptions.
- Scenario 3 is narrative only and not modeled.
- If the IRR shows as nan, it means the project CapEx is zero (default), so IRR is undefined.
"""


def render_v5_chat(
    results: List[FairfieldResult],
    focus_phase: str,
    focus_scenario_id: str,
    sidebar_snapshot: Dict[str, Any],
) -> None:
    _section("Ask the Fairfield TEA Assistant")

    if _Groq is None:
        st.info("Install the Groq SDK (`pip install groq`) to enable the LLM chat.")
        return

    api_key = _groq_api_key()
    if not api_key:
        st.info(
            "Add your Groq API key to enable the Fairfield TEA chat assistant.\n\n"
            "**Running locally**: set `GROQ_API_KEY=gsk_...` or add it to `.streamlit/secrets.toml`.\n\n"
            "**On Streamlit Community Cloud**: add `GROQ_API_KEY = \"gsk_...\"` in app secrets.",
            icon="🔑",
        )
        return

    col_model, col_clear, col_info = st.columns([2, 1, 4])
    with col_model:
        groq_model = st.selectbox("Model", GROQ_MODELS, index=0, key="v5_groq_model")
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear chat", key="v5_clear_chat"):
            st.session_state.v5_chat_messages = []
    with col_info:
        st.caption("Powered by [Groq](https://groq.com) and grounded in the current Fairfield v5 scenario.")

    if "v5_chat_messages" not in st.session_state:
        st.session_state.v5_chat_messages = []

    sys_prompt = _build_v5_system_prompt(results, focus_phase, focus_scenario_id, sidebar_snapshot)

    for msg in st.session_state.v5_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(_render_chat_text(msg["content"]))

    if user_input := st.chat_input("Ask about Fairfield assumptions, outputs, or figure meaning...", key="v5_chat_input"):
        st.session_state.v5_chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(_render_chat_text(user_input))

        api_messages = [{"role": "system", "content": sys_prompt}]
        api_messages.extend(st.session_state.v5_chat_messages)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                client = _Groq(api_key=api_key)
                stream = client.chat.completions.create(
                    model=groq_model,
                    messages=api_messages,
                    stream=True,
                    max_tokens=1024,
                    temperature=0.3,
                )
                for chunk in stream:
                    token = chunk.choices[0].delta.content or ""
                    full_response += token
                    placeholder.markdown(_render_chat_text(full_response, trailing_cursor=True), unsafe_allow_html=True)
                placeholder.markdown(_render_chat_text(full_response), unsafe_allow_html=True)
            except Exception as exc:
                full_response = f"Groq API error: {exc}"
                placeholder.error(full_response)

        st.session_state.v5_chat_messages.append({"role": "assistant", "content": full_response})


def fig_v5_outputs(results: List[FairfieldResult]) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), constrained_layout=True)
    phases = list(PHASE_VOLUMES_L.keys())
    x = np.arange(len(phases))
    w = 0.34

    for ax, scenario_id, title in zip(axes, ["S1", "S2"], ["Scenario 1", "Scenario 2"]):
        pha = np.array([_fairfield_result(results, phase, scenario_id).annual_pha_kg / 1000.0 for phase in phases])
        scp = np.array([_fairfield_result(results, phase, scenario_id).annual_scp_kg / 1000.0 for phase in phases])
        ax.bar(x, pha, width=0.58, color="#0ea5e9", label="PHA", edgecolor="white", linewidth=0.8)
        ax.bar(x, scp, width=0.58, bottom=pha, color="#22c55e", label="SCP", edgecolor="white", linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.set_ylabel("Sellable output (t/y)")
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=9)
    fig.suptitle("Fairfield annual sellable product output by phase and scenario", y=1.02, fontsize=14, fontweight="bold")
    return fig


def fig_v5_msp_and_cash(results: List[FairfieldResult]) -> plt.Figure:
    phases = list(PHASE_VOLUMES_L.keys())
    x = np.arange(len(phases))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.2), constrained_layout=True)

    for scenario_id, color in [("S1", "#0ea5e9"), ("S2", "#8b5cf6")]:
        msps = [_fairfield_result(results, phase, scenario_id).pha_msp_with_scp_credit for phase in phases]
        cash = [_fairfield_result(results, phase, scenario_id).annual_cash_flow / 1e6 for phase in phases]
        ax1.plot(x, msps, marker="o", linewidth=2.4, color=color, label=scenario_id)
        ax2.plot(x, cash, marker="o", linewidth=2.4, color=color, label=scenario_id)

    for ax in [ax1, ax2]:
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)
    ax1.set_title("PHA MSP with SCP credit")
    ax1.set_ylabel("MSP ($/kg)")
    ax2.set_title("Annual project cash flow")
    ax2.set_ylabel("Cash flow (M$/yr)")
    return fig


def fig_v5_returns(results: List[FairfieldResult]) -> plt.Figure:
    phases = list(PHASE_VOLUMES_L.keys())
    x = np.arange(len(phases))
    fig, axes = plt.subplots(1, 3, figsize=(17.0, 6.2), constrained_layout=True)

    for scenario_id, color in [("S1", "#0ea5e9"), ("S2", "#8b5cf6")]:
        npvs = [_fairfield_result(results, phase, scenario_id).npv / 1e6 for phase in phases]
        irrs = [_fairfield_result(results, phase, scenario_id).irr * 100 for phase in phases]
        pays = [_fairfield_result(results, phase, scenario_id).simple_payback_years for phase in phases]
        axes[0].plot(x, npvs, marker="o", linewidth=2.4, color=color, label=scenario_id)
        axes[1].plot(x, irrs, marker="o", linewidth=2.4, color=color, label=scenario_id)
        axes[2].plot(x, pays, marker="o", linewidth=2.4, color=color, label=scenario_id)

    titles = ["NPV by phase", "IRR by phase", "Simple payback by phase"]
    ylabels = ["NPV (M$)", "IRR (%)", "Payback (yr)"]
    for ax, title, ylabel in zip(axes, titles, ylabels):
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)
    axes[0].axhline(0, color="#334155", lw=1.0)
    axes[1].axhline(8, color="#f59e0b", ls="--", lw=1.0, alpha=0.7)
    axes[2].axhline(5, color="#22c55e", ls="--", lw=1.0, alpha=0.7)
    return fig


def fig_v9_s1_s2_across_phases(
    results: List[FairfieldResult],
    scp_target_price: float,
    discount_rate: float,
    npv_years: int,
    operating_mode: str = "continuous",
    dsp_pathway_label: str = "",
    phbv_enabled: bool = False,
    phbv_hv_mol_pct: float = 10.0,
) -> plt.Figure:
    """Investor-memo-style 3-panel grouped bar chart: S1 vs S2 across phases.

    Panels: annual revenue, annual cash flow, 10-year NPV at the active
    discount rate. Matches the style used in the v7 investor memo.
    """
    phases = list(PHASE_VOLUMES_L.keys())
    x = np.arange(len(phases))
    bar_w = 0.36
    s1_color = "#3b82f6"
    s2_color = "#a855f7"

    fig, axes = plt.subplots(1, 3, figsize=(16.0, 5.6), constrained_layout=True)

    revenue_by = {sid: np.array([_fairfield_result(results, p, sid).total_revenue / 1e6 for p in phases]) for sid in ("S1", "S2")}
    cash_by = {sid: np.array([_fairfield_result(results, p, sid).annual_cash_flow / 1e6 for p in phases]) for sid in ("S1", "S2")}
    npv_by = {sid: np.array([_fairfield_result(results, p, sid).npv / 1e6 for p in phases]) for sid in ("S1", "S2")}

    def _label_bars(ax, xs, ys, color):
        y_max = max(max(ys), 0.0)
        for xi, yi in zip(xs, ys):
            va = "bottom" if yi >= 0 else "top"
            ax.text(xi, yi + (0.02 * (y_max if y_max else 1.0)) * (1 if yi >= 0 else -1),
                    f"${yi:.1f}M", ha="center", va=va, fontsize=9, color=color)

    panels = [
        (axes[0], revenue_by, "Annual revenue (M$/yr)", "Annual revenue ($M/yr)"),
        (axes[1], cash_by, "Annual cash flow (M$/yr)", "Annual cash flow ($M/yr)"),
        (axes[2], npv_by, f"{npv_years}-year NPV at {discount_rate*100:.0f}% (M$)", f"{npv_years}-year NPV at {discount_rate*100:.0f}% ($M)"),
    ]
    for ax, data_by, ylabel, panel_title in panels:
        s1_vals = data_by["S1"]
        s2_vals = data_by["S2"]
        ax.bar(x - bar_w/2, s1_vals, width=bar_w, color=s1_color, label="S1", edgecolor="white", linewidth=0.6)
        ax.bar(x + bar_w/2, s2_vals, width=bar_w, color=s2_color, label="S2", edgecolor="white", linewidth=0.6)
        _label_bars(ax, x - bar_w/2, s1_vals, s1_color)
        _label_bars(ax, x + bar_w/2, s2_vals, s2_color)
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.set_ylabel(ylabel)
        ax.set_title(panel_title)
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="upper left", fontsize=9, frameon=False)
        if min(s1_vals.min(), s2_vals.min()) < 0:
            ax.axhline(0, color="#334155", lw=0.8)
        else:
            y_max_all = max(s1_vals.max(), s2_vals.max())
            ax.set_ylim(0, y_max_all * 1.18)

    mode_tag = "continuous fermentation (sidebar titer / PHB)"
    prod_tag = f"PHBV @ {phbv_hv_mol_pct:.0f}% HV" if phbv_enabled else "PHB base case"
    dsp_tag = f"DSP: {dsp_pathway_label}" if dsp_pathway_label else ""
    subtitle_bits = [f"S1 vs S2 across phases ({mode_tag}, ${scp_target_price:.2f}/kg SCP, {prod_tag})"]
    if dsp_tag:
        subtitle_bits.append(dsp_tag)
    fig.suptitle(" | ".join(subtitle_bits), y=1.02, fontsize=13, fontweight="bold")
    return fig


def fig_v5_npv_vs_price(
    results: List[FairfieldResult],
    phase: str,
    scp_target_price: float,
    pha_price_marker: float,
    discount_rate: float,
    npv_years: int,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13.5, 6.5), constrained_layout=True)
    prices = np.linspace(1.0, 10.0, 250)
    for scenario_id, color in [("S1", "#0ea5e9"), ("S2", "#8b5cf6")]:
        r = _fairfield_result(results, phase, scenario_id)
        npvs = []
        for p in prices:
            revenue = r.annual_pha_kg * p + r.annual_scp_kg * scp_target_price
            annual_cash = revenue - (r.total_annual_cost - r.annual_major_capex)
            npv = -r.project_capex_purchase + sum(
                annual_cash / (1 + discount_rate) ** t for t in range(1, npv_years + 1)
            )
            npvs.append(npv / 1e6)
        ax.plot(prices, npvs, color=color, linewidth=2.4, label=scenario_id)
    ax.axhline(0, color="#334155", lw=1.0)
    ax.axvline(pha_price_marker, color="#f97316", ls="--", lw=1.0, label="Current PHA blend price")
    ax.set_xlabel("PHA selling price used in NPV sweep ($/kg)")
    ax.set_ylabel("Project NPV (M$)")
    ax.set_title(f"Fairfield NPV vs PHA selling price — {phase}")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    return fig


def fig_v5_irr_vs_price(
    results: List[FairfieldResult],
    phase: str,
    scp_target_price: float,
    pha_price_marker: float,
    npv_years: int,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13.5, 6.5), constrained_layout=True)
    prices = np.linspace(1.0, 10.0, 250)
    plotted_any = False
    for scenario_id, color in [("S1", "#0ea5e9"), ("S2", "#8b5cf6")]:
        r = _fairfield_result(results, phase, scenario_id)
        irrs = []
        for p in prices:
            revenue = r.annual_pha_kg * p + r.annual_scp_kg * scp_target_price
            annual_cash = revenue - (r.total_annual_cost - r.annual_major_capex)
            irrs.append(_compute_irr(r.project_capex_purchase, annual_cash, npv_years) * 100)
        finite = np.isfinite(irrs)
        if np.any(finite):
            plotted_any = True
            ax.plot(prices, np.array(irrs, dtype=float), color=color, linewidth=2.4, label=scenario_id)
    ax.axvline(pha_price_marker, color="#f97316", ls="--", lw=1.0, label="Current PHA blend price")
    ax.axhline(8, color="#f59e0b", ls="--", lw=1.0, alpha=0.7)
    ax.axhline(15, color="#22c55e", ls="--", lw=1.0, alpha=0.7)
    ax.set_xlabel("PHA selling price used in IRR sweep ($/kg)")
    ax.set_ylabel("IRR (%)")
    ax.set_ylim(-10, 80)
    ax.set_title(f"Fairfield IRR vs PHA selling price — {phase}")
    ax.grid(alpha=0.25)
    if plotted_any:
        ax.legend(fontsize=9)
    else:
        ax.text(
            0.5, 0.5,
            "IRR is undefined for the current settings because upfront project CapEx is zero.\n\n"
            "Increase `Acquisition cost` or `Added major CapEx` above $0M to generate an IRR curve.",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#cbd5e1", alpha=0.95),
        )
    return fig


def fig_v5_cost_structure(results: List[FairfieldResult], phase: str, scenario_id: str) -> plt.Figure:
    r = _fairfield_result(results, phase, scenario_id)
    comps = [
        ("Feedstock", r.substrate_cost / 1e6),
        ("Pretreatment", r.pretreatment_cost / 1e6),
        ("Nitrogen", r.nitrogen_cost / 1e6),
        ("Electricity", r.electricity_cost / 1e6),
        ("Steam / thermal", r.steam_cost / 1e6),
        ("PHA extraction", r.extraction_cost / 1e6),
        ("Downstream", r.downstream_cost / 1e6),
        ("CIP / maintenance", r.cip_cost / 1e6),
        ("Labor", r.labor_cost / 1e6),
        ("Annualized CapEx", r.annual_major_capex / 1e6),
    ]
    labels = [name for name, _ in comps]
    vals = [value for _, value in comps]
    fig, ax = plt.subplots(figsize=(13.5, 6.8), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, vals, color="#38bdf8", edgecolor="white", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Annual cost contribution (M$/yr)")
    ax.set_title(f"Fairfield annual cost structure — {scenario_id}, {phase}")
    ax.grid(axis="x", alpha=0.25)
    for i, val in enumerate(vals):
        ax.text(val + max(0.01, val * 0.02), i, f"{val:,.2f}", va="center", fontsize=9)
    return fig


def fig_v5_discounted_cf(
    results: List[FairfieldResult],
    phase: str,
    scenario_id: str,
    discount_rate: float,
    npv_years: int,
) -> plt.Figure:
    r = _fairfield_result(results, phase, scenario_id)
    years = np.arange(0, npv_years + 1)
    cumulative = np.zeros(len(years))
    cumulative[0] = -r.project_capex_purchase
    for t in range(1, len(years)):
        cumulative[t] = cumulative[t - 1] + r.annual_cash_flow / (1 + discount_rate) ** t
    fig, ax = plt.subplots(figsize=(13.5, 6.5), constrained_layout=True)
    ax.plot(years, cumulative / 1e6, color="#0ea5e9", linewidth=2.4)
    ax.fill_between(years, cumulative / 1e6, 0, where=(cumulative < 0), color="#ef4444", alpha=0.10)
    ax.fill_between(years, cumulative / 1e6, 0, where=(cumulative >= 0), color="#22c55e", alpha=0.10)
    ax.axhline(0, color="#334155", lw=1.0)
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative discounted cash flow (M$)")
    ax.set_title(f"Fairfield discounted cash flow — {scenario_id}, {phase}")
    ax.grid(alpha=0.25)
    return fig


def fig_v5_feedstock_sensitivity(results: List[FairfieldResult], phase: str, scp_credit_price: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13.5, 6.5), constrained_layout=True)
    factors = np.array([0.8, 1.0, 1.2])
    labels = ["-20%", "Base", "+20%"]
    x = np.arange(len(labels))
    w = 0.32
    for idx, (scenario_id, color) in enumerate([("S1", "#0ea5e9"), ("S2", "#8b5cf6")]):
        r = _fairfield_result(results, phase, scenario_id)
        vals = []
        for f in factors:
            feed_adj = (r.substrate_cost + r.pretreatment_cost) * f
            total_cost = (
                feed_adj + r.nitrogen_cost + r.electricity_cost + r.steam_cost
                + r.extraction_cost + r.downstream_cost + r.cip_cost + r.labor_cost
                + r.annual_major_capex
            )
            vals.append((total_cost - r.annual_scp_kg * scp_credit_price) / max(1.0, r.annual_pha_kg))
        ax.bar(x + (idx - 0.5) * w, vals, width=w, color=color, edgecolor="white", linewidth=0.8, label=scenario_id)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("PHA MSP with SCP credit ($/kg)")
    ax.set_title(f"Feedstock sugar-content sensitivity (±20%) — {phase}")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=9)
    return fig


def fig_v5_oat_sensitivity(
    results: List[FairfieldResult],
    phase: str,
    scenario_id: str,
    acquisition_cost: float,
    added_major_capex: float,
    base_overrides: Dict[str, float],
    delta: float = 0.20,
) -> plt.Figure:
    base = _fairfield_result(results, phase, scenario_id)
    scenario = FAIRFIELD_SCENARIOS[scenario_id]

    base_feedstock_price = float(
        scenario.jb_share * base_overrides["jb_sugar_price"] + scenario.dlp_share * base_overrides.get("dlp_sugar_price", 0.0)
    )
    base_pretreat_cost = float(
        scenario.jb_share * base_overrides["jb_pretreat_cost"] + scenario.dlp_share * base_overrides.get("dlp_pretreat_cost", 0.0)
    )
    specs = [
        ("Biomass yield", "yield_kg_per_kg_sugar", base.yield_kg_per_kg_sugar),
        ("CDW titer", "titer_gL", base.titer_gL),
        ("PHB content", "phb_content_frac", base.phb_content_frac),
        ("Carbon recovery", "carbon_recovery_frac", base.carbon_recovery_frac),
        ("Electricity price", "electricity_price", float(base_overrides["electricity_price"])),
        ("Feedstock price", "blended_feedstock_price", base_feedstock_price),
        ("Pretreatment cost", "blended_pretreat_cost", base_pretreat_cost),
        ("Nitrogen reduction", "n_reduction_frac", base.n_reduction_frac),
        ("Labor", "labor_cost", base.labor_cost),
        ("Acquisition cost", "project_capex_purchase", acquisition_cost + added_major_capex),
        ("Discount rate", "discount_rate", float(base_overrides["discount_rate"])),
    ]

    labels: List[str] = []
    low_vals: List[float] = []
    high_vals: List[float] = []
    base_msp = base.pha_msp_with_scp_credit

    for label, key, value in specs:
        if key == "blended_feedstock_price":
            scale_lo = max(1e-9, 1.0 - delta)
            scale_hi = 1.0 + delta
            low_override = {
                "jb_sugar_price": base_overrides["jb_sugar_price"] * scale_lo,
                "dlp_sugar_price": base_overrides.get("dlp_sugar_price", 0.0) * scale_lo,
            }
            high_override = {
                "jb_sugar_price": base_overrides["jb_sugar_price"] * scale_hi,
                "dlp_sugar_price": base_overrides.get("dlp_sugar_price", 0.0) * scale_hi,
            }
        elif key == "blended_pretreat_cost":
            scale_lo = max(1e-9, 1.0 - delta)
            scale_hi = 1.0 + delta
            low_override = {
                "jb_pretreat_cost": base_overrides["jb_pretreat_cost"] * scale_lo,
                "dlp_pretreat_cost": base_overrides.get("dlp_pretreat_cost", 0.0) * scale_lo,
            }
            high_override = {
                "jb_pretreat_cost": base_overrides["jb_pretreat_cost"] * scale_hi,
                "dlp_pretreat_cost": base_overrides.get("dlp_pretreat_cost", 0.0) * scale_hi,
            }
        elif key == "project_capex_purchase":
            low_override = {key: max(1e-6, value * (1.0 - delta))}
            high_override = {key: value * (1.0 + delta)}
        elif key == "n_reduction_frac":
            low_override = {key: max(0.0, value - delta)}
            high_override = {key: min(0.98, value + delta)}
        elif key in {"phb_content_frac", "carbon_recovery_frac"}:
            low_override = {key: max(0.05, value * (1.0 - delta))}
            high_override = {key: min(0.95, value * (1.0 + delta))}
        elif key == "discount_rate":
            low_override = {key: max(0.01, value * (1.0 - delta))}
            high_override = {key: min(0.40, value * (1.0 + delta))}
        else:
            low_override = {key: max(1e-9, value * (1.0 - delta))}
            high_override = {key: value * (1.0 + delta)}

        low_case_overrides = dict(base_overrides)
        low_case_overrides.update(low_override)
        high_case_overrides = dict(base_overrides)
        high_case_overrides.update(high_override)

        low_r = _fairfield_single_result(
            phase, base.utilization_pct, scenario, acquisition_cost, added_major_capex, low_case_overrides
        )
        high_r = _fairfield_single_result(
            phase, base.utilization_pct, scenario, acquisition_cost, added_major_capex, high_case_overrides
        )
        labels.append(label)
        low_vals.append(low_r.pha_msp_with_scp_credit)
        high_vals.append(high_r.pha_msp_with_scp_credit)

    order = np.argsort([max(abs(lv - base_msp), abs(hv - base_msp)) for lv, hv in zip(low_vals, high_vals)])[::-1]
    labels = [labels[i] for i in order]
    low_vals = [low_vals[i] for i in order]
    high_vals = [high_vals[i] for i in order]

    fig, ax = plt.subplots(figsize=(13.8, 7.8), constrained_layout=True)
    y = np.arange(len(labels))
    for i, (lo, hi) in enumerate(zip(low_vals, high_vals)):
        ax.barh(i, abs(base_msp - lo), left=min(base_msp, lo), height=0.58, color="#f97316", alpha=0.88,
                edgecolor="white", linewidth=0.8, label="Low case" if i == 0 else None)
        ax.barh(i, abs(hi - base_msp), left=min(base_msp, hi), height=0.58, color="#8b5cf6", alpha=0.88,
                edgecolor="white", linewidth=0.8, label="High case" if i == 0 else None)
        ax.text(lo, i, f"${lo:.2f}", ha="right" if lo < base_msp else "left", va="center", fontsize=8,
                clip_on=False)
        ax.text(hi, i, f"${hi:.2f}", ha="left" if hi > base_msp else "right", va="center", fontsize=8,
                clip_on=False)
    ax.axvline(base_msp, color="#0f172a", lw=1.3)
    ax.text(base_msp, len(labels) + 0.15, f"Base MSP ${base_msp:.2f}/kg", ha="center", fontsize=9, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("PHA MSP with SCP credit ($/kg)")
    ax.set_title(f"One-at-a-time sensitivity (±{int(delta * 100)}%) — {scenario_id}, {phase}")
    ax.grid(axis="x", alpha=0.25)
    xmin = min(min(low_vals), min(high_vals), base_msp)
    xmax = max(max(low_vals), max(high_vals), base_msp)
    pad = max(0.08, 0.10 * (xmax - xmin))
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.legend(fontsize=9, loc="lower right")
    return fig


# ── Break-even analysis figures (live, driven by active sidebar settings) ──
def _breakeven_decomposition(
    phase: str,
    scenario_id: str,
    base_overrides: Dict[str, float],
    acquisition_cost: float,
    added_major_capex: float,
) -> Dict[str, float]:
    """Return revenue-per-CDW, variable-per-CDW, fixed labor, and break-even CDW/titer/util
    using the *active* scenario overrides and phase."""
    scenario = FAIRFIELD_SCENARIOS[scenario_id]
    base_r = _fairfield_single_result(
        phase, 100.0, scenario, acquisition_cost, added_major_capex, base_overrides
    )
    cdw = max(1.0, base_r.annual_cdw_kg)
    variable_cash = (
        base_r.substrate_cost + base_r.pretreatment_cost + base_r.nitrogen_cost
        + base_r.electricity_cost + base_r.steam_cost + base_r.extraction_cost
        + base_r.downstream_cost + base_r.cip_cost
    )
    rev_per_cdw = base_r.total_revenue / cdw
    var_per_cdw = variable_cash / cdw
    margin_per_cdw = rev_per_cdw - var_per_cdw
    labor = base_r.labor_cost
    be_cdw = labor / margin_per_cdw if margin_per_cdw > 1e-9 else float("nan")
    vessel_L = PHASE_VOLUMES_L[phase]
    cycles = _annual_operating_cycles()
    titer = base_r.titer_gL
    be_titer_at_current_util = (
        be_cdw / (vessel_L * (base_r.utilization_pct / 100.0) * cycles / 1000.0)
        if be_cdw == be_cdw else float("nan")
    )
    be_util_at_current_titer = (
        be_cdw / (vessel_L * (titer / 1000.0) * cycles) * 100.0
        if be_cdw == be_cdw else float("nan")
    )
    return {
        "rev_per_cdw": rev_per_cdw,
        "var_per_cdw": var_per_cdw,
        "margin_per_cdw": margin_per_cdw,
        "labor": labor,
        "be_cdw_kg": be_cdw,
        "be_titer_gL": be_titer_at_current_util,
        "be_util_pct": be_util_at_current_titer,
        "base_result": base_r,
    }


def fig_v5_waterfall(
    results: List[FairfieldResult],
    phase: str,
    scenario_id: str,
) -> plt.Figure:
    """Annual P&L waterfall — revenue minus each cost bucket → cash flow."""
    r = _fairfield_result(results, phase, scenario_id)
    rv = r.total_revenue / 1e6
    feed = (r.substrate_cost + r.pretreatment_cost) / 1e6
    nit = r.nitrogen_cost / 1e6
    elec = r.electricity_cost / 1e6
    stm = r.steam_cost / 1e6
    ext = r.extraction_cost / 1e6
    dwn = r.downstream_cost / 1e6
    hgp = float(getattr(r, "hgp_dsp_cost", 0.0)) / 1e6
    cp = r.cip_cost / 1e6
    lab = r.labor_cost / 1e6
    cap = r.annual_major_capex / 1e6
    cf = r.annual_cash_flow / 1e6
    hgp_on = bool(getattr(r, "annual_hgp_kg", 0.0) > 0)
    pha_on = bool(getattr(r, "annual_pha_kg", 0.0) > 0)
    if hgp_on and pha_on:
        rev_label = "Revenue\n(PHA+HGP)"
    elif hgp_on:
        rev_label = "Revenue\n(HGP)"
    else:
        rev_label = "Revenue\n(PHA+SCP)"
    values = [rv, -feed, -nit, -elec, -stm, -ext, -dwn, -hgp, -cp, -lab, -cap, cf]
    labels = [
        rev_label, "Feedstock &\npretreat", "Nitrogen",
        "Electricity", "Steam", "PHA\nextraction", "Downstream",
        "HGP DSP", "CIP / maint.", "Labor", "Annualized\nCapEx", "Cash\nflow",
    ]
    colors = ["#059669"] + ["#dc2626"] * 10 + ["#0369a1"]
    starts: List[float] = []
    running = 0.0
    for v in values[:-1]:
        starts.append(running)
        running += v
    starts.append(0.0)

    fig, ax = plt.subplots(figsize=(12.5, 5.8), constrained_layout=True)
    for i, (val, s) in enumerate(zip(values, starts)):
        ax.bar(i, val, bottom=s, color=colors[i], edgecolor="white",
               linewidth=1.2, width=0.72)
        mid = s + val / 2.0
        ax.text(i, mid, f"${abs(val):.2f}M", ha="center", va="center",
                fontsize=9, fontweight="bold",
                color="white" if abs(val) > 0.35 else "#0f172a")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("$M/yr", fontsize=11)
    ax.set_title(
        f"Annual P&L waterfall — {phase} / {scenario_id} "
        f"({r.titer_gL:.0f} g/L CDW, {r.utilization_pct:.0f}% utilization)",
        fontsize=12, color="#0f172a",
    )
    ax.axhline(0, color="#0f172a", linewidth=0.8)
    ax.grid(axis="y", alpha=0.3)
    return fig


def fig_v5_revenue_vs_opex(
    phase: str,
    scenario_id: str,
    base_overrides: Dict[str, float],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """Annual revenue vs annual OpEx as CDW titer sweeps 10–80 g/L at active utilization."""
    scenario = FAIRFIELD_SCENARIOS[scenario_id]
    base_r = _fairfield_single_result(
        phase, base_overrides.get("__util", 100.0), scenario,
        acquisition_cost, added_major_capex, base_overrides
    )
    util = base_r.utilization_pct
    titers = np.linspace(10.0, 80.0, 141)
    revs: List[float] = []
    opxs: List[float] = []
    for t in titers:
        ov = dict(base_overrides)
        ov["titer_gL"] = float(t)
        r = _fairfield_single_result(
            phase, util, scenario, acquisition_cost, added_major_capex, ov
        )
        cash_opex = r.total_annual_cost - r.annual_major_capex
        revs.append(r.total_revenue / 1e6)
        opxs.append(cash_opex / 1e6)
    info = _breakeven_decomposition(
        phase, scenario_id, base_overrides, acquisition_cost, added_major_capex
    )
    be_titer = info["be_titer_gL"]

    fig, ax = plt.subplots(figsize=(11.5, 5.4), constrained_layout=True)
    ax.plot(titers, revs, color="#059669", linewidth=2.8, label="Annual revenue")
    ax.plot(titers, opxs, color="#dc2626", linewidth=2.8, label="Annual cash OpEx")
    ax.fill_between(titers, revs, opxs,
                    where=(np.array(revs) > np.array(opxs)),
                    color="#bbf7d0", alpha=0.5, label="Profit zone")
    ax.fill_between(titers, revs, opxs,
                    where=(np.array(revs) <= np.array(opxs)),
                    color="#fecaca", alpha=0.5, label="Loss zone")
    if be_titer == be_titer and 10.0 <= be_titer <= 80.0:
        ax.axvline(be_titer, color="#0f172a", linewidth=1.2, linestyle=":")
        ax.text(be_titer + 0.8, min(revs) + 0.1 * (max(revs) - min(revs)),
                f"Break-even\n{be_titer:.1f} g/L",
                color="#0f172a", fontsize=10, fontweight="bold")
    ax.set_xlabel("CDW titer (g/L)", fontsize=11)
    ax.set_ylabel("$M/yr", fontsize=11)
    ax.set_title(
        f"Annual revenue vs. cash OpEx — {phase} / {scenario_id}, "
        f"{util:.0f}% utilization",
        fontsize=12, color="#0f172a",
    )
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=9)
    return fig


def fig_v5_breakeven_titer(
    phase: str,
    scenario_id: str,
    base_overrides: Dict[str, float],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """Annual cash flow as CDW titer sweeps from 0 to 80 g/L at active utilization."""
    scenario = FAIRFIELD_SCENARIOS[scenario_id]
    base_r = _fairfield_single_result(
        phase, 100.0, scenario, acquisition_cost, added_major_capex, base_overrides
    )
    util = base_r.utilization_pct
    active_titer = base_r.titer_gL
    titers = np.linspace(0.0, 80.0, 161)
    cfs: List[float] = []
    for t in titers:
        ov = dict(base_overrides)
        ov["titer_gL"] = float(t)
        r = _fairfield_single_result(
            phase, util, scenario, acquisition_cost, added_major_capex, ov
        )
        cfs.append(r.annual_cash_flow / 1e6)
    info = _breakeven_decomposition(
        phase, scenario_id, base_overrides, acquisition_cost, added_major_capex
    )
    be_titer = info["be_titer_gL"]

    fig, ax = plt.subplots(figsize=(11.5, 5.4), constrained_layout=True)
    arr = np.array(cfs)
    ax.plot(titers, cfs, color="#0e746f", linewidth=2.8)
    ax.axhline(0, color="#64748b", linewidth=1, linestyle="--")
    ax.fill_between(titers, cfs, 0, where=(arr < 0),
                    color="#fecaca", alpha=0.55, label="Negative cash flow")
    ax.fill_between(titers, cfs, 0, where=(arr >= 0),
                    color="#bbf7d0", alpha=0.55, label="Positive cash flow")
    if be_titer == be_titer and 0.0 <= be_titer <= 80.0:
        ax.axvline(be_titer, color="#ef4444", linewidth=1.5, linestyle=":")
        ax.text(be_titer + 1.0, arr.min() * 0.55,
                f"Cash break-even\n{be_titer:.1f} g/L",
                color="#ef4444", fontsize=10, fontweight="bold")
    if 0.0 <= active_titer <= 80.0:
        ax.axvline(active_titer, color="#0f172a", linewidth=1.2, alpha=0.7)
        ax.text(active_titer, arr.max() * 0.85,
                f"Active\n{active_titer:.1f} g/L",
                ha="center", color="#0f172a", fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="#f1f5f9", ec="#cbd5e1"))
    ax.set_xlabel("CDW titer (g/L)", fontsize=11)
    ax.set_ylabel("Annual cash flow ($M/yr)", fontsize=11)
    ax.set_title(
        f"Cash flow sensitivity to CDW titer — {phase} / {scenario_id}, "
        f"{util:.0f}% utilization",
        fontsize=12, color="#0f172a",
    )
    ax.grid(alpha=0.25)
    ax.set_xlim(0, 80)
    ax.legend(loc="upper left", fontsize=9)
    return fig


def fig_v5_breakeven_util(
    phase: str,
    scenario_id: str,
    base_overrides: Dict[str, float],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """Annual cash flow as utilization sweeps from 0 to 100% at active CDW titer."""
    scenario = FAIRFIELD_SCENARIOS[scenario_id]
    base_r = _fairfield_single_result(
        phase, 100.0, scenario, acquisition_cost, added_major_capex, base_overrides
    )
    active_util = base_r.utilization_pct
    utils = np.linspace(0.0, 100.0, 101)
    cfs: List[float] = []
    for u in utils:
        r = _fairfield_single_result(
            phase, float(u), scenario, acquisition_cost, added_major_capex, base_overrides
        )
        cfs.append(r.annual_cash_flow / 1e6)
    info = _breakeven_decomposition(
        phase, scenario_id, base_overrides, acquisition_cost, added_major_capex
    )
    be_util = info["be_util_pct"]

    fig, ax = plt.subplots(figsize=(11.5, 5.4), constrained_layout=True)
    arr = np.array(cfs)
    ax.plot(utils, cfs, color="#0369a1", linewidth=2.8)
    ax.axhline(0, color="#64748b", linewidth=1, linestyle="--")
    ax.fill_between(utils, cfs, 0, where=(arr < 0),
                    color="#fecaca", alpha=0.55, label="Negative cash flow")
    ax.fill_between(utils, cfs, 0, where=(arr >= 0),
                    color="#bbf7d0", alpha=0.55, label="Positive cash flow")
    if be_util == be_util and 0.0 <= be_util <= 100.0:
        ax.axvline(be_util, color="#ef4444", linewidth=1.5, linestyle=":")
        ax.text(be_util + 1.0, arr.min() * 0.55,
                f"Cash break-even\n{be_util:.1f}%",
                color="#ef4444", fontsize=10, fontweight="bold")
    if 0.0 <= active_util <= 100.0:
        ax.axvline(active_util, color="#0f172a", linewidth=1.2, alpha=0.7)
        ax.text(active_util, arr.max() * 0.85,
                f"Active\n{active_util:.0f}%",
                ha="center", color="#0f172a", fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="#f1f5f9", ec="#cbd5e1"))
    ax.set_xlabel(f"Utilization of {PHASE_VOLUMES_L[phase]:,.0f} L installed volume (%)",
                  fontsize=11)
    ax.set_ylabel("Annual cash flow ($M/yr)", fontsize=11)
    ax.set_title(
        f"Cash flow sensitivity to utilization — {phase} / {scenario_id}, "
        f"{base_r.titer_gL:.0f} g/L CDW",
        fontsize=12, color="#0f172a",
    )
    ax.grid(alpha=0.25)
    ax.set_xlim(0, 100)
    ax.legend(loc="upper left", fontsize=9)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  v10 memo-parity figures (live, slider-driven) — added for Revision 3 report
# ═══════════════════════════════════════════════════════════════════════════════
# These four figures mirror the memo / Revision 3 investor report and are
# driven entirely by current sidebar state. They compute the three-mode
# comparison (v9 baseline / HGP co-production / HGP alone) on the fly by
# toggling hgp_enabled and hgp_production_mode in a copy of the active
# overrides dict, so the user can see how moving any slider reshapes the
# headline story.

V10_C_OFF   = "#64748B"   # slate grey (baseline)
V10_C_COPR  = "#0E746F"   # teal (co-production)
V10_C_ALONE = "#B45309"   # amber (alone)


def _v10_three_mode_phase3(
    common_overrides: Dict[str, Any],
    scenario_overrides: Dict[str, Dict[str, Any]],
    acquisition_cost: float,
    added_major_capex: float,
) -> Dict[str, Dict[str, Any]]:
    """Run Phase III at both scenarios for the three HGP modes using the
    currently-active settings. Returns {mode -> {sid -> FairfieldResult}}.
    mode ∈ {'off','coprod','alone'}."""
    phase = "Phase III"
    util_pct = float(PHASE_DEFAULT_UTIL[phase])
    out: Dict[str, Dict[str, Any]] = {"off": {}, "coprod": {}, "alone": {}}
    mode_overrides = {
        "off":    {"hgp_enabled": False},
        "coprod": {"hgp_enabled": True, "hgp_production_mode": "coproduction"},
        "alone":  {"hgp_enabled": True, "hgp_production_mode": "alone"},
    }
    for mkey, mov in mode_overrides.items():
        for sid, scen in FAIRFIELD_SCENARIOS.items():
            ov = dict(common_overrides)
            ov.update(scenario_overrides[sid])
            ov.update(mov)
            ov["labor_cost"] = PHASE_FIXED_LABOR[phase]
            out[mkey][sid] = _fairfield_single_result(
                phase, util_pct, scen, acquisition_cost, added_major_capex, ov
            )
    return out


def fig_v10_phase3_headline(
    common_overrides: Dict[str, Any],
    scenario_overrides: Dict[str, Dict[str, Any]],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """Three-mode Phase III bars: revenue / cash flow / NPV, S1 and S2."""
    grid = _v10_three_mode_phase3(common_overrides, scenario_overrides, acquisition_cost, added_major_capex)
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.4))
    modes = ["off", "coprod", "alone"]
    mode_labels = ["Baseline (v9)\nfeed-grade SCP",
                   "HGP co-production\nwith polymer",
                   "HGP alone\n(phaCAB KO)"]
    metrics = [("rev",  "Phase III annual revenue ($M)", lambda r: r.total_revenue / 1e6),
               ("cf",   "Phase III annual cash flow ($M)", lambda r: r.annual_cash_flow / 1e6),
               ("npv",  "Phase III 10-yr NPV ($M)", lambda r: r.npv / 1e6)]
    width = 0.35
    x = np.arange(len(modes))
    for ax, (_, title, f) in zip(axes, metrics):
        s1 = [f(grid[m]["S1"]) for m in modes]
        s2 = [f(grid[m]["S2"]) for m in modes]
        ax.bar(x - width/2, s1, width, color="#0E746F", label="S1 (JB COD)")
        ax.bar(x + width/2, s2, width, color="#B45309", label="S2 (70/30 JB+DLP)")
        ax.set_xticks(x)
        ax.set_xticklabels(mode_labels, fontsize=8.5)
        ax.set_title(title, fontsize=10.5)
        ax.grid(axis="y", alpha=0.3)
        ax.axhline(0, color="#334155", linewidth=0.6)
        for xi, (a, b) in enumerate(zip(s1, s2)):
            for xv, yv in ((xi - width/2, a), (xi + width/2, b)):
                va = "bottom" if yv >= 0 else "top"
                ax.annotate(f"{yv:,.0f}", (xv, yv),
                            xytext=(0, 3 if yv >= 0 else -3),
                            textcoords="offset points",
                            ha="center", va=va, fontsize=7.5)
        ymax = max(max(s1), max(s2))
        ymin = min(min(s1), min(s2), 0)
        ax.set_ylim(ymin * 1.15 if ymin < 0 else 0, ymax * 1.20 if ymax > 0 else 1)
    axes[0].legend(loc="upper left", framealpha=0.9, fontsize=8.5)
    fig.suptitle(
        "Phase III headline economics across HGP operating modes (live, reflects current sidebar)",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    return fig


def fig_v10_mass_flow_phase3(
    common_overrides: Dict[str, Any],
    scenario_overrides: Dict[str, Dict[str, Any]],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """Stacked Phase III product slate (PHA / feed-SCP / HGP) for S1 across
    three modes, responsive to current slider state."""
    grid = _v10_three_mode_phase3(common_overrides, scenario_overrides, acquisition_cost, added_major_capex)
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    modes = ["off", "coprod", "alone"]
    mode_labels = ["Baseline (v9)\nSCP + PHA",
                   "HGP + PHA\nco-production",
                   "HGP alone\n(phaCAB KO)"]
    pha = [grid[m]["S1"].annual_pha_kg / 1000.0 for m in modes]
    scp = [grid[m]["S1"].annual_scp_kg / 1000.0 for m in modes]
    hgp = [getattr(grid[m]["S1"], "annual_hgp_kg", 0.0) / 1000.0 for m in modes]
    x = np.arange(len(modes)); w = 0.6
    ax.bar(x, pha, w, color="#0E746F", label="PHA (sellable t/y)")
    ax.bar(x, scp, w, bottom=pha, color="#64748B", label="Feed-grade SCP (t/y)")
    ax.bar(x, hgp, w, bottom=[p + s for p, s in zip(pha, scp)],
           color="#B45309", label="HGP whole-cell mash (t/y)")
    totals = [p + s + h for p, s, h in zip(pha, scp, hgp)]
    for xi, (p, s, h, t) in enumerate(zip(pha, scp, hgp, totals)):
        if p > 50:
            ax.text(xi, p / 2, f"PHA\n{p:,.0f}", ha="center", va="center",
                    color="white", fontsize=8.5, fontweight="bold")
        if s > 50:
            ax.text(xi, p + s / 2, f"SCP\n{s:,.0f}", ha="center", va="center",
                    color="white", fontsize=8.5, fontweight="bold")
        if h > 50:
            ax.text(xi, p + s + h / 2, f"HGP\n{h:,.0f}", ha="center", va="center",
                    color="white", fontsize=8.5, fontweight="bold")
        ax.text(xi, t * 1.02 + 50, f"{t:,.0f} t/y\ntotal", ha="center", va="bottom",
                fontsize=9, color="#0F172A")
    ax.set_xticks(x); ax.set_xticklabels(mode_labels, fontsize=9)
    ax.set_ylabel("Sellable product mass (t/y)")
    ax.set_title("Phase III product slate by operating mode, S1 (live, reflects current sidebar)")
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, (max(totals) if totals else 1) * 1.2)
    ax.legend(loc="upper left", framealpha=0.9)
    fig.tight_layout()
    return fig


def fig_v10_hgp_price_sensitivity(
    common_overrides: Dict[str, Any],
    scenario_overrides: Dict[str, Dict[str, Any]],
    acquisition_cost: float,
    added_major_capex: float,
) -> plt.Figure:
    """NPV at Phase III vs HGP selling price for both co-prod and alone
    configurations, both scenarios. Respects current sidebar for everything
    except HGP price (swept 3-12 $/kg) and HGP on/off/mode."""
    phase = "Phase III"
    util_pct = float(PHASE_DEFAULT_UTIL[phase])
    price_grid = np.round(np.arange(3.0, 12.05, 0.5), 2)
    curves = {("coprod", "S1"): [], ("coprod", "S2"): [],
              ("alone",  "S1"): [], ("alone",  "S2"): []}
    mode_overrides = {
        "coprod": {"hgp_enabled": True, "hgp_production_mode": "coproduction"},
        "alone":  {"hgp_enabled": True, "hgp_production_mode": "alone"},
    }
    for p in price_grid:
        for mkey, mov in mode_overrides.items():
            for sid, scen in FAIRFIELD_SCENARIOS.items():
                ov = dict(common_overrides)
                ov.update(scenario_overrides[sid])
                ov.update(mov)
                ov["hgp_selling_price"] = float(p)
                ov["labor_cost"] = PHASE_FIXED_LABOR[phase]
                r = _fairfield_single_result(
                    phase, util_pct, scen, acquisition_cost, added_major_capex, ov
                )
                curves[(mkey, sid)].append(r.npv / 1e6)
    hgp_price_now = float(common_overrides.get("hgp_selling_price", HGP_SELLING_PRICE_DEFAULT))
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.plot(price_grid, curves[("coprod", "S1")], "-o", color=V10_C_COPR,
            markersize=4, label="HGP + PHA co-production, S1")
    ax.plot(price_grid, curves[("coprod", "S2")], "--s", color=V10_C_COPR,
            markersize=4, label="HGP + PHA co-production, S2")
    ax.plot(price_grid, curves[("alone",  "S1")], "-o", color=V10_C_ALONE,
            markersize=4, label="HGP alone (N-replete), S1")
    ax.plot(price_grid, curves[("alone",  "S2")], "--s", color=V10_C_ALONE,
            markersize=4, label="HGP alone (N-replete), S2")
    ax.axvline(hgp_price_now, color="#0F172A", linestyle=":", alpha=0.7)
    ax.axhline(0, color="#334155", linewidth=0.6)
    ax.axvspan(3.0, 6.0, color="#F1F5F9", alpha=0.6, zorder=0)
    ax.axvspan(6.0, 10.0, color="#ECFDF5", alpha=0.4, zorder=0)
    ax.axvspan(10.0, 12.0, color="#FEF3C7", alpha=0.3, zorder=0)
    ymin, ymax = ax.get_ylim()
    ax.text(4.5, ymin + (ymax - ymin) * 0.05, "Solein cost-\ntarget floor",
            ha="center", fontsize=8, color="#475569")
    ax.text(8.0, ymin + (ymax - ymin) * 0.05, "Quorn / Solein\nmid-band",
            ha="center", fontsize=8, color="#475569")
    ax.text(11.0, ymin + (ymax - ymin) * 0.05, "Branded\nspecialty",
            ha="center", fontsize=8, color="#475569")
    ax.text(hgp_price_now, ymax * 0.92 if ymax > 0 else 0,
            f"current\n${hgp_price_now:.2f}/kg", fontsize=8.5, color="#0F172A",
            va="top", ha="left")
    ax.set_xlabel("HGP selling price ($/kg)")
    ax.set_ylabel("Phase III 10-yr NPV ($M)")
    ax.set_title("Phase III NPV sensitivity to HGP selling price (live, reflects current sidebar)")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", framealpha=0.9, fontsize=8.5)
    fig.tight_layout()
    return fig


def fig_v10_dsp_stack(
    hgp_dsp_cost_per_kg: float,
) -> plt.Figure:
    """Side-by-side DSP cost stack ($/kg sellable non-PHA product): feed-grade
    SCP (centrifuge + spray-dry + pelletize, ~$0.60/kg all-in) vs HGP whole-
    cell mash (TFF endotoxin + food-grade spray dry + QA). The HGP total
    respects the current sidebar HGP-DSP slider by proportionally scaling
    the three HGP sub-lines so the stack sums to the active $/kg value."""
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    scp_stack = [
        ("Centrifuge + spray dry\n+ pelletize", 0.55, "#64748B"),
        ("CIP + sanitation",                    0.05, "#94A3B8"),
    ]
    base_hgp = [
        ("Endotoxin (LPS) removal\nTFF + polymyxin-B polish", 1.05, "#B45309"),
        ("Food-grade spray dry\n+ sanitary packaging",        0.50, "#D97706"),
        ("QA / regulatory overhead",                          0.25, "#FCD34D"),
    ]
    base_hgp_total = sum(v for _, v, _ in base_hgp)
    scale = hgp_dsp_cost_per_kg / base_hgp_total if base_hgp_total > 0 else 1.0
    hgp_stack = [(name, v * scale, c) for (name, v, c) in base_hgp]
    scp_total = sum(v for _, v, _ in scp_stack)
    hgp_total = sum(v for _, v, _ in hgp_stack)
    for col_x, stack, total in [(0, scp_stack, scp_total), (1, hgp_stack, hgp_total)]:
        bottom = 0.0
        for (name, val, color) in stack:
            ax.bar(col_x, val, width=0.5, bottom=bottom, color=color,
                   edgecolor="white", linewidth=1.0)
            if val > 0.1:
                ax.text(col_x, bottom + val / 2, f"{name}\n${val:.2f}/kg",
                        ha="center", va="center", color="white",
                        fontsize=8.0, fontweight="bold")
            bottom += val
        ax.text(col_x, total + 0.06, f"${total:.2f}/kg\nall-in",
                ha="center", va="bottom", fontsize=10, color="#0F172A",
                fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Feed-grade SCP\n(animal feed)",
                        "HGP whole-cell mash\n(human ingredient)"])
    ax.set_ylabel("Downstream cost ($/kg sellable non-PHA product)")
    ax.set_title(f"DSP cost stack: feed-grade SCP vs HGP (HGP slider at ${hgp_dsp_cost_per_kg:.2f}/kg)")
    ax.set_ylim(0, max(scp_total, hgp_total) * 1.4)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


V5_FIGURE_FORMULAS: Dict[str, str] = {
    "Phase Output": (
        "This figure is built in 4 steps.\n\n"
        "1. **Utilized vessel volume** = installed vessel volume × utilization.\n"
        "Example: Phase III at 90% utilization uses 400,000 L × 0.90 = 360,000 L of broth volume.\n\n"
        "2. **Annual operating cycles** = 8,760 h/year × 85% uptime ÷ 24 h HRT = 310.25 turnover-equivalents per year.\n\n"
        "3. **Annual CDW** = utilized vessel volume × CDW titer × annual operating cycles.\n"
        "The v7 base case is locked at 60 g/L for both S1 and S2 (was 35 g/L for S1 in v5/v6).\n\n"
        "For example, Phase III S1 at 90% utilization and the 60 g/L v7 base case gives "
        "360,000 L × 60 g/L × 310.25 ÷ 1,000,000 = about 6,701 t/y CDW. At the v5/v6 "
        "conservative 35 g/L, the same calculation gives about 3,909 t/y CDW. "
        "Note: the site handoff (Fairfield_TEA_v7_Final.pdf, page 7) states "
        "~10,700 t/y for the 35 g/L case, which is arithmetically incorrect — "
        "the handoff's own formula evaluates to ~3,909 t/y.\n\n"
        "4. **Sellable PHA** = annual CDW × PHB fraction × 0.88 extraction recovery × 0.95 dry basis.\n\n"
        "5. **Sellable SCP** = annual CDW × (1 - PHB fraction) × 0.85 biomass recovery × 0.92 dry basis.\n\n"
        "The stacked bars therefore show final sellable product tonnage, not raw fermentation mass."
    ),
    "MSP and Cash Flow": (
        "This figure combines two related calculations.\n\n"
        "**Left panel: PHA MSP with SCP credit**\n"
        "1. Add annual costs: feedstock + pretreatment + nitrogen + electricity + steam + extraction + downstream + CIP/maintenance + labor + annualized CapEx.\n"
        "2. Compute SCP credit = annual sellable SCP × the current `SCP credit` slider value.\n"
        "3. Compute PHA MSP with SCP credit = (total annual cost - SCP credit) ÷ annual sellable PHA.\n\n"
        "**Right panel: annual cash flow**\n"
        "1. PHA revenue = annual sellable PHA × blended PHA price.\n"
        "The blended PHA price comes from the current PHB price, PHBV price, and PHB share sliders.\n"
        "2. SCP revenue = annual sellable SCP × the current SCP selling price slider.\n"
        "3. Cash flow = total revenue - cash operating cost.\n"
        "Cash operating cost excludes annualized CapEx, because capital is treated as an upfront investment in the finance model."
    ),
    "Returns by Phase": (
        "This figure compares finance outcomes across Phase I / II / III for each scenario.\n\n"
        "1. **Project CapEx** = acquisition slider + added major CapEx slider.\n"
        "2. **Annual cash flow** = revenue - cash operating cost.\n"
        "3. **NPV** = -project CapEx + sum of discounted annual cash flow over the current NPV horizon at the current discount rate.\n"
        "4. **IRR** = discount rate that makes the NPV exactly zero.\n"
        "5. **Simple payback** = project CapEx ÷ annual cash flow.\n\n"
        "This figure answers how the project improves financially as the facility moves from 50,000 L to 400,000 L."
    ),
    "S1 vs S2 Across Phases": (
        "Investor-memo-style 3-panel grouped bar chart comparing Scenario 1 and Scenario 2 "
        "at Phase I, II, and III.\n\n"
        "1. **Annual revenue** = annual sellable PHA × PHA revenue price + annual sellable SCP × SCP selling price. "
        "In PHBV mode the PHA stream is priced at the (auto-scaled or overridden) PHBV price.\n"
        "2. **Annual cash flow** = annual revenue - cash operating cost (excludes annualized CapEx).\n"
        "3. **10-year NPV** = -project CapEx + sum of discounted annual cash flow at the current discount rate "
        "and horizon.\n\n"
        "Because titer and PHB content are shared between S1 and S2 at the v9 base case, the two scenarios "
        "produce identical PHA and SCP tonnage (top-line revenue is identical). S1 and S2 differ only on the "
        "cost side: S2 has higher nitrogen reduction and higher carbon recovery but pays a DLP pretreatment "
        "step and a galactose-uptake penalty on the DLP fraction. The panel titles and subtitle reflect the "
        "currently selected SCP price, DSP pathway, and PHBV setting."
    ),
    "NPV vs Selling Price": (
        "This figure holds the selected phase fixed and sweeps only the PHA selling price.\n\n"
        "1. For each candidate PHA price, compute annual PHA revenue = annual sellable PHA × swept price.\n"
        "2. SCP revenue stays fixed at annual sellable SCP × the current SCP selling price slider.\n"
        "3. Annual cash flow = total revenue - cash operating cost.\n"
        "4. NPV = -upfront project CapEx + discounted annual cash flow over the current horizon at the current discount rate.\n\n"
        "The x-intercept is the breakeven PHA price where project NPV becomes zero."
    ),
    "IRR vs Selling Price": (
        "This figure uses the same price sweep as the NPV figure, but solves for IRR instead of NPV.\n\n"
        "For each candidate PHA price:\n"
        "1. Compute annual revenue and annual cash flow.\n"
        "2. Solve for IRR in: 0 = -project CapEx + sum of annual cash flow / (1 + IRR)^t.\n"
        "3. If project CapEx is zero, IRR is undefined, so the chart shows an explanatory note instead of a line.\n\n"
        "Higher curves mean the phase/scenario combination clears investor hurdle rates at lower selling prices."
    ),
    "Cost Structure": (
        "This figure decomposes the selected phase/scenario annual cost into explicit buckets.\n\n"
        "The bars shown are:\n"
        "- feedstock sugar cost\n"
        "- pretreatment cost\n"
        "- nitrogen supplementation\n"
        "- electricity\n"
        "- steam / thermal\n"
        "- PHA extraction\n"
        "- downstream finishing\n"
        "- CIP / maintenance\n"
        "- labor\n"
        "- annualized CapEx\n\n"
        "Each bar value is annual dollars converted to M$/yr, so the chart is a true annual budget breakdown."
    ),
    "Discounted Cash Flow": (
        "This is the standard discounted cash flow build for the selected phase/scenario.\n\n"
        "1. Year 0 starts at negative project CapEx.\n"
        "2. Each later year adds annual cash flow discounted by the current discount-rate slider.\n"
        "3. Cumulative discounted cash flow is plotted through time.\n\n"
        "Where the line crosses zero is the discounted payback point."
    ),
    "Feedstock Sensitivity": (
        "This is a targeted uncertainty check tied to the open HPLC data gap.\n\n"
        "1. Only feedstock sugar cost + pretreatment cost are varied.\n"
        "2. Three cases are evaluated: -20%, base, and +20%.\n"
        "3. All other costs and yields remain unchanged.\n"
        "4. The resulting PHA MSP with SCP credit is recalculated for S1 and S2 using the current SCP credit slider value.\n\n"
        "This is not a full tornado; it is a specific composition-risk sensitivity for the Jelly Belly stream."
    ),
    "OAT Sensitivity": (
        "This is a one-at-a-time tornado for the selected phase and selected scenario.\n\n"
        "1. Start from the base case MSP with SCP credit.\n"
        "2. Change one input at a time by ±20%, while keeping every other input fixed.\n"
        "3. Recompute the full Fairfield result using the same v5 equations.\n"
        "4. Plot the resulting low and high MSP values on either side of the base MSP line.\n\n"
        "Inputs tested include yield, titer, PHB content, carbon recovery, electricity price, blended feedstock price, blended pretreatment cost, nitrogen reduction, labor, acquisition cost, and discount rate.\n\n"
        "Longer bars mean that input has a larger effect on the selected case economics."
    ),
    "Phase III Headline (v10, three modes)": (
        "Three-mode headline chart used in the investor memo.\n\n"
        "For each HGP mode (off / co-production / alone) the engine is run at Phase III with the current "
        "sidebar settings:\n"
        "- **off**: v9 baseline. Non-PHA biomass is sold as feed-grade SCP at the current SCP price.\n"
        "- **co-production**: HGP toggle ON, mode = co-production. Polymer and non-PHA streams are "
        "unchanged from v9, but the non-PHA stream is priced at the HGP selling price with the HGP "
        "DSP cost line added.\n"
        "- **alone**: HGP toggle ON, mode = alone. PHB content is forced to the alone-mode basal value "
        "(0% for a phaCAB-knockout strain, up to 15% to model a leaky wild-type). Full CDW routes into "
        "HGP at the 85% whole-cell recovery.\n\n"
        "Three panels show annual revenue, annual cash flow, and 10-year NPV at the current discount "
        "rate, with S1 and S2 side by side. Every bar is recomputed whenever any sidebar slider moves."
    ),
    "Product Slate by Mode (Phase III)": (
        "Stacked Phase III mass flow for S1 across the three HGP modes, built using the current sidebar.\n\n"
        "For each mode the engine returns annual sellable PHA, annual sellable feed-grade SCP, and annual "
        "HGP whole-cell mash tonnage.\n\n"
        "Totals above each bar are annual sellable product mass, not raw fermentation mass. Downstream "
        "recoveries are baked into the tonnage (PHA 0.88 × 0.95; feed-grade SCP 0.85 × 0.92; HGP 0.85 "
        "whole-cell mash on the non-PHA fraction of CDW)."
    ),
    "HGP Price Sensitivity": (
        "Phase III 10-year NPV as the HGP selling price sweeps from $3/kg to $12/kg, holding everything "
        "else at the current sidebar values.\n\n"
        "Four curves are shown: co-production S1, co-production S2, HGP-alone S1, HGP-alone S2. The "
        "solid vertical line marks the current HGP price slider value. The three shaded bands are the "
        "commercial reference ranges used elsewhere in the model: $3-6/kg (Solein dry-protein production-"
        "cost floor), $6-10/kg (Quorn / Solein mid-band), and $10-12/kg (branded specialty off-take).\n\n"
        "Anywhere the curves sit above zero the project is NPV-positive at that HGP price."
    ),
    "P&L Waterfall": (
        "Annual P&L decomposition at the current focus phase and scenario.\n\n"
        "Starts from total annual revenue (PHA + SCP or HGP) and subtracts each cost bucket in turn "
        "(feedstock, pretreatment, nitrogen, electricity, steam, PHA extraction, downstream, CIP, HGP "
        "DSP if enabled, labor) to land on annual operating cash flow (excluding annualized CapEx).\n\n"
        "Green bars are additive (revenue), red bars are subtractive (cost buckets), blue is the residual "
        "operating cash flow for the year."
    ),
    "DSP Cost Stack": (
        "Side-by-side downstream-processing cost stack, $/kg of sellable non-PHA product.\n\n"
        "**Left:** feed-grade SCP train (centrifuge + spray-dry + pelletize + CIP), ~$0.60/kg all-in at "
        "Phase III scale. This number is included in the engine's CDW-wide downstream cost line and has "
        "no separate SCP DSP slider.\n\n"
        "**Right:** HGP whole-cell mash train (TFF endotoxin reduction + optional polymyxin-B polish + "
        "food-grade spray dry + sanitary packaging + release QA). The sub-stack is scaled so the total "
        "matches the **HGP DSP cost ($/kg HGP)** slider in the sidebar, so moving that slider "
        "proportionally rescales the three HGP segments."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP FLOW
# ═══════════════════════════════════════════════════════════════════════════════

_require_app_password()

st.title("Leatherback Fairfield TEA Dashboard v10")
st.caption(
    "Dedicated Fairfield dashboard | AB InBev Fairfield brewery | "
    "Continuous fermentation (24 h HRT, 85% uptime) | "
    "DSP pathway selector (NaOCl / NaOH / Mechanical+enzymatic) | "
    "PHBV co-production toggle | "
    "Human-grade SCP toggle (v10) with co-production and HGP-alone sub-modes | "
    "Scenarios 1 and 2 | NCIMB 11599 | "
    "Base case: 60 g/L CDW, 60% PHB (sidebar-adjustable)"
)

_sb_hdr("Focus View")
st.sidebar.caption(
    "This does not change the full model run. It only chooses which phase/scenario the summary cards and single-case figures focus on."
)
focus_phase = st.sidebar.selectbox("Detailed chart phase", list(PHASE_VOLUMES_L.keys()), index=2, key="v5_focus_phase")
focus_scenario = st.sidebar.selectbox(
    "Detailed chart scenario",
    [f"{k} — {v.title}" for k, v in FAIRFIELD_SCENARIOS.items()],
    index=0,
    key="v5_focus_scenario",
)
focus_scenario_id = focus_scenario.split(" — ", 1)[0]

_sb_hdr("Fairfield Controls")
phase_utils = {
    phase: float(
        st.sidebar.slider(
            f"{phase} utilization (%)",
            5, 100, PHASE_DEFAULT_UTIL[phase], 1,
            key=f"v5_{phase}_util",
        )
    )
    for phase in PHASE_VOLUMES_L
}
acquisition_cost = (
    st.sidebar.slider(
        "Acquisition cost ($M)",
        min_value=0.0,
        max_value=45.0,
        value=0.0,
        step=1.0,
        format="$%.1fM",
        key="v5_acquisition_cost",
        help="Upfront Fairfield acquisition cost. This is modeled as an upfront purchase cost and annualized through the finance layer.",
    ) * 1e6
)
added_major_capex = (
    st.sidebar.slider(
        "Added major CapEx ($M)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.5,
        format="$%.1fM",
        key="v5_added_major_capex",
        help="Additional major purchased capital above the acquired facility. This is modeled as upfront added capital and annualized through the finance layer.",
    ) * 1e6
)

# Continuous fermentation only (fed-batch UI removed).
operating_mode = "continuous"

_sb_hdr("Scenario 1 Inputs")
st.sidebar.caption(
    "S1 base case locked at 60 g/L CDW, 60% PHB content, 50% nitrogen reduction, "
    "100% Jelly Belly COD feed. S1 and S2 now share identical titer and PHB "
    "content by construction; they differ only on cost-side biology "
    "(nitrogen reduction, carbon recovery, feedstock mix). Drag titer down "
    "to 35 g/L to reproduce the v5/v6 conservative Year 1 case."
)
s1_titer = st.sidebar.slider("S1 CDW titer (g/L)", 10.0, 120.0, 60.0, 1.0, key="v5_s1_titer")
s1_yield = st.sidebar.slider("S1 biomass yield (kg CDW/kg sugar)", 0.20, 0.80, 0.50, 0.01, key="v5_s1_yield")
s1_phb = st.sidebar.slider("S1 PHB content (% CDW)", 20.0, 85.0, 60.0, 1.0, key="v5_s1_phb") / 100.0
s1_scp_cp = st.sidebar.slider("S1 SCP protein (% CP)", 50.0, 85.0, 68.0, 1.0, key="v5_s1_scp_cp") / 100.0
s1_n_reduction = st.sidebar.slider("S1 nitrogen reduction (%)", 0.0, 95.0, 50.0, 1.0, key="v5_s1_n_reduction") / 100.0
s1_carbon_recovery = st.sidebar.slider("S1 carbon recovery (%)", 70.0, 100.0, 90.0, 1.0, key="v5_s1_carbon_recovery") / 100.0

_sb_hdr("Scenario 2 Inputs")
st.sidebar.caption(
    "S2 base case locked at 60 g/L CDW, 60% PHB content, 75% nitrogen reduction, "
    "92% carbon recovery, 70% Jelly Belly COD / 30% DLP feed. Identical product "
    "slate to S1 by construction; differs from S1 on cost-side biology only."
)
s2_titer = st.sidebar.slider("S2 CDW titer (g/L)", 10.0, 120.0, 60.0, 1.0, key="v5_s2_titer")
s2_yield = st.sidebar.slider("S2 biomass yield (kg CDW/kg sugar)", 0.20, 0.80, 0.496, 0.001, key="v5_s2_yield")
s2_phb = st.sidebar.slider("S2 PHB content (% CDW)", 20.0, 85.0, 60.0, 1.0, key="v5_s2_phb") / 100.0
s2_scp_cp = st.sidebar.slider("S2 SCP protein (% CP)", 45.0, 80.0, 60.0, 1.0, key="v5_s2_scp_cp") / 100.0
s2_n_reduction = st.sidebar.slider("S2 nitrogen reduction (%)", 0.0, 98.0, 75.0, 1.0, key="v5_s2_n_reduction") / 100.0
s2_carbon_recovery = st.sidebar.slider("S2 carbon recovery (%)", 70.0, 100.0, 92.0, 1.0, key="v5_s2_carbon_recovery") / 100.0

_sb_hdr("Downstream Processing (v9)")
st.sidebar.caption(
    "Choose the DSP pathway. The two DSP cost sliders below auto-populate "
    "with pathway defaults when you switch; switching pathways resets those "
    "two sliders to the new pathway's literature-anchored defaults."
)
_pathway_ids = list(DSP_PATHWAYS.keys())
_pathway_labels = [DSP_PATHWAYS[pid]["label"] for pid in _pathway_ids]
_pathway_default_idx = _pathway_ids.index(DSP_PATHWAY_DEFAULT)
dsp_pathway_label = st.sidebar.selectbox(
    "DSP pathway",
    options=_pathway_labels,
    index=_pathway_default_idx,
    key="v9_dsp_pathway",
    help=(
        "Mechanical+enzymatic is the modern CMO standard (Kapritchkoff 2006, "
        "Jacquel 2008 review, Danimer commercial disclosures). NaOCl reproduces "
        "the v7/v8 Biopol-era baseline. NaOH is an intermediate option."
    ),
)
dsp_pathway_id = _pathway_ids[_pathway_labels.index(dsp_pathway_label)]
_pathway = DSP_PATHWAYS[dsp_pathway_id]
st.sidebar.caption(
    f"**{_pathway['label']}** \n"
    f"Mw note: {_pathway['mw_note']} \n"
    f"_{_pathway['pathway_note']}_ \n"
    f"Incremental equipment CapEx is not auto-added; bump the "
    f"'Added major CapEx' slider below if you want to model it."
)

_sb_hdr("Process + Cost Inputs")
electricity_price = st.sidebar.slider("Electricity price ($/kWh)", 0.01, 0.30, 0.12, 0.005, key="v5_electricity_price")
electricity_kwh_per_kg_cdw = st.sidebar.slider("Electricity intensity (kWh/kg CDW)", 0.20, 5.00, float(ELECTRICITY_KWH_PER_KG_CDW), 0.01, key="v5_elec_intensity")
jb_sugar_price = st.sidebar.slider("Jelly Belly sugar cost ($/kg sugar)", 0.01, 0.50, JB_SUGAR_PRICE, 0.005, key="v5_jb_sugar_price")
dlp_sugar_price = st.sidebar.slider("DLP sugar cost ($/kg sugar)", 0.01, 0.50, DLP_SUGAR_PRICE, 0.005, key="v5_dlp_sugar_price")
jb_pretreat_cost = st.sidebar.slider("Jelly Belly pretreatment ($/kg sugar)", 0.00, 0.20, JB_PRETREAT_COST, 0.001, key="v5_jb_pretreat")
dlp_pretreat_cost = st.sidebar.slider("DLP pretreatment ($/kg sugar)", 0.00, 0.10, DLP_PRETREAT_COST, 0.001, key="v5_dlp_pretreat")
steam_cost_per_kg_cdw = st.sidebar.slider("Steam / thermal cost ($/kg CDW)", 0.00, 1.00, STEAM_COST_PER_KG_CDW, 0.01, key="v5_steam_cost")
# DSP cost sliders are pathway-keyed: switching pathway rebuilds the slider
# with the pathway's default value, so the user sees the pathway's literature
# anchor immediately but retains independent state per pathway.
downstream_cost_per_kg_cdw = st.sidebar.slider(
    "Downstream cost ($/kg CDW, pathway-driven)",
    0.00, 2.00, float(_pathway["downstream_per_kg_cdw"]), 0.01,
    key=f"v9_downstream_cost_{dsp_pathway_id}",
    help="Centrifuge, drying, and non-PHA fraction handling. Default comes from the selected DSP pathway.",
)
cip_cost_per_kg_cdw = st.sidebar.slider("CIP / maintenance cost ($/kg CDW)", 0.00, 1.00, CIP_COST_PER_KG_CDW, 0.01, key="v5_cip_cost")
pha_extraction_cost_per_kg_sellable = st.sidebar.slider(
    "PHA extraction cost ($/kg sellable PHA, pathway-driven)",
    0.00, 3.00, float(_pathway["pha_extraction_per_kg_sellable"]), 0.01,
    key=f"v9_pha_extraction_{dsp_pathway_id}",
    help="Polymer-liberation step for the selected DSP pathway. Default comes from pathway literature anchors.",
)
standard_n_cost_per_kg_cdw = st.sidebar.slider("Base nitrogen cost ($/kg CDW)", 0.00, 0.50, STANDARD_N_COST_PER_KG_CDW, 0.005, key="v5_n_cost")

_sb_hdr("Labor + Market Inputs")
phase_labor = {
    "Phase I": st.sidebar.slider("Phase I labor ($/yr)", 0.10, 5.0, PHASE_FIXED_LABOR["Phase I"] / 1e6, 0.05, format="$%.2fM", key="v5_phase1_labor") * 1e6,
    "Phase II": st.sidebar.slider("Phase II labor ($/yr)", 0.10, 8.0, PHASE_FIXED_LABOR["Phase II"] / 1e6, 0.05, format="$%.2fM", key="v5_phase2_labor") * 1e6,
    "Phase III": st.sidebar.slider("Phase III labor ($/yr)", 0.10, 12.0, PHASE_FIXED_LABOR["Phase III"] / 1e6, 0.05, format="$%.2fM", key="v5_phase3_labor") * 1e6,
}
phb_standard_price = st.sidebar.slider("PHB selling price ($/kg)", 1.00, 15.0, PHA_STANDARD_PRICE, 0.10, key="v5_phb_price")
phbv_price = st.sidebar.slider("PHBV selling price ($/kg)", 1.00, 20.0, PHBV_PRICE, 0.10, key="v5_phbv_price")
phb_share = st.sidebar.slider("PHB share of PHA revenue mix (%)", 0.0, 100.0, PHA_BLEND_STANDARD_SHARE * 100.0, 1.0, key="v5_phb_share") / 100.0

_sb_hdr("PHBV Co-production (v9)")
st.sidebar.caption(
    "PHBV mode overrides the PHB/PHBV blend above. When ON, the entire PHA "
    "stream is sold as PHBV at a price that scales with HV content, and a "
    "co-substrate (propionate, valerate, or levulinate) cost line is added "
    "to the variable cost stack. When OFF, behavior matches v8."
)
phbv_enabled = st.sidebar.checkbox(
    "Enable PHBV co-production",
    value=PHBV_ENABLED_DEFAULT,
    key="v9_phbv_enabled",
)
if phbv_enabled:
    _cosub_ids = list(COSUBSTRATE_PRESETS.keys())
    _cosub_labels = [COSUBSTRATE_PRESETS[cid]["label"] for cid in _cosub_ids]
    phbv_cosubstrate_label = st.sidebar.selectbox(
        "PHBV co-substrate",
        options=_cosub_labels,
        index=0,
        key="v9_phbv_cosubstrate",
        help=(
            "Propionate is the industry default (Doi 1988, Madison-Huisman 1999). "
            "Valerate has the highest mass-efficiency but is the most expensive. "
            "Levulinate is the cheapest reagent but has lower incorporation yield."
        ),
    )
    phbv_cosubstrate_id = _cosub_ids[_cosub_labels.index(phbv_cosubstrate_label)]
    _cosub = COSUBSTRATE_PRESETS[phbv_cosubstrate_id]
    phbv_hv_mol_pct = float(st.sidebar.slider(
        "PHBV HV content (mol %)",
        min_value=2.0,
        max_value=float(_cosub["max_hv_mol_pct"]),
        value=float(_cosub["default_hv_mol_pct"]),
        step=0.5,
        key=f"v9_phbv_hv_mol_pct_{phbv_cosubstrate_id}",
        help="Incorporated 3-hydroxyvalerate on a molar basis. Higher HV content drives higher co-substrate demand and a higher market price.",
    ))
    phbv_cosubstrate_kg_per_kg_hv = float(st.sidebar.slider(
        f"{_cosub['label'].split(' (')[0]} demand (kg / kg HV incorporated)",
        min_value=1.0,
        max_value=6.0,
        value=float(_cosub["kg_per_kg_hv"]),
        step=0.1,
        key=f"v9_phbv_cosub_ratio_{phbv_cosubstrate_id}",
        help="Mass of co-substrate fed per kg of 3-HV actually incorporated into polymer. Captures both stoichiometry and respiration loss.",
    ))
    phbv_cosubstrate_price = float(st.sidebar.slider(
        f"{_cosub['label'].split(' (')[0]} cost ($/kg)",
        min_value=0.50,
        max_value=8.00,
        value=float(_cosub["price_per_kg"]),
        step=0.05,
        key=f"v9_phbv_cosub_price_{phbv_cosubstrate_id}",
    ))
    _phbv_auto = phbv_auto_price(phbv_hv_mol_pct)
    phbv_price_override = st.sidebar.checkbox(
        f"Override auto-scaled PHBV price (auto = \\${_phbv_auto:.2f}/kg at {phbv_hv_mol_pct:.1f}% HV)",
        value=False,
        key="v9_phbv_price_override",
    )
    if phbv_price_override:
        phbv_selling_price = float(st.sidebar.slider(
            "PHBV selling price — manual override ($/kg)",
            min_value=3.00, max_value=20.00, value=float(_phbv_auto), step=0.10,
            key="v9_phbv_manual_price",
        ))
    else:
        phbv_selling_price = float(_phbv_auto)
    st.sidebar.caption(
        f"**Auto-scaled PHBV price:** \\${_phbv_auto:.2f}/kg at {phbv_hv_mol_pct:.1f}% HV. "
        "Anchors: \\$5.50/kg at 5% HV, \\$7/kg at 10%, \\$9/kg at 15%, \\$12/kg at 20% "
        "(Tianan Biopolymer, Kaneka PHBH, Danimer Nodax; 2023-2025 specialty-bioplastic surveys)."
    )
else:
    phbv_cosubstrate_id = "propionate"
    phbv_hv_mol_pct = COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["default_hv_mol_pct"]
    phbv_cosubstrate_kg_per_kg_hv = COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["kg_per_kg_hv"]
    phbv_cosubstrate_price = COSUBSTRATE_PRESETS[phbv_cosubstrate_id]["price_per_kg"]
    phbv_selling_price = phbv_auto_price(phbv_hv_mol_pct)

# ── v10 human-grade SCP (HGP) ──────────────────────────────────────────────
_sb_hdr("Human-grade SCP (v10)")
st.sidebar.caption(
    "HGP mode re-prices and re-costs the non-PHA fraction of CDW as human-grade "
    "whole-cell protein mash instead of feed-grade SCP. When OFF, the model "
    "behaves exactly like v9. Regulatory caveat: _C. necator_ H16 has a mixed "
    "regulatory footprint (EFSA QPS \"production purposes only\"; PHA polymer "
    "holds FDA FCNs including Kaneka FCN 1835) but the biomass itself does not "
    "hold a US GRAS notice or an EFSA Novel Food authorisation as a food "
    "ingredient. Solar Foods' Solein (a _Xanthobacter_-group organism, not "
    "_C. necator_) holds Singapore novel-food approval (2022) and US "
    "self-affirmed GRAS (2024); these clearances do not extend to a new "
    "_C. necator_ HGP. US GRAS / EFSA Novel Food dossiers run 2-3 years once "
    "toxicology, allergenicity, and compositional packages are in hand. Treat "
    "HGP economics as pro-forma pending that clearance."
)
hgp_enabled = st.sidebar.checkbox(
    "Enable human-grade SCP (HGP)",
    value=HGP_ENABLED_DEFAULT,
    key="v10_hgp_enabled",
)
if hgp_enabled:
    hgp_mode_labels = {
        "coproduction": "Co-production with polymer (PHA retained)",
        "alone": "HGP alone (minimize PHA, N-replete growth)",
    }
    hgp_mode_ids = list(hgp_mode_labels.keys())
    _hgp_mode_label = st.sidebar.radio(
        "HGP production mode",
        options=[hgp_mode_labels[mid] for mid in hgp_mode_ids],
        index=0,
        key="v10_hgp_production_mode",
        help=(
            "Co-production keeps the PHA stream (and PHBV if enabled) unchanged "
            "from v9; the non-PHA fraction of CDW is simply sold as HGP. "
            "HGP-alone operates the fermenter N-replete to suppress PHA "
            "accumulation; PHB content is forced to a basal level (~8%) and "
            "~92% of CDW is sold as HGP."
        ),
    )
    hgp_production_mode = hgp_mode_ids[[hgp_mode_labels[mid] for mid in hgp_mode_ids].index(_hgp_mode_label)]
    hgp_selling_price = float(st.sidebar.slider(
        "HGP selling price ($/kg)",
        min_value=3.00, max_value=12.00,
        value=HGP_SELLING_PRICE_DEFAULT, step=0.10,
        key="v10_hgp_selling_price",
        help=(
            "Mid-band default $8/kg. Anchors: ingredient-grade mycoprotein (Quorn) "
            "$6-10/kg per 2024-25 food-ingredient trade surveys (Finnigan 2019 is "
            "the nutritional-profile reference, not a price source); Solar Foods "
            "Solein single-digit USD/kg dry-protein production-cost target at "
            "Factory 01 scale; Ritala 2017 bacterial-SCP review. Calysta FeedKind "
            "is feed-grade only and is NOT used as an HGP-price anchor."
        ),
    ))
    hgp_dsp_cost_per_kg = float(st.sidebar.slider(
        "HGP DSP cost ($/kg HGP)",
        min_value=0.50, max_value=5.00,
        value=HGP_DSP_COST_PER_KG_DEFAULT, step=0.05,
        key="v10_hgp_dsp_cost",
        help=(
            "Internal bottom-up engineering estimate for a spray-dried whole-cell "
            "mash flowsheet. Decomposition: endotoxin (LPS) removal via thermal "
            "inactivation + TFF (~$1.05/kg HGP) + food-grade spray drying and "
            "sanitary packaging (~$0.50/kg HGP) + release QA / regulatory overhead "
            "($0.20-0.40/kg). Default $1.80/kg is the mid-case."
        ),
    ))
    hgp_recovery_frac = float(st.sidebar.slider(
        "HGP whole-cell recovery (fraction of non-PHA CDW)",
        min_value=0.60, max_value=0.95,
        value=HGP_RECOVERY_FRAC_DEFAULT, step=0.01,
        key="v10_hgp_recovery",
        help=(
            "Spray-dried whole-cell mash (Quorn / Solein style) recovers 80-90% of "
            "the non-PHA CDW. Feed-grade pelletized SCP is ~78% for reference. "
            "Lower values reflect tighter endotoxin / QA specs."
        ),
    ))
    hgp_cp_frac = float(st.sidebar.slider(
        "HGP crude-protein content (fraction)",
        min_value=0.45, max_value=0.75,
        value=HGP_CP_DEFAULT, step=0.01,
        key="v10_hgp_cp",
        help=(
            "Whole-cell bacterial SCP typically assays 55-75% crude protein "
            "(Ritala 2017 review of bacterial / single-cell protein). Displayed "
            "for spec transparency; does not directly feed the revenue math "
            "because pricing is per kg of mash sold."
        ),
    ))
    if hgp_production_mode == "alone":
        hgp_alone_phb_frac = float(st.sidebar.slider(
            "HGP-alone residual PHB content (fraction)",
            min_value=0.00, max_value=0.15,
            value=HGP_ALONE_PHB_FRAC_DEFAULT, step=0.01,
            key="v10_hgp_alone_phb",
            help=(
                "Default 0% assumes a phaCAB knockout strain: deletion of the PHB "
                "synthase (phaC) in C. necator H16 abolishes PHA accumulation "
                "entirely (polymer-negative phenotype reported by Slater 1988 and "
                "Peoples & Sinskey 1989; phaCAB operon mapped in Pohlmann 2006). "
                "Raise the slider to model the wild-type N-replete case where basal "
                "PHA accumulates to 5-15% of CDW even without deliberate "
                "N-limitation (Braunegg 1998, Khanna 2005)."
            ),
        ))
    else:
        hgp_alone_phb_frac = HGP_ALONE_PHB_FRAC_DEFAULT
    st.sidebar.caption(
        f"**HGP base case:** \\${hgp_selling_price:.2f}/kg selling price, "
        f"\\${hgp_dsp_cost_per_kg:.2f}/kg DSP, {hgp_recovery_frac * 100:.0f}% "
        f"recovery, {hgp_cp_frac * 100:.0f}% crude protein. "
        "Facility CapEx for the HGP retrofit (endotoxin skid, sanitary spray drier, "
        "GFSI compliance) is **not** auto-added; users who want to stress-test "
        "the food-grade retrofit should bump the 'Added major CapEx' slider by a "
        "literature-anchored \\$8-15M at Phase III."
    )
else:
    hgp_production_mode = HGP_PRODUCTION_MODE_DEFAULT
    hgp_selling_price = HGP_SELLING_PRICE_DEFAULT
    hgp_dsp_cost_per_kg = HGP_DSP_COST_PER_KG_DEFAULT
    hgp_recovery_frac = HGP_RECOVERY_FRAC_DEFAULT
    hgp_cp_frac = HGP_CP_DEFAULT
    hgp_alone_phb_frac = HGP_ALONE_PHB_FRAC_DEFAULT

scp_target_price = st.sidebar.slider(
    "Feed-grade SCP selling price ($/kg)",
    0.30, 8.00, SCP_TARGET_PRICE, 0.05,
    key="v5_scp_price",
)
st.sidebar.caption(
    "**Market price, not MSP.** Default \\$2.00/kg is the upper end of the "
    "feed-grade bacterial-SCP benchmark band: fishmeal \\$1.45-1.79/kg (FRED "
    "PFISHUSDM 2024-2025), Calysta FeedKind \\$1.50-2.00/kg (Rabobank / "
    "Aquafeed), Unibio UniProtein ~\\$2.00/kg. The MSP reported above is the "
    "project's computed cost floor; market price minus MSP is the operating "
    "margin per kg of SCP sold."
)
scp_credit_price = st.sidebar.slider("SCP credit price for PHA MSP ($/kg)", 0.10, 5.00, SCP_CREDIT_PRICE, 0.01, key="v5_scp_credit")
discount_rate = st.sidebar.slider("Discount rate (%)", 1.0, 30.0, DISCOUNT_RATE * 100.0, 1.0, key="v5_discount_rate") / 100.0
npv_years = int(st.sidebar.slider("NPV / IRR horizon (years)", 3, 30, NPV_YEARS, 1, key="v5_npv_years"))

scenario_overrides = {
    "S1": {
        "titer_gL": s1_titer,
        "yield_kg_per_kg_sugar": s1_yield,
        "phb_content_frac": s1_phb,
        "scp_protein_frac": s1_scp_cp,
        "n_reduction_frac": s1_n_reduction,
        "carbon_recovery_frac": s1_carbon_recovery,
        "jb_sugar_price": jb_sugar_price,
        "jb_pretreat_cost": jb_pretreat_cost,
    },
    "S2": {
        "titer_gL": s2_titer,
        "yield_kg_per_kg_sugar": s2_yield,
        "phb_content_frac": s2_phb,
        "scp_protein_frac": s2_scp_cp,
        "n_reduction_frac": s2_n_reduction,
        "carbon_recovery_frac": s2_carbon_recovery,
        "jb_sugar_price": jb_sugar_price,
        "dlp_sugar_price": dlp_sugar_price,
        "jb_pretreat_cost": jb_pretreat_cost,
        "dlp_pretreat_cost": dlp_pretreat_cost,
    },
}
s1_titer_eff = s1_titer
s2_titer_eff = s2_titer
s1_phb_eff = s1_phb
s2_phb_eff = s2_phb

# v10: HGP-alone mode forces PHB content to a basal level in the engine.
# Mirror that override into scenario_overrides so the guardrail check and
# the facility panel both see the effective PHB, not the slider's value.
if hgp_enabled and hgp_production_mode == "alone":
    for sid in ("S1", "S2"):
        scenario_overrides[sid]["phb_content_frac"] = float(hgp_alone_phb_frac)
    s1_phb_eff = float(hgp_alone_phb_frac)
    s2_phb_eff = float(hgp_alone_phb_frac)

common_overrides = {
    "electricity_price": electricity_price,
    "electricity_kwh_per_kg_cdw": electricity_kwh_per_kg_cdw,
    "steam_cost_per_kg_cdw": steam_cost_per_kg_cdw,
    "downstream_cost_per_kg_cdw": downstream_cost_per_kg_cdw,
    "cip_cost_per_kg_cdw": cip_cost_per_kg_cdw,
    "pha_extraction_cost_per_kg_sellable": pha_extraction_cost_per_kg_sellable,
    "standard_n_cost_per_kg_cdw": standard_n_cost_per_kg_cdw,
    "pha_blended_price": phb_standard_price * phb_share + phbv_price * (1.0 - phb_share),
    "scp_target_price": scp_target_price,
    "scp_credit_price": scp_credit_price,
    "discount_rate": discount_rate,
    "npv_years": float(npv_years),
    # Operating-mode pass-through (UI is continuous-only; defaults retained for engine compatibility)
    "operating_mode": operating_mode,
    "cycle_h": FED_BATCH_CYCLE_H_DEFAULT,
    "duty_cycle_frac": FED_BATCH_DUTY_FRAC_DEFAULT,
    "otr_retrofit_capex": 0.0,
    # v9 DSP pathway pass-through
    "dsp_pathway_id": dsp_pathway_id,
    # v9 PHBV co-production pass-through
    "phbv_enabled": bool(phbv_enabled),
    "phbv_cosubstrate_id": phbv_cosubstrate_id,
    "phbv_hv_mol_pct": float(phbv_hv_mol_pct),
    "phbv_cosubstrate_kg_per_kg_hv": float(phbv_cosubstrate_kg_per_kg_hv),
    "phbv_cosubstrate_price": float(phbv_cosubstrate_price),
    "phbv_selling_price": float(phbv_selling_price),
    # v10 human-grade SCP (HGP) pass-through
    "hgp_enabled": bool(hgp_enabled),
    "hgp_production_mode": hgp_production_mode,
    "hgp_selling_price": float(hgp_selling_price),
    "hgp_dsp_cost_per_kg": float(hgp_dsp_cost_per_kg),
    "hgp_recovery_frac": float(hgp_recovery_frac),
    "hgp_cp_frac": float(hgp_cp_frac),
    "hgp_alone_phb_frac": float(hgp_alone_phb_frac),
}
pha_blended_price = common_overrides["pha_blended_price"]
base_overrides_by_scenario = {
    scenario_id: {
        **common_overrides,
        **scenario_overrides[scenario_id],
        "labor_cost": phase_labor[focus_phase],
    }
    for scenario_id in FAIRFIELD_SCENARIOS
}

results: List[FairfieldResult] = []
for phase, util_pct in phase_utils.items():
    for scenario in FAIRFIELD_SCENARIOS.values():
        overrides = dict(common_overrides)
        overrides.update(scenario_overrides[scenario.id])
        overrides["labor_cost"] = phase_labor[phase]
        results.append(_fairfield_single_result(phase, util_pct, scenario, acquisition_cost, added_major_capex, overrides))

focus = _fairfield_result(results, focus_phase, focus_scenario_id)
guardrail_warnings = _fairfield_guardrail_warnings(
    phase_utils,
    scenario_overrides["S1"],
    scenario_overrides["S2"],
    {
        "electricity_price": electricity_price,
        "electricity_kwh_per_kg_cdw": electricity_kwh_per_kg_cdw,
        "jb_sugar_price": jb_sugar_price,
        "dlp_sugar_price": dlp_sugar_price,
        "jb_pretreat_cost": jb_pretreat_cost,
        "dlp_pretreat_cost": dlp_pretreat_cost,
    },
    {
        "discount_rate": discount_rate,
        "npv_years": float(npv_years),
    },
    operating_mode=operating_mode,
    hgp_alone=bool(hgp_enabled and hgp_production_mode == "alone"),
)

# v10 HGP banner: surface the regulatory-pro-forma caveat on the main page
# whenever HGP is enabled, so the reader is not misled into comparing HGP
# headline economics to a feed-grade reference case without context.
if hgp_enabled:
    _hgp_mode_text = (
        "Co-production with polymer — PHA stream retained, non-PHA CDW sold as HGP."
        if hgp_production_mode == "coproduction"
        else (
            f"HGP alone — phaCAB knockout strain (residual PHB {hgp_alone_phb_frac*100:.0f}%), "
            "N-replete fermentation; ~100% of CDW sold as HGP when KO is complete."
        )
    )
    st.info(
        "**Note: human-grade SCP (HGP) mode is ON (v10).** "
        f"{_hgp_mode_text} "
        f"HGP is priced at \\${hgp_selling_price:.2f}/kg with an incremental DSP cost of "
        f"\\${hgp_dsp_cost_per_kg:.2f}/kg HGP (endotoxin removal + food-grade spray drying + QA). "
        "**Regulatory status:** _C. necator_ H16 has a mixed regulatory "
        "footprint rather than a blanket clearance. The organism sits on the "
        "EFSA Qualified Presumption of Safety (QPS) list with the "
        "qualification \"production purposes only\" (it is accepted as a "
        "production host where viable cells do not reach the finished "
        "product), and PHA polymer produced from _C. necator_ H16 holds "
        "multiple FDA Food Contact Notifications (e.g. Kaneka FCN 1835 on "
        "P(3HB-co-3HHx)). Neither the QPS listing nor the FCNs cover use of "
        "the biomass as a food ingredient. The biomass itself does not hold "
        "an FDA GRAS notice or an EFSA Novel Food authorisation in any "
        "major market as of the model date. The closest commercial "
        "precedent, Solar Foods' Solein, is produced from a "
        "_Xanthobacter_-group organism (not _C. necator_) and holds "
        "Singapore novel-food approval (2022) and US self-affirmed GRAS "
        "(2024); its EFSA Novel Food dossier is in progress. A "
        "C. necator-biomass HGP product would require its own GRAS "
        "notification (or self-affirmed GRAS) in the US, or an EFSA Novel "
        "Food authorisation in the EU, each a 2-3 year process once the "
        "toxicology, allergenicity, and compositional dossiers are in "
        "hand. **Treat HGP headline economics as pro-forma pending that "
        "clearance.** "
        "Food-grade facility retrofit CapEx (endotoxin skid, sanitary "
        "spray drier, GFSI compliance; internal estimate \\$8-15M at "
        "Phase III) is **not** auto-added; bump the **Added major CapEx** "
        "slider to stress-test it."
    )

# Default-settings note: call out the v9 vs v8/v7 difference in the DSP flowsheet
# so that headline numbers in the app (under v9 defaults) are reconciled against
# figures in the existing memo/investor report (which were generated under the
# v7/v8 NaOCl baseline).
if dsp_pathway_id == DSP_PATHWAY_DEFAULT and not phbv_enabled and not hgp_enabled:
    st.info(
        "**Note — headline numbers are slightly better than the current memo / TEA report.** "
        "The default downstream-processing flowsheet has been upgraded from "
        "**NaOCl hypochlorite digestion** (the Biopol-era method used in the "
        "memo and report) to **mechanical + enzymatic recovery** "
        "(high-pressure homogenization + protease / lipase polishing — the standard "
        "flowsheet at modern CMO scale). Impact at Phase III:\n\n"
        "- PHA minimum selling price (with SCP credit): **\\~\\$2.60/kg → \\~\\$2.00/kg** (about \\$0.60/kg lower).\n"
        "- Annual DSP operating cost: **\\~\\$5.0M → \\~\\$2.9M** (about \\$2.1M lower per year).\n"
        "- Net Phase III NPV is roughly **\\$13M higher** per scenario from the opex savings.\n\n"
        "Incremental equipment for the upgraded flowsheet (homogenization skid + "
        "polishing reactor) is **not** auto-added as CapEx; if you want to model "
        "that retrofit cost, increase the **Added major CapEx** slider accordingly. "
        "To reproduce the memo/report numbers exactly, switch the DSP pathway "
        "in the sidebar to **NaOCl hypochlorite (Biopol-era baseline)**."
    )

with st.expander("Fairfield Facility + Scenario Basis", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            (
                f"<div style='line-height:1.7;'>"
                f"<div><strong>Facility:</strong> Former AB InBev brewery, 3101 Busch Drive, Fairfield CA</div>"
                f"<div><strong>Installed phases:</strong> 50,000 L / 150,000 L / 400,000 L</div>"
                f"<div><strong>Mode:</strong> Continuous, 24 h HRT, 85% uptime</div>"
                f"<div><strong>Electricity:</strong> ${electricity_price:.3f}/kWh</div>"
                f"<div><strong>Strain:</strong> C. necator NCIMB 11599</div>"
                f"<div><strong>Acquisition:</strong> ${acquisition_cost/1e6:.1f}M</div>"
                f"<div><strong>Added major CapEx:</strong> ${added_major_capex/1e6:.1f}M</div>"
                f"<div><strong>DSP pathway (v9):</strong> {DSP_PATHWAYS[dsp_pathway_id]['label']} "
                f"(extraction ${pha_extraction_cost_per_kg_sellable:.3f}/kg PHA, "
                f"downstream ${downstream_cost_per_kg_cdw:.3f}/kg CDW; "
                f"incremental equipment CapEx not auto-added)</div>"
                f"<div><strong>Annualized CapEx:</strong> ${(focus.annual_major_capex)/1e6:.2f}M/yr at {discount_rate:.0%}, {npv_years} yr</div>"
                f"</div>"
            ),
            unsafe_allow_html=True,
        )
    with c2:
        if phbv_enabled:
            pha_revenue_line = (
                f"<div><strong>PHA revenue basis (v9 PHBV ON):</strong> "
                f"100% PHBV at <strong>${phbv_selling_price:.2f}/kg</strong> "
                f"({phbv_hv_mol_pct:.1f} mol% HV, {COSUBSTRATE_PRESETS[phbv_cosubstrate_id]['label'].split(' (')[0]} "
                f"co-feed at {phbv_cosubstrate_kg_per_kg_hv:.1f} kg/kg HV × ${phbv_cosubstrate_price:.2f}/kg)</div>"
            )
        else:
            pha_revenue_line = (
                f"<div><strong>PHA revenue basis (PHBV OFF):</strong> "
                f"{phb_share*100:.0f}% PHB @ ${phb_standard_price:.2f}/kg + "
                f"{(1.0-phb_share)*100:.0f}% PHBV @ ${phbv_price:.2f}/kg = "
                f"<strong>${common_overrides['pha_blended_price']:.2f}/kg</strong></div>"
            )
        # Effective PHB content line reflects HGP-alone override of the
        # per-scenario PHB slider values, so the displayed product slate
        # matches the engine output.
        if hgp_enabled and hgp_production_mode == "alone":
            s1_phb_display = float(hgp_alone_phb_frac)
            s2_phb_display = float(hgp_alone_phb_frac)
        else:
            s1_phb_display = s1_phb_eff
            s2_phb_display = s2_phb_eff

        if hgp_enabled:
            non_pha_product_line = (
                f"<div><strong>HGP selling price (v10):</strong> ${hgp_selling_price:.2f}/kg "
                f"({hgp_recovery_frac*100:.0f}% whole-cell recovery, "
                f"{hgp_cp_frac*100:.0f}% crude protein, "
                f"${hgp_dsp_cost_per_kg:.2f}/kg HGP DSP)</div>"
                f"<div><strong>HGP production mode:</strong> "
                f"{'Co-production with polymer' if hgp_production_mode == 'coproduction' else ('HGP alone, phaCAB KO (residual PHB ' + f'{hgp_alone_phb_frac*100:.0f}%)')}</div>"
                f"<div><strong>PHA MSP credit basis:</strong> HGP at ${hgp_selling_price:.2f}/kg (v10 override)</div>"
            )
        else:
            non_pha_product_line = (
                f"<div><strong>SCP target price:</strong> ${scp_target_price:.2f}/kg</div>"
                f"<div><strong>SCP credit for PHA MSP:</strong> ${scp_credit_price:.2f}/kg</div>"
            )

        st.markdown(
            (
                f"<div style='line-height:1.7;'>"
                f"<div><strong>Scenario 1:</strong> 100% Jelly Belly COD, yield {s1_yield:.3f} kg/kg, {s1_titer_eff:.1f} g/L, {s1_phb_display*100:.0f}% PHB, {s1_scp_cp*100:.0f}% SCP CP</div>"
                f"<div><strong>Scenario 2:</strong> 70/30 Jelly Belly COD/DLP, yield {s2_yield:.3f} kg/kg, {s2_titer_eff:.1f} g/L, {s2_phb_display*100:.0f}% PHB, {s2_scp_cp*100:.0f}% SCP CP</div>"
                + non_pha_product_line
                + pha_revenue_line +
                f"<div><strong>Scenario 3:</strong> Narrative upside only, not modeled in v10</div>"
                f"</div>"
            ),
            unsafe_allow_html=True,
        )

_section("Selected Operating Point")
st.caption(
    f"Detailed view is currently centered on `{focus_phase}` / `{focus_scenario_id}`. "
    "All phases and both modeled scenarios are still calculated in the table and multi-case figures below."
)
st.caption(
    f"Throughput basis (continuous): {focus.vessel_volume_L:,.0f} L installed × "
    f"{focus.utilization_pct:.0f}% utilization = {focus.active_volume_L:,.0f} L "
    f"utilized broth volume; annual CDW uses {_annual_operating_cycles():.2f} "
    f"operating turnover-equivalents/year (24 h HRT with 85% uptime)."
)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Scenario", focus.scenario_id)
c2.metric("Phase", focus.phase)
c3.metric("CDW (t/y)", f"{focus.annual_cdw_tpy:,.0f}")
_pha_msp_display = (
    "N/A (no polymer)"
    if not np.isfinite(focus.pha_msp_with_scp_credit)
    else f"${focus.pha_msp_with_scp_credit:.2f}/kg"
)
c4.metric("PHA MSP w/ SCP", _pha_msp_display)
c5.metric("NPV", f"${focus.npv/1e6:,.1f}M")
c6.metric("IRR", f"{focus.irr*100:,.1f}%" if np.isfinite(focus.irr) else "n/a")

c7, c8, c9, c10 = st.columns(4)
c7.metric("Utilized volume", f"{focus.active_volume_L:,.0f} L")
c8.metric("PHA output", f"{focus.annual_pha_kg/1e3:,.0f} t/y")
c9.metric("SCP output", f"{focus.annual_scp_kg/1e3:,.0f} t/y")
c10.metric("Cash flow", f"${focus.annual_cash_flow/1e6:,.2f}M/yr")

_section("Fairfield Notes")
st.info(
    "This v5 dashboard is Fairfield-only. It excludes autotrophic H2/CO2, HFCS-90 fructose, molasses, and standard whey permeate. "
    "The only modeled feedstock paths are Scenario 1 Jelly Belly COD and Scenario 2 70/30 Jelly Belly COD + DLP."
)
if guardrail_warnings:
    for msg in guardrail_warnings:
        st.warning(msg.replace("$", r"\$"), icon="⚠️")
else:
    st.success("All Fairfield-controlled inputs are inside the current recommended planning bands.", icon="✅")
st.warning(
    "Open data item: Jelly Belly COD sugar composition is still estimated from published confectionary formulas. "
    "The feedstock sensitivity figure applies a ±20% band to feedstock + pretreatment cost to reflect that uncertainty."
)
st.info(
    "Annual throughput uses the continuous roll-up: utilized broth volume × titer × "
    "(8,760 h/year × 85% uptime ÷ 24 h HRT). At the v7/v8 locked 60 g/L continuous "
    "base case, Phase III S1 at 90% utilization gives ~6,701 t/y CDW. At the v5/v6 "
    "35 g/L conservative case, the same configuration gives ~3,909 t/y CDW. "
    "The site handoff (Fairfield_TEA_v7_Final.pdf, page 7) states ~10,700 t/y "
    "for the 35 g/L case, which does not match its own formula "
    "(306,000 L × 35 g/L × 8,760/24 ÷ 1e6 = 3,909 t/y). The v8 TEA does not "
    "inherit that defect because it computes CDW from first principles."
)

_section("Phase + Scenario Table")
rows = _fairfield_rows(results)
st.dataframe(rows, use_container_width=True)
if rows:
    csv = "\n".join([",".join(rows[0].keys())] + [",".join(str(v) for v in row.values()) for row in rows]).encode()
    st.download_button("Download Fairfield v5 CSV", data=csv, file_name="fairfield_v5_results.csv", mime="text/csv")

_section("Figures")
# v10 Revision 3: dropdown is ordered by narrative importance for an
# investor reading the report. The top five figures are the headline
# story (mode comparison, product slate, scenario comparison, HGP price,
# unit economics); the next four are phase-specific decomposition
# (waterfall, DSP stack, full cost structure, discounted cash flow);
# the final four are scale and sensitivity.
fig_opts = {
    "Phase III Headline (v10, three modes)": lambda: fig_v10_phase3_headline(
        common_overrides, scenario_overrides, acquisition_cost, added_major_capex,
    ),
    "Product Slate by Mode (Phase III)": lambda: fig_v10_mass_flow_phase3(
        common_overrides, scenario_overrides, acquisition_cost, added_major_capex,
    ),
    "S1 vs S2 Across Phases": lambda: fig_v9_s1_s2_across_phases(
        results,
        scp_target_price=scp_target_price,
        discount_rate=discount_rate,
        npv_years=npv_years,
        operating_mode=operating_mode,
        dsp_pathway_label=DSP_PATHWAYS[dsp_pathway_id]["label"],
        phbv_enabled=bool(phbv_enabled),
        phbv_hv_mol_pct=float(phbv_hv_mol_pct),
    ),
    "HGP Price Sensitivity": lambda: fig_v10_hgp_price_sensitivity(
        common_overrides, scenario_overrides, acquisition_cost, added_major_capex,
    ),
    "MSP and Cash Flow": lambda: fig_v5_msp_and_cash(results),
    "NPV vs Selling Price": lambda: fig_v5_npv_vs_price(results, focus_phase, scp_target_price, pha_blended_price, discount_rate, npv_years),
    "IRR vs Selling Price": lambda: fig_v5_irr_vs_price(results, focus_phase, scp_target_price, pha_blended_price, npv_years),
    "P&L Waterfall": lambda: fig_v5_waterfall(results, focus_phase, focus_scenario_id),
    "DSP Cost Stack": lambda: fig_v10_dsp_stack(float(hgp_dsp_cost_per_kg)),
    "Cost Structure": lambda: fig_v5_cost_structure(results, focus_phase, focus_scenario_id),
    "Discounted Cash Flow": lambda: fig_v5_discounted_cf(results, focus_phase, focus_scenario_id, discount_rate, npv_years),
    "Phase Output": lambda: fig_v5_outputs(results),
    "Returns by Phase": lambda: fig_v5_returns(results),
    "Feedstock Sensitivity": lambda: fig_v5_feedstock_sensitivity(results, focus_phase, scp_credit_price),
    "OAT Sensitivity": lambda: fig_v5_oat_sensitivity(
        results, focus_phase, focus_scenario_id, acquisition_cost, added_major_capex,
        base_overrides_by_scenario[focus_scenario_id]
    ),
}
sel_fig = st.selectbox("Select Fairfield figure", list(fig_opts.keys()), key="v5_sel_fig")
formula_text = V5_FIGURE_FORMULAS.get(sel_fig)
if formula_text:
    with st.expander("How is this figure calculated?"):
        st.markdown(formula_text.replace("$", r"\$"))
st.markdown('<div class="fig-frame">', unsafe_allow_html=True)
fig = fig_opts[sel_fig]()
st.pyplot(fig, use_container_width=True)
plt.close(fig)
st.markdown("</div>", unsafe_allow_html=True)

_section("Break-Even Analysis")
_be_info = _breakeven_decomposition(
    focus_phase, focus_scenario_id, base_overrides_by_scenario[focus_scenario_id],
    acquisition_cost, added_major_capex,
)
_be_base = _be_info["base_result"]
_be_cdw_tpy = _be_info["be_cdw_kg"] / 1000.0 if _be_info["be_cdw_kg"] == _be_info["be_cdw_kg"] else float("nan")
_active_cdw_tpy = _be_base.annual_cdw_tpy
_margin_of_safety = (
    (_active_cdw_tpy - _be_cdw_tpy) / _active_cdw_tpy * 100.0
    if _active_cdw_tpy > 0 and _be_cdw_tpy == _be_cdw_tpy else float("nan")
)
st.info(
    f"At active settings ({focus_phase} / {focus_scenario_id}, {_be_base.titer_gL:.1f} g/L CDW, "
    f"{_be_base.utilization_pct:.0f}% utilization), each kg of CDW generates "
    f"\\${_be_info['rev_per_cdw']:.2f} of revenue against \\${_be_info['var_per_cdw']:.2f} of variable cost, "
    f"for a contribution margin of \\${_be_info['margin_per_cdw']:.2f}/kg. "
    f"Fixed labor is \\${_be_info['labor']/1e6:.2f}M/yr. "
    f"Cash break-even requires {_be_cdw_tpy:,.0f} t/y CDW "
    f"(≈ {_be_info['be_titer_gL']:.1f} g/L at current utilization, or "
    f"{_be_info['be_util_pct']:.1f}% utilization at current titer). "
    f"Active case produces {_active_cdw_tpy:,.0f} t/y — a {_margin_of_safety:.0f}% margin of safety."
)
be_tab_names = ["P&L Waterfall", "Revenue vs OpEx", "Cash flow vs Titer", "Cash flow vs Utilization"]
be_tabs = st.tabs(be_tab_names)
with be_tabs[0]:
    st.caption(
        "Annual P&L decomposition at the current focus phase and scenario. "
        "Green = revenue; red = cost buckets; blue = residual annual cash flow. "
        "Updates live with sidebar changes."
    )
    _fig_be = fig_v5_waterfall(results, focus_phase, focus_scenario_id)
    st.pyplot(_fig_be, use_container_width=True)
    plt.close(_fig_be)
with be_tabs[1]:
    st.caption(
        "Annual revenue vs. annual cash OpEx as CDW titer sweeps 10–80 g/L, holding all other "
        "active settings constant. The crossover is the titer at which revenue exactly covers "
        "cash operating costs."
    )
    _fig_be = fig_v5_revenue_vs_opex(
        focus_phase, focus_scenario_id,
        base_overrides_by_scenario[focus_scenario_id],
        acquisition_cost, added_major_capex,
    )
    st.pyplot(_fig_be, use_container_width=True)
    plt.close(_fig_be)
with be_tabs[2]:
    st.caption(
        "Annual cash flow as CDW titer sweeps 0–80 g/L, at the currently selected utilization. "
        "Dotted red line is cash break-even; the dark line marks the active titer."
    )
    _fig_be = fig_v5_breakeven_titer(
        focus_phase, focus_scenario_id,
        base_overrides_by_scenario[focus_scenario_id],
        acquisition_cost, added_major_capex,
    )
    st.pyplot(_fig_be, use_container_width=True)
    plt.close(_fig_be)
with be_tabs[3]:
    st.caption(
        "Annual cash flow as utilization sweeps 0–100%, at the currently selected CDW titer. "
        "Dotted red line is cash break-even; the dark line marks the active utilization."
    )
    _fig_be = fig_v5_breakeven_util(
        focus_phase, focus_scenario_id,
        base_overrides_by_scenario[focus_scenario_id],
        acquisition_cost, added_major_capex,
    )
    st.pyplot(_fig_be, use_container_width=True)
    plt.close(_fig_be)

_section("Reference Trace")
st.markdown("- `Fairfield_TEA_v7_Final.pdf`: primary locked Fairfield handoff used for facility, phase sizes, continuous-mode assumptions, Scenario 1 and 2 definitions, and target pricing.")
st.markdown("- [Orita et al. 2012](https://doi.org/10.1016/j.jbiosc.2011.09.010): NCIMB 11599 glucose-utilizing phenotype and equivalence to H16 on fructose.")
st.markdown("- [PubMed 40669633](https://pubmed.ncbi.nlm.nih.gov/40669633/): retained as prior-session support for dairy-side feedstock framing where the new handoff did not fully override it.")
st.markdown("- [NREL electrolysis overview](https://www.nrel.gov/hydrogen/electrolysis.html): retained as historical v4 reference only; **not used in v5 economics** because Fairfield excludes H2/CO2 fermentation and electrolyzer CapEx.")
st.markdown("- **High-cell-density literature (Kim / Ryu / Budde):**")
st.markdown("  - [Kim et al. 1994 — Biotechnol. Bioeng. 43(9):892-898](https://doi.org/10.1002/bit.260430908): glucose fed-batch of _A. eutrophus_ with on-line glucose control; 121 g/L CDW, 76% PHB.")
st.markdown("  - [Ryu et al. 1997 — Biotechnol. Bioeng. 55(1):28-32](https://doi.org/10.1002/(SICI)1097-0290(19970705)55:1%3C28::AID-BIT4%3E3.0.CO;2-Z): phosphate-limited fed-batch of _A. eutrophus_; 281 g/L CDW, 232 g/L PHB.")
st.markdown("  - [Budde et al. 2011 — Appl. Environ. Microbiol. 77(9):2847-2854](https://doi.org/10.1128/AEM.02429-10): engineered _R. eutropha_ P(HB-co-HHx) fed-batch at lab and pilot scale; 100-160 g/L / 60-70% PHB at pilot to commercial vessel scale.")
st.markdown("- Existing v4 / source-model assumptions are used only where the Fairfield handoff did not provide a more specific value.")

with st.expander("Scenario 3 narrative only"):
    st.markdown(
        "Scenario 3 remains an upside sensitivity only in v5. It is **not modeled**. "
        "The dashboard assumes bankable operation on NCIMB 11599 + invertase today, with Scenario 2 as the near-term DLP-assisted improvement path."
    )

sidebar_snapshot = {
    "phase_utils": phase_utils,
    "acquisition_cost_musd": round(acquisition_cost / 1e6, 3),
    "added_major_capex_musd": round(added_major_capex / 1e6, 3),
    "s1_titer_gL": s1_titer,
    "s2_titer_gL": s2_titer,
    "s1_yield": s1_yield,
    "s2_yield": s2_yield,
    "electricity_price": electricity_price,
    "jb_sugar_price": jb_sugar_price,
    "dlp_sugar_price": dlp_sugar_price,
    "labor_musd": {k: round(v / 1e6, 3) for k, v in phase_labor.items()},
    "pha_blended_price": round(pha_blended_price, 3),
    "scp_target_price": scp_target_price,
    "scp_credit_price": scp_credit_price,
    "discount_rate": discount_rate,
    "npv_years": npv_years,
    "operating_mode": operating_mode,
    # v9 DSP + PHBV snapshot
    "dsp_pathway_id": dsp_pathway_id,
    "dsp_pathway_label": DSP_PATHWAYS[dsp_pathway_id]["label"],
    "dsp_pathway_phase3_capex_musd": round(DSP_PATHWAYS[dsp_pathway_id]["phase3_capex"] / 1e6, 3),
    "phbv_enabled": bool(phbv_enabled),
    "phbv_cosubstrate_id": phbv_cosubstrate_id if phbv_enabled else None,
    "phbv_hv_mol_pct": round(float(phbv_hv_mol_pct), 2) if phbv_enabled else None,
    "phbv_cosubstrate_kg_per_kg_hv": round(float(phbv_cosubstrate_kg_per_kg_hv), 3) if phbv_enabled else None,
    "phbv_cosubstrate_price_per_kg": round(float(phbv_cosubstrate_price), 3) if phbv_enabled else None,
    "phbv_selling_price_per_kg": round(float(phbv_selling_price), 3) if phbv_enabled else None,
    # v10 HGP snapshot
    "hgp_enabled": bool(hgp_enabled),
    "hgp_production_mode": hgp_production_mode if hgp_enabled else None,
    "hgp_selling_price_per_kg": round(float(hgp_selling_price), 3) if hgp_enabled else None,
    "hgp_dsp_cost_per_kg": round(float(hgp_dsp_cost_per_kg), 3) if hgp_enabled else None,
    "hgp_recovery_frac": round(float(hgp_recovery_frac), 3) if hgp_enabled else None,
    "hgp_cp_frac": round(float(hgp_cp_frac), 3) if hgp_enabled else None,
    "hgp_alone_phb_frac": round(float(hgp_alone_phb_frac), 3) if (hgp_enabled and hgp_production_mode == "alone") else None,
}
render_v5_chat(results, focus_phase, focus_scenario_id, sidebar_snapshot)

st.caption(
    "Leatherback Fairfield TEA Dashboard v10 — Fairfield-only continuous fermentation model "
    "with fixed phase volumes, S1/S2 feedstock scenarios, v9 DSP pathways, optional PHBV "
    "co-production, and v10 human-grade protein (HGP). SCP market default \\$2.00/kg "
    "(fishmeal / FeedKind / UniProtein benchmarks), slider \\$0.30-\\$8.00/kg."
)
