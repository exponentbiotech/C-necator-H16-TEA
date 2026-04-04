#!/usr/bin/env python3
"""
Literature-Guarded C. necator H16 SCP/PHA TEA Dashboard — v3
===============================================
Visual upgrade, verified paper-direct reference links, Groq-powered LLM chat,
and a more believable installed-CapEx finance model.

Run locally:
    cd ~/Downloads
    streamlit run tea_dashboard_v3.py

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

import importlib
import math
import sys
from dataclasses import fields
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
    page_title="C. necator H16 SCP/PHA TEA Dashboard v3",
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
        "labor_small_scale":  {"label": "Labor <1,000 t/y ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor 3,500 t/y ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor 7,000 t/y ($/yr)", "basis": "scenario"},
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
        "labor_small_scale":  {"label": "Labor <1,000 t/y ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor 3,500 t/y ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor 7,000 t/y ($/yr)", "basis": "scenario"},
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
        "labor_small_scale":  {"label": "Labor <1,000 t/y ($/yr)", "basis": "scenario"},
        "labor_medium_scale": {"label": "Labor 3,500 t/y ($/yr)", "basis": "scenario"},
        "labor_large_scale":  {"label": "Labor 7,000 t/y ($/yr)", "basis": "scenario"},
        "npv_discount_rate":  {"label": "NPV discount rate", "basis": "scenario"},
        "npv_years":          {"label": "NPV horizon (years)", "basis": "scenario"},
    },
}

FINANCE_DEFAULTS: Dict[str, Dict[str, float]] = {
    "scp": {
        "reference_capacity_tpy": 3_500.0,
        "base_installed_capex_ref": 25_000_000.0,
        "capex_scaling_exponent": 0.60,
        "added_capex_ref": 0.0,
    },
    "pha": {
        "reference_capacity_tpy": 3_500.0,
        "base_installed_capex_ref": 35_000_000.0,
        "capex_scaling_exponent": 0.60,
        "added_capex_ref": 0.0,
    },
    "bio": {
        "reference_capacity_tpy": 3_500.0,
        "base_installed_capex_ref": 45_000_000.0,
        "capex_scaling_exponent": 0.60,
        "added_capex_ref": 0.0,
    },
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
        "used": "Used for scenario structure, capacity tiers (50, 350, 3,500, 7,000 t/y), and the imported TEA model architecture. Not a single literature scalar.",
        "url": "",
        "url_note": "Internal / confidential document.",
    },
    "wang_2022": {
        "title": "Wang et al. 2022, Processes 10:17",
        "kind": "Literature / TEA",
        "why": "DLP pricing and lactase-reuse / pretreatment economics.",
        "used": "Used qualitatively for DLP pretreatment and feed-cost framing. No single hard-coded numeric default is copied directly from this citation in v3.",
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
        "used": "Used qualitatively for optimized sugar/substrate PHA performance framing; no single fixed scalar is copied directly into v3 from this paper.",
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
                    "v3 finance model: define a believable installed CapEx at 3,500 t/y, "
                    "scale it across capacities with an exponent, and optionally add extra CapEx on top."
                )
                values["base_installed_capex_ref"] = st.slider(
                    "Base installed CapEx at 3,500 t/y ($M)",
                    min_value=0.0,
                    max_value=250.0,
                    value=float(st.session_state.get("base_installed_capex_ref", fin["base_installed_capex_ref"] / 1e6)),
                    step=1.0,
                    format="$%.1fM",
                    key="base_installed_capex_ref",
                    help=(
                        "Reference installed project cost at 3,500 t/y. "
                        "Use this as the believable total installed capital basis for the finance model."
                    ),
                ) * 1e6
                values["added_capex_ref"] = st.slider(
                    "Extra added CapEx at 3,500 t/y ($M)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(st.session_state.get("added_capex_ref", fin["added_capex_ref"] / 1e6)),
                    step=0.5,
                    format="$%.1fM",
                    key="added_capex_ref",
                    help="Optional extra project scope on top of the base installed CapEx, referenced at 3,500 t/y.",
                ) * 1e6
                values["capex_scaling_exponent"] = st.slider(
                    "CapEx scaling exponent",
                    min_value=0.40,
                    max_value=1.00,
                    value=float(st.session_state.get("capex_scaling_exponent", fin["capex_scaling_exponent"])),
                    step=0.05,
                    format="%.2f",
                    key="capex_scaling_exponent",
                    help="Use ~0.60 for a classic six-tenths rule. Lower values create stronger economies of scale.",
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


def render_key_metrics(model_key: str, results: List[Any]) -> None:
    if model_key == "scp":
        _section("Lowest MSP at 3,500 t/y -- all SCP scenarios")
        pool = [r for r in results if r.capacity_tpy == 3_500.0]
        best = min(pool, key=lambda r: r.msp)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("MSP ($/kg)", f"${best.msp:.3f}")
        c2.metric("Feedstock", _display_text(best.feed.value))
        c3.metric("Mode", _display_text(best.mode.value))
        c4.metric("Annual SCP (t/y)", f"{best.annual_product_kg / 1e3:,.0f}")
        c5.metric("Reactor (m3)", f"{best.reactor_volume_m3:,.0f}")
    elif model_key == "pha":
        _section("Lowest MSP at 3,500 t/y -- all PHA scenarios")
        pool = [r for r in results if r.capacity_tpy == 3_500.0]
        best = min(pool, key=lambda r: r.msp)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("MSP ($/kg)", f"${best.msp:.3f}")
        c2.metric("Feedstock", _display_text(best.feed.value))
        c3.metric("Mode", _display_text(best.mode.value))
        c4.metric("Product", _display_text(best.product.value))
        c5.metric("Scenario", _display_text(best.titer_scenario.value))
        c6.metric("Annual PHA (t/y)", f"{best.annual_product_kg / 1e3:,.0f}")
    else:
        _section("Lowest PHA MSP with SCP credit at 3,500 t/y CDW")
        pool = [r for r in results if r.capacity_tpy_cdw == 3_500.0]
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
        ax1.plot(prices, paybacks, color=colors[idx % len(colors)],
                 linewidth=2, label=f"{cap:,.0f} t/y")

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

    # ── Right panel: cumulative discounted cash flow at chosen price, 3500 t/y ──
    target_cap = 3_500.0
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
    ax2.set_title(f"Discounted CF at {_selected_price_context(model_key, sell_price, scp_price)}, 3,500 t/y")
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
        ax1.plot(prices, irrs, color=colors[idx % len(colors)],
                 linewidth=2, label=f"{cap:,.0f} t/y")

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
        ax2.plot(capex_range / 1e6, irrs, color=colors[idx % len(colors)],
                 linewidth=2, label=f"{cap:,.0f} t/y")

    ax2.axhline(8, color="#f59e0b", ls="--", lw=1, alpha=0.6)
    ax2.axhline(15, color="#22c55e", ls="--", lw=1, alpha=0.6)
    current_ref = best_map.get(3_500.0, list(best_map.values())[len(best_map) // 2])
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
#  FIGURE FORMULA EXPLANATIONS (plain English)
# ═══════════════════════════════════════════════════════════════════════════════

FIGURE_FORMULAS: Dict[str, str] = {
    "MSP Overview": (
        "**Minimum Selling Price (MSP)** = Total Annual Cost / Annual Product Output (kg/yr).\n\n"
        "Total Annual Cost includes operating expenses (feedstock, energy, labor, nitrogen, etc.) "
        "**plus annualized Major CapEx** if set in the sidebar. "
        "The CapEx is annualized using the Capital Recovery Factor: "
        "CRF = r(1+r)^N / ((1+r)^N - 1), where r = discount rate and N = project years.\n\n"
        "MSP is the lowest price per kg you must charge to cover all yearly costs including capital recovery."
    ),
    "Scale Curve": (
        "Same MSP formula (Total Annual Cost / Annual Output) plotted against production capacity (t/y).\n\n"
        "Larger plants spread fixed costs (labor, overheads, **annualized CapEx**) over more product, "
        "so MSP drops as capacity increases. "
        "In v3, installed CapEx is defined at 3,500 t/y and then scaled across capacities with a cost-capacity exponent, "
        "which creates a more believable economies-of-scale pattern than using the same fixed capital add-on at every scale."
    ),
    "Cost Structure (3,500 t/y)": (
        "Stacked bar chart decomposing the **total annual operating cost** into cost categories "
        "(substrate, energy, labor, nitrogen, aeration, downstream) at the 3,500 t/y capacity tier.\n\n"
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
        "In v3, annualized installed CapEx is folded into the cost basis before NPV is computed."
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
        "Total Project CapEx = minor included purchase CapEx from the TEA model + scaled installed CapEx from the v3 finance model.\n"
        "Annual Project Cash Flow = Revenue - cash operating cost.\n"
        "To avoid double counting, annualized CapEx charges are added back out of total annual cost.\n\n"
        "In **Biorefinery** mode, the swept price is the **PHA selling price**. SCP revenue is still calculated using the separate `SCP market price` assumption.\n\n"
        "Shows how many years of profit are needed to recoup the initial capital investment.\n\n"
        "**Right panel -- Discounted Cash Flow**:\n"
        "Starts at -Total Project CapEx in year 0, then adds discounted annual project cash flow each year: "
        "CF(t) = Cash Flow / (1 + r)^t.\n"
        "The **payback year** is where the cumulative line crosses zero. "
        "Red shading = still in the red; green = investment recovered.\n\n"
        "*Discount rate is taken from the NPV discount rate assumption in the sidebar.*"
    ),
    "IRR Analysis": (
        "**Internal Rate of Return (IRR)** is the discount rate that makes the Net Present Value "
        "of the project exactly zero:\n\n"
        "0 = -Total Project CapEx + Sum over t=1..N of (Annual Project Cash Flow / (1 + IRR)^t)\n\n"
        "In plain terms: IRR is the **annual percentage return** the project earns on the initial investment. "
        "A higher IRR is better.\n\n"
        "Total Project CapEx = minor included purchase CapEx + scaled installed CapEx from the v3 finance model.\n"
        "Annual Project Cash Flow = Revenue - cash operating cost, with annualized CapEx charges added back "
        "to avoid double counting the same capital twice.\n\n"
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
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
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
        pool = [r for r in results if r.capacity_tpy == 3_500.0]
        best = min(pool, key=lambda r: r.msp)
        headline = (
            f"Best SCP MSP at 3,500 t/y: ${best.msp:.3f}/kg via "
            f"{_display_text(best.feed.value)}, {_display_text(best.mode.value)}"
        )
    elif model_key == "pha":
        pool = [r for r in results if r.capacity_tpy == 3_500.0]
        best = min(pool, key=lambda r: r.msp)
        headline = (
            f"Best PHA MSP at 3,500 t/y: ${best.msp:.3f}/kg via "
            f"{_display_text(best.feed.value)}, {_display_text(best.mode.value)}, "
            f"{_display_text(best.product.value)}, {_display_text(best.titer_scenario.value)}"
        )
    else:
        pool = [r for r in results if r.capacity_tpy_cdw == 3_500.0]
        best = min(pool, key=lambda r: r.pha_msp_with_scp_credit)
        headline = (f"Best PHA MSP w/ SCP credit at 3,500 t/y CDW: ${best.pha_msp_with_scp_credit:.3f}/kg "
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
- v3 uses a reference installed-CapEx-at-3,500-t/y model with a scaling exponent across capacities. That installed CapEx is annualized using the Capital Recovery Factor and added to annual cost for MSP figures, while payback/IRR use the corresponding upfront project investment and annual cash flow.
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
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask about the TEA results, assumptions, or references..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

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
                    placeholder.markdown(full_response + " |")
                placeholder.markdown(full_response)
            except Exception as exc:
                full_response = f"Groq API error: {exc}"
                placeholder.error(full_response)

        st.session_state.chat_messages.append({"role": "assistant", "content": full_response})


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP FLOW
# ═══════════════════════════════════════════════════════════════════════════════

st.title("C. necator H16 SCP/PHA TEA Dashboard v3")
st.caption(
    "Literature-guarded assumptions | Verified paper links | Groq-powered LLM chat | Installed-CapEx finance model"
)

st.info(
    "The base math comes from the imported TEA modules. "
    "v3 adds a more believable installed-CapEx model: define a base installed CapEx at 3,500 t/y, "
    "scale it by capacity with an exponent, and optionally add extra CapEx on top. "
    "That capital is annualized into MSP figures and used as upfront investment for payback/IRR.",
    icon="ℹ️",
)

_sb_hdr("Select Model")
choice = st.sidebar.radio("", [
    "SCP — Single-Cell Protein",
    "PHA — Bioplastic",
    "Biorefinery — SCP + PHA together",
], index=0, label_visibility="collapsed")

if choice.startswith("SCP"):
    model_key = "scp"
    defaults = scp.Assumptions()
elif choice.startswith("PHA"):
    model_key = "pha"
    defaults = pha.Assumptions()
else:
    model_key = "bio"
    defaults = bio.Assumptions()

_sb_hdr("Model Assumptions")

assumption_kwargs, range_warnings, scenario_notes_list, audit_rows, skipped = render_assumptions(model_key, defaults)
base_installed_capex_ref = float(assumption_kwargs.pop("base_installed_capex_ref", FINANCE_DEFAULTS[model_key]["base_installed_capex_ref"]))
added_capex_ref = float(assumption_kwargs.pop("added_capex_ref", FINANCE_DEFAULTS[model_key]["added_capex_ref"]))
capex_scaling_exponent = float(assumption_kwargs.pop("capex_scaling_exponent", FINANCE_DEFAULTS[model_key]["capex_scaling_exponent"]))
target_sell_price = float(assumption_kwargs.pop("target_sell_price", 3.0))
derived_warnings = add_derived_warnings(model_key, assumption_kwargs)

if skipped:
    with st.sidebar.expander("Fixed structured assumptions", expanded=False):
        st.write("Not editable here: " + ", ".join(f"`{n}`" for n in skipped))

if model_key == "scp":
    assumptions = scp.Assumptions(**assumption_kwargs)
elif model_key == "pha":
    assumptions = pha.Assumptions(**assumption_kwargs)
else:
    assumptions = bio.Assumptions(**assumption_kwargs)

# -- Assumption audit --
_section("Assumption Audit")
if range_warnings or derived_warnings:
    for msg in range_warnings + derived_warnings:
        st.warning(msg, icon="⚠️")
else:
    st.success("All literature-ranged inputs are inside their recommended bands.", icon="✅")

if scenario_notes_list:
    with st.expander("Scenario-only / untethered edits"):
        for msg in scenario_notes_list:
            st.info(msg)

with st.expander("Parameter audit table"):
    st.dataframe(audit_rows, use_container_width=True)

# -- Run model --
with st.status("Running all scenarios...", expanded=False) as status:
    if model_key == "scp":
        results = scp.run_all_scenarios(assumptions=assumptions, verbose=False)
    elif model_key == "pha":
        results = pha.run_all_scenarios(assumptions=assumptions, verbose=False)
    else:
        results = bio.run_all_scenarios(assumptions=assumptions, verbose=False)
    status.update(label=f"Done -- {len(results)} scenarios computed", state="complete")

# -- Annualize major CapEx into every scenario's cost & MSP --
_disc = float(assumption_kwargs.get("npv_discount_rate", 0.08))
_nyrs = int(assumption_kwargs.get("npv_years", 10))
_annual_capex = 0.0
_ref_capacity = FINANCE_DEFAULTS[model_key]["reference_capacity_tpy"]

if (base_installed_capex_ref > 0 or added_capex_ref > 0) and _disc > 0 and _nyrs > 0:
    _crf = _disc * (1 + _disc) ** _nyrs / ((1 + _disc) ** _nyrs - 1)
    _annual_capex = (base_installed_capex_ref + added_capex_ref) * _crf

    st.info(
        f"Installed CapEx model at **{_ref_capacity:,.0f} t/y**: "
        f"base = **${base_installed_capex_ref / 1e6:.1f}M**, added = **${added_capex_ref / 1e6:.1f}M**, "
        f"scaling exponent = **{capex_scaling_exponent:.2f}**. "
        f"Capital is annualized with CRF = **{_crf:.4f}** at {_disc:.0%} over {_nyrs} years "
        f"and scaled by capacity before being added to annual cost.",
        icon="🏗️",
    )

    for r in results:
        cap = _result_capacity(model_key, r)
        major_purchase = _scaled_capex_from_reference(
            cap,
            base_installed_capex_ref + added_capex_ref,
            _ref_capacity,
            capex_scaling_exponent,
        )
        major_annual = major_purchase * _crf
        r.major_installed_capex_purchase_v3 = major_purchase
        r.major_installed_capex_annual_v3 = major_annual
        r.total_project_capex_purchase_v3 = _base_purchase_capex(r) + major_purchase
        r.total_annual_cost += major_annual
        if model_key == "scp":
            r.msp = r.total_annual_cost / r.annual_product_kg
        elif model_key == "pha":
            r.msp = r.total_annual_cost / r.annual_product_kg
        else:
            if r.annual_pha_product_kg > 0:
                r.pha_msp_standalone = r.total_annual_cost / r.annual_pha_product_kg
                scp_credit = r.annual_scp_product_kg * float(assumption_kwargs.get("scp_market_price", 2.0))
                r.pha_msp_with_scp_credit = (r.total_annual_cost - scp_credit) / r.annual_pha_product_kg
            if r.annual_scp_product_kg > 0:
                pha_credit = r.annual_pha_product_kg * float(assumption_kwargs.get("phb_market_price", 5.0))
                r.scp_msp_with_pha_credit = (r.total_annual_cost - pha_credit) / r.annual_scp_product_kg
            total_prod = r.annual_pha_product_kg + r.annual_scp_product_kg
            if total_prod > 0:
                r.blended_msp = r.total_annual_cost / total_prod

# -- Key metrics --
render_key_metrics(model_key, results)

# -- Results table --
with st.expander("Full results table"):
    rows = build_results_table(model_key, results)
    st.dataframe(rows, use_container_width=True)
    st.download_button("Download CSV",
                       data="\n".join([",".join(rows[0].keys())] + [",".join(str(v) for v in row.values()) for row in rows]).encode() if rows else b"",
                       file_name=f"{model_key}_v3_results.csv", mime="text/csv")

# -- References --
render_reference_trace(model_key, results, assumption_kwargs, defaults)

# -- Figures --
_section("Figures")

if model_key == "bio":
    st.caption("In biorefinery finance plots, the swept price axis is the **PHA selling price**. SCP revenue stays tied to the separate `SCP market price` input.")

_disc_rate = float(assumption_kwargs.get("npv_discount_rate", 0.08))
_scp_mkt = float(assumption_kwargs.get("scp_market_price", 2.0)) if model_key == "bio" else 2.0
_payback_fn = lambda: fig_capital_payback(
    model_key, results, target_sell_price, _disc_rate, _scp_mkt)
_n_years = int(assumption_kwargs.get("npv_years", 10))
_irr_fn = lambda: fig_irr_analysis(
    model_key, results, target_sell_price, _n_years, _scp_mkt)

if model_key == "scp":
    fig_opts = {
        "MSP Overview": lambda: scp.fig_msp_overview(results),
        "Scale Curve": lambda: scp.fig_scale_curve(results),
        "Cost Structure (3,500 t/y)": lambda: scp.fig_cost_structure(results),
        "Sensitivity Tornado": lambda: scp.fig_sensitivity(results),
        "NPV vs Selling Price": lambda: scp.fig_npv_analysis(results),
        "Capital Payback": _payback_fn,
        "IRR Analysis": _irr_fn,
    }
elif model_key == "pha":
    fig_opts = {
        "MSP Overview": lambda: pha.fig_msp_overview(results),
        "Scale Curve": lambda: pha.fig_scale_curve(results),
        "Conservative vs Optimized": lambda: pha.fig_con_vs_opt(results),
        "PHB vs PHBV": lambda: pha.fig_phb_vs_phbv(results),
        "Cost Structure (3,500 t/y)": lambda: pha.fig_cost_structure(results),
        "Sensitivity Tornado": lambda: pha.fig_sensitivity(results),
        "NPV vs Selling Price": lambda: pha.fig_npv_analysis(results),
        "Capital Payback": _payback_fn,
        "IRR Analysis": _irr_fn,
    }
else:
    fig_opts = {
        "MSP Overview": lambda: bio.fig_msp_overview(results),
        "Biorefinery Advantage": lambda: bio.fig_biorefinery_advantage(results),
        "Revenue per Batch": lambda: bio.fig_revenue_per_batch(results),
        "Cost Structure (3,500 t/y)": lambda: bio.fig_cost_structure(results),
        "Scale Curve": lambda: bio.fig_scale_curve(results),
        "Sensitivity Tornado": lambda: bio.fig_sensitivity(results),
        "NPV vs Selling Price": lambda: bio.fig_npv_analysis(results),
        "Capital Payback": _payback_fn,
        "IRR Analysis": _irr_fn,
        "Process Flow Diagram": lambda: bio.fig_process_flow(),
    }

sel_fig = st.selectbox("Select figure", list(fig_opts.keys()))

# Formula / explanation button
formula_text = FIGURE_FORMULAS.get(sel_fig)
if formula_text:
    with st.expander("How is this figure calculated?"):
        st.markdown(formula_text)

st.markdown('<div class="fig-frame">', unsafe_allow_html=True)
try:
    fig = fig_opts[sel_fig]()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
except Exception as exc:
    st.error(f"Could not render figure: {exc}")
st.markdown('</div>', unsafe_allow_html=True)

# -- Text report --
with st.expander("Full text report"):
    if model_key == "scp":
        report = scp.format_report(results)
    elif model_key == "pha":
        report = pha.format_report(results)
    else:
        report = bio.format_report(results)
    st.text(report)
    st.download_button("Download report", data=report,
                       file_name=f"{model_key}_v3_report.txt", mime="text/plain")

# -- LLM Chat --
render_chat(model_key, assumption_kwargs, defaults, results)

st.caption("Guarded TEA Dashboard v3. Installed-CapEx finance layer added on top of the imported source modules.")
