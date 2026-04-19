#!/usr/bin/env python3
"""
Leatherback Fairfield TEA Dashboard — v7
========================================
Dedicated Fairfield model built from the April 2026 site handoff and PDF.

Scope:
  - Facility: former AB InBev brewery, 3101 Busch Dr, Fairfield CA
  - Fixed phase sizes: 50,000 L / 150,000 L / 400,000 L
  - Continuous mode, 24 h residence time, 85 % uptime
  - Scenarios modeled: S1 (Jelly Belly COD) and S2 (70/30 JB COD + DLP)
  - Finance: 9 % discount rate, 10-year horizon
  - CapEx sliders: acquisition cost + added major CapEx

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

Run locally:
    cd ~/Downloads
    streamlit run tea_dashboard_v7.py

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
    page_title="Leatherback Fairfield TEA Dashboard v7",
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

    st.title("Leatherback Fairfield TEA Dashboard v7")
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
    "wang_2022": {
        "title": "Wang et al. 2022, Processes 10:17",
        "kind": "Literature / TEA",
        "why": "DLP pricing and lactase-reuse / pretreatment economics.",
        "used": "Used qualitatively for DLP pretreatment and feed-cost framing. No single hard-coded numeric default is copied directly from this citation.",
        "url": "https://scholar.google.com/scholar?q=Wang+2022+Processes+delactosed+whey+permeate+enzyme",
        "url_note": "MDPI Processes article not located via DOI search. Replace with your team's known DOI.",
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
        "title": "Dalsasso et al. 2019 -- molasses PHB",
        "kind": "Literature",
        "why": "Molasses-based PHA performance and conservative titer framing (11.7 g/L PHB).",
        "used": "Used specifically for the conservative molasses PHB titer framing around 11.7 g/L PHB, and more generally for molasses-based PHA plausibility.",
        "url": "https://doi.org/10.3389/fbioe.2022.946085",
        "url_note": "Links to Frontiers review covering Dalsasso-type molasses data. Confirm the exact ResearchGate source with your team.",
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
        "title": "Matassa et al. 2016, Microbial Biotechnology 9(5):568-575",
        "kind": "Literature (open access)",
        "why": "H2-oxidizing bacteria as sustainable microbial protein source. Supports 3.0 kg DCW / kg H2 yield framing.",
        "used": "Used alongside Ishizaki as support for the autotrophic H2/CO2 biomass-yield assumption near 3.0 kg DCW per kg H2.",
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
        "title": "Kim & Lee 1994, Microbiol. Biotechnol. Lett.",
        "kind": "Literature",
        "why": "High-cell-density fed-batch (122 g/L CDW, 65% PHB) reference for H2/CO2.",
        "used": "Used qualitatively to anchor the upper-end feasibility of optimized H2/CO2 PHA cases (122 g/L CDW, 65% PHB), not copied directly as the dashboard default titer.",
        "url": "https://www.koreascience.kr/article/JAKO199411920017566.view",
        "url_note": "",
    },
    "ryu_1997": {
        "title": "Ryu et al. 1997, Biotechnol. Bioeng. 55(1):28-32",
        "kind": "Literature",
        "why": "High-cell-density fructose fed-batch (281 g/L CDW, 232 g/L PHB).",
        "used": "Used qualitatively to anchor the upper-end feasibility of optimized fructose PHA cases, not copied directly as a dashboard default because the guarded app keeps more conservative user-facing ranges.",
        "url": "https://doi.org/10.1002/%28SICI%291097-0290%2819970705%2955:1%3C28::AID-BIT4%3E3.0.CO;2-Z",
        "url_note": "",
    },
    "plasmid_2025": {
        "title": "DOI 10.1016/j.plasmid.2025.102765",
        "kind": "Literature",
        "why": "Sucrose / related substrate performance reference for optimized PHA framing.",
        "used": "Used qualitatively for optimized sugar/substrate PHA performance framing; no single fixed scalar is copied directly from this paper.",
        "url": "https://doi.org/10.1016/j.plasmid.2025.102765",
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
    ids = ["framework_2026", "imarc_ammonium_2025"]
    if model_key in {"pha", "bio"}:
        ids.extend(["kim_1994", "ryu_1997", "plasmid_2025"])
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

    for note in notes:
        st.markdown(f"- {note}")

    for ref_id in refs:
        ref = REFERENCE_LIBRARY[ref_id]
        url = (ref.get("url") or "").strip()
        url_note = (ref.get("url_note") or "").strip()
        used = (ref.get("used") or "").strip()
        if url:
            link_md = f"[{ref['title']}]({url})"
        else:
            link_md = f"**{ref['title']}** *(no public URL)*"
        extra = f" -- *{url_note}*" if url_note else ""
        st.markdown(f"- {link_md} `{ref['kind']}`{extra}")
        st.markdown(f"  Used in dashboard: {ref['why']}")
        if used:
            st.markdown(f"  Exactly used from this source: {used}")


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


def _annual_operating_cycles() -> float:
    return HOURS_PER_YEAR * UPTIME_FRACTION / CONTINUOUS_HRT_H


def _annual_cdw_kg_from_phase(vessel_volume_L: float, utilization_pct: float, titer_gL: float) -> Tuple[float, float]:
    utilized_volume_L = vessel_volume_L * (utilization_pct / 100.0)
    annual_cdw_kg = utilized_volume_L * (titer_gL / 1000.0) * _annual_operating_cycles()
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
    total_project_capex = float(overrides.get("project_capex_purchase", acquisition_cost + added_major_capex))
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

    active_volume_L, annual_cdw_kg = _annual_cdw_kg_from_phase(vessel_volume_L, util_pct, titer_gL)
    annual_pha_kg = _sellable_pha_kg(annual_cdw_kg, phb_content_frac)
    annual_scp_kg = _sellable_scp_kg(annual_cdw_kg, phb_content_frac)
    annual_total_product_kg = annual_pha_kg + annual_scp_kg

    sugar_required_kg = annual_cdw_kg / max(1e-9, yield_kg_per_kg_sugar * carbon_recovery_frac)
    substrate_cost = sugar_required_kg * (jb_share * jb_sugar_price + dlp_share * dlp_sugar_price)
    pretreatment_cost = sugar_required_kg * (jb_share * jb_pretreat_cost + dlp_share * dlp_pretreat_cost)
    nitrogen_cost = annual_cdw_kg * standard_n_cost_per_kg_cdw * (1.0 - n_reduction_frac)
    electricity_cost = annual_cdw_kg * electricity_kwh_per_kg_cdw * electricity_price
    steam_cost = annual_cdw_kg * steam_cost_per_kg_cdw
    extraction_cost = annual_pha_kg * pha_extraction_cost_per_kg_sellable
    downstream_cost = annual_cdw_kg * downstream_cost_per_kg_cdw
    cip_cost = annual_cdw_kg * cip_cost_per_kg_cdw

    total_annual_cost = (
        substrate_cost + pretreatment_cost + nitrogen_cost + electricity_cost
        + steam_cost + extraction_cost + downstream_cost + cip_cost
        + labor_cost + annual_major_capex
    )
    total_revenue = annual_pha_kg * pha_blended_price + annual_scp_kg * scp_target_price
    annual_cash_flow = total_revenue - (total_annual_cost - annual_major_capex)
    pha_msp_standalone = total_annual_cost / max(1.0, annual_pha_kg)
    pha_msp_with_scp_credit = (total_annual_cost - annual_scp_kg * scp_credit_price) / max(1.0, annual_pha_kg)
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

    _check("S1 CDW titer (g/L)", s1_inputs["titer_gL"], 35.0, 85.0, "S1 base case is locked at 60 g/L; 35 g/L reproduces the v5/v6 conservative Year 1 case and >85 g/L should be treated as a stretch assumption.")
    _check("S2 CDW titer (g/L)", s2_inputs["titer_gL"], 35.0, 85.0, "S2 base case is locked at 60 g/L; values above ~85 g/L move into aggressive high-cell-density territory.")
    _check("S1 biomass yield (kg/kg sugar)", s1_inputs["yield_kg_per_kg_sugar"], 0.40, 0.55)
    _check("S2 biomass yield (kg/kg sugar)", s2_inputs["yield_kg_per_kg_sugar"], 0.42, 0.55)
    _check("S1 PHB content (% CDW)", s1_inputs["phb_content_frac"] * 100.0, 30.0, 72.0)
    _check("S2 PHB content (% CDW)", s2_inputs["phb_content_frac"] * 100.0, 30.0, 72.0)
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

    if s1_inputs["titer_gL"] > 85.0 or s2_inputs["titer_gL"] > 85.0:
        warnings.append("Titer above 85 g/L is allowed for exploration, but should be treated as speculative unless you have process-specific supporting data.")
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
    cp = r.cip_cost / 1e6
    lab = r.labor_cost / 1e6
    cap = r.annual_major_capex / 1e6
    cf = r.annual_cash_flow / 1e6
    values = [rv, -feed, -nit, -elec, -stm, -ext, -dwn, -cp, -lab, -cap, cf]
    labels = [
        "Revenue\n(PHA+SCP)", "Feedstock &\npretreat", "Nitrogen",
        "Electricity", "Steam", "Extraction", "Downstream",
        "CIP / maint.", "Labor", "Annualized\nCapEx", "Cash\nflow",
    ]
    colors = ["#059669"] + ["#dc2626"] * 9 + ["#0369a1"]
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
}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP FLOW
# ═══════════════════════════════════════════════════════════════════════════════

_require_app_password()

st.title("Leatherback Fairfield TEA Dashboard v7")
st.caption(
    "Dedicated Fairfield dashboard | AB InBev Fairfield brewery | continuous 24 h HRT | "
    "Scenarios 1 and 2 only | NCIMB 11599 | 60 g/L CDW, 60% PHB base case locked (v7)"
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

_sb_hdr("Process + Cost Inputs")
electricity_price = st.sidebar.slider("Electricity price ($/kWh)", 0.01, 0.30, 0.12, 0.005, key="v5_electricity_price")
electricity_kwh_per_kg_cdw = st.sidebar.slider("Electricity intensity (kWh/kg CDW)", 0.20, 5.00, float(ELECTRICITY_KWH_PER_KG_CDW), 0.01, key="v5_elec_intensity")
jb_sugar_price = st.sidebar.slider("Jelly Belly sugar cost ($/kg sugar)", 0.01, 0.50, JB_SUGAR_PRICE, 0.005, key="v5_jb_sugar_price")
dlp_sugar_price = st.sidebar.slider("DLP sugar cost ($/kg sugar)", 0.01, 0.50, DLP_SUGAR_PRICE, 0.005, key="v5_dlp_sugar_price")
jb_pretreat_cost = st.sidebar.slider("Jelly Belly pretreatment ($/kg sugar)", 0.00, 0.20, JB_PRETREAT_COST, 0.001, key="v5_jb_pretreat")
dlp_pretreat_cost = st.sidebar.slider("DLP pretreatment ($/kg sugar)", 0.00, 0.10, DLP_PRETREAT_COST, 0.001, key="v5_dlp_pretreat")
steam_cost_per_kg_cdw = st.sidebar.slider("Steam / thermal cost ($/kg CDW)", 0.00, 1.00, STEAM_COST_PER_KG_CDW, 0.01, key="v5_steam_cost")
downstream_cost_per_kg_cdw = st.sidebar.slider("Downstream cost ($/kg CDW)", 0.00, 2.00, DOWNSTREAM_COST_PER_KG_CDW, 0.01, key="v5_downstream_cost")
cip_cost_per_kg_cdw = st.sidebar.slider("CIP / maintenance cost ($/kg CDW)", 0.00, 1.00, CIP_COST_PER_KG_CDW, 0.01, key="v5_cip_cost")
pha_extraction_cost_per_kg_sellable = st.sidebar.slider(
    "PHA extraction cost ($/kg sellable PHA)", 0.00, 3.00, float(PHA_EXTRACTION_COST_PER_KG_SELLABLE), 0.01, key="v5_pha_extraction"
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
scp_target_price = st.sidebar.slider(
    "Feed-grade SCP selling price ($/kg)",
    0.30, 8.00, SCP_TARGET_PRICE, 0.05,
    key="v5_scp_price",
)
st.sidebar.caption(
    "**Market price, not MSP.** Default $2.00/kg is the upper end of the "
    "feed-grade bacterial-SCP benchmark band: fishmeal $1.45-1.79/kg (FRED "
    "PFISHUSDM 2024-2025), Calysta FeedKind $1.50-2.00/kg (Rabobank / "
    "Aquafeed), Unibio UniProtein ~$2.00/kg. The MSP reported above is the "
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
)

with st.expander("Fairfield Facility + Scenario Basis", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            (
                f"<div style='line-height:1.7;'>"
                f"<div><strong>Facility:</strong> Former AB InBev brewery, 3101 Busch Drive, Fairfield CA</div>"
                f"<div><strong>Installed phases:</strong> 50,000 L / 150,000 L / 400,000 L</div>"
                f"<div><strong>Mode:</strong> Continuous, 24 h HRT, 85% uptime locked</div>"
                f"<div><strong>Electricity:</strong> ${electricity_price:.3f}/kWh</div>"
                f"<div><strong>Strain:</strong> C. necator NCIMB 11599</div>"
                f"<div><strong>Acquisition:</strong> ${acquisition_cost/1e6:.1f}M</div>"
                f"<div><strong>Added major CapEx:</strong> ${added_major_capex/1e6:.1f}M</div>"
                f"<div><strong>Annualized CapEx:</strong> ${(focus.annual_major_capex)/1e6:.2f}M/yr at {discount_rate:.0%}, {npv_years} yr</div>"
                f"</div>"
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            (
                f"<div style='line-height:1.7;'>"
                f"<div><strong>Scenario 1:</strong> 100% Jelly Belly COD, yield {s1_yield:.3f} kg/kg, {s1_titer:.1f} g/L, {s1_phb*100:.0f}% PHB, {s1_scp_cp*100:.0f}% SCP CP</div>"
                f"<div><strong>Scenario 2:</strong> 70/30 Jelly Belly COD/DLP, yield {s2_yield:.3f} kg/kg, {s2_titer:.1f} g/L, {s2_phb*100:.0f}% PHB, {s2_scp_cp*100:.0f}% SCP CP</div>"
                f"<div><strong>SCP target price:</strong> ${scp_target_price:.2f}/kg</div>"
                f"<div><strong>PHA revenue price basis:</strong> {phb_share*100:.0f}% PHB @ ${phb_standard_price:.2f}/kg + {(1.0-phb_share)*100:.0f}% PHBV @ ${phbv_price:.2f}/kg = <strong>${common_overrides['pha_blended_price']:.2f}/kg</strong></div>"
                f"<div><strong>SCP credit for PHA MSP:</strong> ${scp_credit_price:.2f}/kg</div>"
                f"<div><strong>Scenario 3:</strong> Narrative upside only, not modeled in v5</div>"
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
    f"Throughput basis: {focus.vessel_volume_L:,.0f} L installed × {focus.utilization_pct:.0f}% utilization = "
    f"{focus.active_volume_L:,.0f} L utilized broth volume; annual CDW then uses "
    f"{_annual_operating_cycles():.2f} operating turnover-equivalents/year (24 h HRT with 85% uptime)."
)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Scenario", focus.scenario_id)
c2.metric("Phase", focus.phase)
c3.metric("CDW (t/y)", f"{focus.annual_cdw_tpy:,.0f}")
c4.metric("PHA MSP w/ SCP", f"${focus.pha_msp_with_scp_credit:.2f}/kg")
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
        st.warning(msg, icon="⚠️")
else:
    st.success("All Fairfield-controlled inputs are inside the current recommended planning bands.", icon="✅")
st.warning(
    "Open data item: Jelly Belly COD sugar composition is still estimated from published confectionary formulas. "
    "The feedstock sensitivity figure applies a ±20% band to feedstock + pretreatment cost to reflect that uncertainty."
)
st.info(
    "Annual throughput uses the continuous roll-up: utilized broth volume × titer × "
    "(8,760 h/year × 85% uptime ÷ 24 h HRT). At the v7 locked 60 g/L base case, "
    "Phase III S1 at 90% utilization gives ~6,701 t/y CDW. At the v5/v6 35 g/L "
    "conservative case, the same configuration gives ~3,909 t/y CDW. "
    "The site handoff (Fairfield_TEA_v7_Final.pdf, page 7) states ~10,700 t/y "
    "for the 35 g/L case, which does not match its own formula "
    "(306,000 L × 35 g/L × 8,760/24 ÷ 1e6 = 3,909 t/y). The v7 TEA does not "
    "inherit that defect because it computes CDW from first principles."
)

_section("Phase + Scenario Table")
rows = _fairfield_rows(results)
st.dataframe(rows, use_container_width=True)
if rows:
    csv = "\n".join([",".join(rows[0].keys())] + [",".join(str(v) for v in row.values()) for row in rows]).encode()
    st.download_button("Download Fairfield v5 CSV", data=csv, file_name="fairfield_v5_results.csv", mime="text/csv")

_section("Figures")
fig_opts = {
    "Phase Output": lambda: fig_v5_outputs(results),
    "MSP and Cash Flow": lambda: fig_v5_msp_and_cash(results),
    "Returns by Phase": lambda: fig_v5_returns(results),
    "NPV vs Selling Price": lambda: fig_v5_npv_vs_price(results, focus_phase, scp_target_price, pha_blended_price, discount_rate, npv_years),
    "IRR vs Selling Price": lambda: fig_v5_irr_vs_price(results, focus_phase, scp_target_price, pha_blended_price, npv_years),
    "Cost Structure": lambda: fig_v5_cost_structure(results, focus_phase, focus_scenario_id),
    "Discounted Cash Flow": lambda: fig_v5_discounted_cf(results, focus_phase, focus_scenario_id, discount_rate, npv_years),
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
        st.markdown(formula_text)
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
    f"${_be_info['rev_per_cdw']:.2f} of revenue against ${_be_info['var_per_cdw']:.2f} of variable cost, "
    f"for a contribution margin of ${_be_info['margin_per_cdw']:.2f}/kg. "
    f"Fixed labor is ${_be_info['labor']/1e6:.2f}M/yr. "
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
}
render_v5_chat(results, focus_phase, focus_scenario_id, sidebar_snapshot)

st.caption(
    "Leatherback Fairfield TEA Dashboard v7 — dedicated Fairfield-only dashboard built on "
    "the current TEA workflow, with fixed phase volumes and scenario-locked assumptions. "
    "v7 supersedes v5 and v6: the feed-grade SCP market-price default is corrected to "
    "$2.00/kg (anchored to fishmeal / FeedKind / UniProtein 2024-2025 benchmarks) and the "
    "slider is widened to $0.30-$8.00/kg. The human-grade-protein scenario explored in v6 "
    "is not carried into v7 — the modeled scope is the SCP+PHA biorefinery (S1, S2) only."
)
