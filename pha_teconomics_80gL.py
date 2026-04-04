#!/usr/bin/env python3
"""
Technoeconomic Model — PHA Bioplastic (PHB & PHBV) via Cupriavidus necator
===========================================================================

Products   : PHB homopolymer  and  PHBV copolymer
             Fiber-grade quality (high Mw retention required for spinning)

Feedstock cases (sourced from PhycoVax TEA Framework, March 2026):
  1. Autotrophic — H₂ / CO₂  (H₂ via renewable electrolysis)
  2. Fructose (HFCS-90) — native H16 metabolism, TRL 6–7
  3. DLP (delactosed permeate) — requires DSM545 strain, TRL 4–5
  4. Blackstrap molasses (cane) — partial H16 use, TRL 5–6

Titer scenarios:
  - Conservative : PDF lower-bound titers & yields
  - Optimized    : Literature upper-bound (achievable with R&D)

Capacities : 50  /  350  /  3,500  /  7,000  t/y sellable dry PHA
Modes      : Batch  and  Fed-batch (two-phase: growth → N-limited accumulation)

Output     : Minimum Sales Price (MSP) in USD / kg dry PHA
             (OPEX + annualised minor CapEx < $100 k / unit + labor)
             Net Present Value (NPV) at 8% discount over 10 years

Key data sources:
  - PhycoVax Inc. TEA Question Framework (March 2026, CONFIDENTIAL)
  - Wang et al. 2022, Processes 10:17 (DLP pricing, enzyme reuse TEA)
  - PubMed 40669633 (2025) — whey permeate / DSM545 yields
  - Dalsasso et al. / ResearchGate 2019 — molasses 11.7 g/L PHB
  - ScienceDirect 2025 (DOI: 10.1016/j.plasmid.2025.102765) — sucrose
  - Ishizaki et al. 2001; Matassa 2016 — H₂/CO₂ autotrophic yields
  - IMARC Group — molasses USA $290–295/MT Q2-Q3 2025

Usage
-----
Jupyter — paste entire file into **one** cell, run.  Next cell:

    results = run_all_scenarios()
    figs    = create_all_figures(results)

Terminal:
    python3 pha_teconomics_80gL.py

Dependencies: numpy, matplotlib
    pip install numpy matplotlib
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch


# ═══════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def _log(msg: str) -> None:
    print(msg, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  ASSUMPTIONS
# ═══════════════════════════════════════════════════════════════════════════
#
#  Titer basis — anchored to 80 g/L CDW fed-batch target
#  ─────────────────────────────────────────────────────────
#  Optimised fed-batch CDW ≈ 80 g/L (consistent with SCP model).
#  This is well within published C. necator fed-batch ranges:
#    Kim et al. 1994   — 121 g/L CDW (H₂/CO₂, fed-batch)
#    Ryu et al. 1997   — 281 g/L CDW (fructose, fed-batch, 232 g/L PHB)
#    Typical pilot      — 50–120 g/L CDW
#
#  Batch CDW titers (optimised ~45 g/L, conservative ~25–30 g/L) are
#  derived so that × 1.8 fed-batch factor ≈ 80 g/L CDW.
#  PHB titer = CDW titer × PHB content fraction.
#
#  Conservative batch CDW:  30 g/L (H₂/fructose/DLP), 25 g/L (molasses)
#  Optimized batch CDW:     44 g/L (H₂), 45 g/L (fructose/DLP), 39 g/L (molasses)
#  Fed-batch CDW (1.8×):    ~79–81 g/L (H₂/fructose/DLP), ~71 g/L (molasses)
#
#  PHB yield notes (g PHB / g substrate):
#    Fructose   : 0.25–0.35 g/g (Academia.edu kinetics)
#    DLP        : 0.30–0.38 g/g (PubMed 40669633)
#    Molasses   : 0.15–0.25 g/g (Dalsasso et al.)
#    H₂/CO₂    : CDW yield 3.0 kg/kg H₂ × PHB content 60–75%
#
#  Extraction : Fiber-grade PHA requires high Mw retention (>300 kDa).
#  NaOCl degrades Mw → excluded.  SDS + acetone preserves Mw.
#
#  PHBV : ~10 mol% HV from propionate.  Propionate consumption ≈ 0.08
#  kg/kg PHBV; primary substrate yield reduced ~8%.

@dataclass
class Assumptions:
    """All tuneable parameters for PHA bioplastic TEA model."""

    # ── Product specification ────────────────────────────────────────────
    extraction_recovery: float = 0.88
    product_moisture_fraction: float = 0.05

    # ── Fermentation — Batch ─────────────────────────────────────────────
    batch_growth_h: float = 36.0
    batch_accumulation_h: float = 36.0
    batch_cip_h: float = 18.0
    working_volume_fraction: float = 0.80

    # ── Fermentation — Fed-batch ─────────────────────────────────────────
    fedbatch_growth_h: float = 36.0
    fedbatch_accumulation_h: float = 60.0
    fedbatch_cip_h: float = 18.0
    fedbatch_titer_factor: float = 1.8

    # ── PHB batch titers (g/L) — Conservative (batch CDW ~25–30 g/L) ─────
    titer_h2_con: float = 18.0        # 30 g/L CDW × 0.60 PHB
    titer_fructose_con: float = 18.0  # 30 g/L CDW × 0.60
    titer_dlp_con: float = 18.0       # 30 g/L CDW × 0.60
    titer_molasses_con: float = 12.5  # 25 g/L CDW × 0.50

    # ── PHB batch titers (g/L) — Optimized (→ fed-batch CDW ≈ 80 g/L) ──
    titer_h2_opt: float = 33.0        # 44 g/L CDW × 0.75 → FB 79 g/L CDW
    titer_fructose_opt: float = 27.0  # 45 g/L CDW × 0.60 → FB 81 g/L CDW
    titer_dlp_opt: float = 27.0       # 45 g/L CDW × 0.60 → FB 81 g/L CDW
    titer_molasses_opt: float = 22.0  # 39 g/L CDW × 0.56 → FB 71 g/L CDW

    # ── PHB content (fraction of CDW) — Conservative ─────────────────────
    phb_frac_h2_con: float = 0.60
    phb_frac_fructose_con: float = 0.60
    phb_frac_dlp_con: float = 0.60
    phb_frac_molasses_con: float = 0.50

    # ── PHB content (fraction of CDW) — Optimized ────────────────────────
    phb_frac_h2_opt: float = 0.75
    phb_frac_fructose_opt: float = 0.60
    phb_frac_dlp_opt: float = 0.60
    phb_frac_molasses_opt: float = 0.56

    # ── PHB yields (g PHB / g substrate) — Conservative ──────────────────
    yield_h2_con: float = 1.80
    yield_fructose_con: float = 0.25
    yield_dlp_con: float = 0.30
    yield_molasses_con: float = 0.15

    # ── PHB yields (g PHB / g substrate) — Optimized ─────────────────────
    yield_h2_opt: float = 2.25
    yield_fructose_opt: float = 0.35
    yield_dlp_opt: float = 0.38
    yield_molasses_opt: float = 0.25

    # ── PHBV co-substrate (propionate for ~10 mol% HV) ───────────────────
    phbv_yield_factor: float = 0.92
    propionate_kg_per_kg_phbv: float = 0.08
    propionate_price_per_kg: float = 1.20

    # ── CO₂ (autotrophic) ────────────────────────────────────────────────
    co2_kg_per_kg_cdw: float = 1.83
    co2_price_per_kg: float = 0.00

    # ── Hydrogen / electrolysis ──────────────────────────────────────────
    electricity_price: float = 0.03
    electrolysis_kwh_per_kg_h2: float = 52.0

    # ── Sugar feedstock prices ($/kg fermentable sugar) ──────────────────
    fructose_price_per_kg: float = 0.375
    dlp_price_per_kg_sugar: float = 0.13
    molasses_price_per_kg_sugar: float = 0.155

    # ── Pretreatment cost ($/kg CDW produced) ────────────────────────────
    pretreatment_fructose: float = 0.00
    pretreatment_dlp: float = 0.07
    pretreatment_molasses: float = 0.02

    # ── Nitrogen — (NH₄)₂SO₄ ────────────────────────────────────────────
    n_fraction_of_cdw: float = 0.08
    nh4so4_n_fraction: float = 0.212
    nh4so4_price_per_kg: float = 0.42

    # ── Nitrogen supplement reduction (fraction) ─────────────────────────
    n_reduction_fructose: float = 0.00
    n_reduction_dlp: float = 1.00
    n_reduction_molasses: float = 0.20

    # ── Aeration (kWh / m³ broth / h) ────────────────────────────────────
    aeration_kwh_m3_h_gas: float = 0.55
    aeration_kwh_m3_h_fructose: float = 0.85
    aeration_kwh_m3_h_dlp: float = 0.85
    aeration_kwh_m3_h_molasses: float = 0.95

    # ── Harvesting (centrifugation of dilute PHA broth) ──────────────────
    centrifuge_kwh_per_m3: float = 1.2

    # ── Extraction options ───────────────────────────────────────────────
    #  (name, chem $/kg PHA, energy kWh/kg PHA, fixed $/kg PHA, fiber-ok)
    #  Fiber-grade requires high Mw retention for thread spinning.
    extraction_options: Tuple[Tuple[str, float, float, float, bool], ...] = (
        ("NaOCl digestion",       0.18, 1.5, 0.08, False),
        ("SDS + acetone wash",    0.35, 2.5, 0.10, True),
        ("Chloroform extraction", 0.55, 4.5, 0.18, True),
        ("Enzymatic lysis",       0.45, 2.0, 0.10, True),
    )
    fiber_grade_required: bool = True

    # ── Drying (extracted PHA cake → dry powder) ─────────────────────────
    drying_kwh_per_kg_water: float = 1.2
    wet_pha_moisture: float = 0.50

    # ── Minor CapEx ──────────────────────────────────────────────────────
    capex_threshold: float = 100_000.0
    minor_equipment: Tuple[Tuple[str, float, float, float, float], ...] = (
        ("Feed & media pumps (×3)",     3_500, 50, 0.60, 10),
        ("pH control system",           8_000, 50, 0.40,  8),
        ("DO & gas analysers",          5_000, 50, 0.30,  8),
        ("Media prep tank (SS)",       12_000, 50, 0.60, 15),
        ("Piping, valves, fittings",   15_000, 50, 0.60, 20),
        ("Process control (PLC/HMI)",  20_000, 50, 0.30, 10),
        ("CIP skid (small)",           25_000, 50, 0.60, 12),
        ("Water purification (RO)",    15_000, 50, 0.60, 12),
        ("Extraction chem. tank (SS)",  8_000, 50, 0.60, 15),
        ("Solvent recovery condenser", 18_000, 50, 0.55, 12),
    )

    # ── Labor (annual cost by production scale) ─────────────────────────
    labor_small_scale: float = 2_000_000.0    # <1,000 t/y
    labor_medium_scale: float = 2_000_000.0   # 3,500 t/y (capped at $2 M)
    labor_large_scale: float = 2_000_000.0    # 7,000 t/y (capped at $2 M)

    # ── NPV parameters ──────────────────────────────────────────────────────
    npv_discount_rate: float = 0.08
    npv_years: int = 10

    # ── Schedule ─────────────────────────────────────────────────────────
    hours_per_year: float = 8_760.0


DEFAULT_CAPACITIES: List[float] = [50.0, 350.0, 3_500.0, 7_000.0]

MAJOR_CAPEX_EXCLUDED: Tuple[str, ...] = (
    "Production bioreactor(s) + sterility (SIP/CIP)",
    "Industrial disc-stack centrifuge(s)",
    "Spray dryer or belt dryer",
    "Extraction vessels + solvent recovery column",
    "Electrolyser stack + rectifiers (H₂/CO₂ case)",
    "CO₂ compression / liquefaction (H₂/CO₂ case)",
    "Cold storage / warehouse",
    "Wastewater treatment system",
    "Lactase UF recycle skid (DLP only, ~$1 M at scale)",
)

MARKET_BENCHMARKS: Dict[str, float] = {
    "PHB/PHBV wholesale (current)": 8.50,
    "PLA (polylactic acid)":        1.75,
    "Conventional PE":              1.20,
}


# ═══════════════════════════════════════════════════════════════════════════
#  ENUMS  &  RESULT DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Mode(str, Enum):
    BATCH = "Batch"
    FED_BATCH = "Fed-batch"


class Feed(str, Enum):
    H2_CO2 = "$H_2/CO_2$"
    FRUCTOSE = "Fructose"
    DLP = "DLP"
    MOLASSES = "Molasses"


class Product(str, Enum):
    PHB = "PHB"
    PHBV = "PHBV"


class TiterScenario(str, Enum):
    CONSERVATIVE = "Conservative"
    OPTIMIZED = "Optimized"


FEED_ORDER = [Feed.H2_CO2, Feed.FRUCTOSE, Feed.DLP, Feed.MOLASSES]

FEED_NOTES: Dict[Feed, str] = {
    Feed.H2_CO2:   "Autotrophic baseline — H16 wild-type, ATEX safety premium",
    Feed.FRUCTOSE: "HFCS-90 — H16 native metabolism, no pretreatment, TRL 6–7",
    Feed.DLP:      "Delactosed permeate — requires DSM545 + lactase, TRL 4–5",
    Feed.MOLASSES: "Blackstrap cane — partial H16 (fructose fraction), TRL 5–6",
}


@dataclass
class ScenarioResult:
    feed: Feed
    mode: Mode
    product: Product
    titer_scenario: TiterScenario
    capacity_tpy: float
    extraction_method: str

    annual_product_kg: float
    annual_pha_gross_kg: float
    annual_cdw_kg: float
    reactor_volume_m3: float
    effective_titer_gL: float
    phb_content_frac: float

    substrate_cost: float
    pretreatment_cost: float
    nitrogen_cost: float
    aeration_cost: float
    harvesting_cost: float
    extraction_cost: float
    drying_cost: float
    propionate_cost: float
    minor_capex_annual: float
    labor_cost: float

    total_annual_cost: float
    msp: float

    mass_flows: Dict[str, float]
    capex_included: List[Tuple[str, float, float]]
    capex_excluded: List[Tuple[str, float]]


# ═══════════════════════════════════════════════════════════════════════════
#  PARAMETER  LOOKUPS  (feed × titer-scenario)
# ═══════════════════════════════════════════════════════════════════════════

def _titer(a: Assumptions, feed: Feed, ts: TiterScenario) -> float:
    m = {
        Feed.H2_CO2:   (a.titer_h2_con,       a.titer_h2_opt),
        Feed.FRUCTOSE: (a.titer_fructose_con,  a.titer_fructose_opt),
        Feed.DLP:      (a.titer_dlp_con,       a.titer_dlp_opt),
        Feed.MOLASSES: (a.titer_molasses_con,   a.titer_molasses_opt),
    }
    return m[feed][0 if ts == TiterScenario.CONSERVATIVE else 1]


def _phb_frac(a: Assumptions, feed: Feed, ts: TiterScenario) -> float:
    m = {
        Feed.H2_CO2:   (a.phb_frac_h2_con,       a.phb_frac_h2_opt),
        Feed.FRUCTOSE: (a.phb_frac_fructose_con,  a.phb_frac_fructose_opt),
        Feed.DLP:      (a.phb_frac_dlp_con,       a.phb_frac_dlp_opt),
        Feed.MOLASSES: (a.phb_frac_molasses_con,   a.phb_frac_molasses_opt),
    }
    return m[feed][0 if ts == TiterScenario.CONSERVATIVE else 1]


def _pha_yield(a: Assumptions, feed: Feed, ts: TiterScenario) -> float:
    m = {
        Feed.H2_CO2:   (a.yield_h2_con,       a.yield_h2_opt),
        Feed.FRUCTOSE: (a.yield_fructose_con,  a.yield_fructose_opt),
        Feed.DLP:      (a.yield_dlp_con,       a.yield_dlp_opt),
        Feed.MOLASSES: (a.yield_molasses_con,   a.yield_molasses_opt),
    }
    return m[feed][0 if ts == TiterScenario.CONSERVATIVE else 1]


def _aeration_coeff(a: Assumptions, feed: Feed) -> float:
    return {
        Feed.H2_CO2:   a.aeration_kwh_m3_h_gas,
        Feed.FRUCTOSE: a.aeration_kwh_m3_h_fructose,
        Feed.DLP:      a.aeration_kwh_m3_h_dlp,
        Feed.MOLASSES: a.aeration_kwh_m3_h_molasses,
    }[feed]


def _n_reduction(a: Assumptions, feed: Feed) -> float:
    return {
        Feed.H2_CO2:   0.0,
        Feed.FRUCTOSE: a.n_reduction_fructose,
        Feed.DLP:      a.n_reduction_dlp,
        Feed.MOLASSES: a.n_reduction_molasses,
    }[feed]


def _pretreatment_rate(a: Assumptions, feed: Feed) -> float:
    return {
        Feed.H2_CO2:   0.0,
        Feed.FRUCTOSE: a.pretreatment_fructose,
        Feed.DLP:      a.pretreatment_dlp,
        Feed.MOLASSES: a.pretreatment_molasses,
    }[feed]


# ═══════════════════════════════════════════════════════════════════════════
#  MODEL  CORE
# ═══════════════════════════════════════════════════════════════════════════

def _effective_titer(a: Assumptions, mode: Mode, feed: Feed,
                     ts: TiterScenario) -> float:
    base = _titer(a, feed, ts)
    return base * a.fedbatch_titer_factor if mode == Mode.FED_BATCH else base


def _cycle_h(a: Assumptions, mode: Mode) -> float:
    if mode == Mode.FED_BATCH:
        return a.fedbatch_growth_h + a.fedbatch_accumulation_h + a.fedbatch_cip_h
    return a.batch_growth_h + a.batch_accumulation_h + a.batch_cip_h


def _fermentation_h(a: Assumptions, mode: Mode) -> float:
    if mode == Mode.FED_BATCH:
        return a.fedbatch_growth_h + a.fedbatch_accumulation_h
    return a.batch_growth_h + a.batch_accumulation_h


def _reactor_volume(a: Assumptions, mode: Mode, titer_gL: float,
                    annual_pha_gross: float) -> float:
    cycle = _cycle_h(a, mode)
    batches = a.hours_per_year / cycle
    pha_per_batch = annual_pha_gross / batches
    working_L = pha_per_batch / (titer_gL / 1000.0)
    return (working_L / 1000.0) / a.working_volume_fraction


def _aeration_kwh(a: Assumptions, mode: Mode, feed: Feed,
                  vessel_m3: float) -> float:
    coeff = _aeration_coeff(a, feed)
    broth = vessel_m3 * a.working_volume_fraction
    ferm_h = _fermentation_h(a, mode)
    cycle = _cycle_h(a, mode)
    batches = a.hours_per_year / cycle
    return batches * broth * coeff * ferm_h


def _substrate_cost(a: Assumptions, feed: Feed, product: Product,
                    ts: TiterScenario, pha_gross: float,
                    cdw_kg: float) -> Tuple[float, Dict[str, float]]:
    y = _pha_yield(a, feed, ts)
    if product == Product.PHBV:
        y *= a.phbv_yield_factor

    flows: Dict[str, float] = {}
    if feed == Feed.H2_CO2:
        h2 = pha_gross / y
        kwh = h2 * a.electrolysis_kwh_per_kg_h2
        co2 = cdw_kg * a.co2_kg_per_kg_cdw
        cost = kwh * a.electricity_price + co2 * a.co2_price_per_kg
        flows["H2 (kg/y)"] = h2
        flows["CO2 (kg/y)"] = co2
        flows["Electrolysis (kWh/y)"] = kwh
        return cost, flows
    sugar = pha_gross / y
    if feed == Feed.FRUCTOSE:
        flows["Fructose (kg/y)"] = sugar
        return sugar * a.fructose_price_per_kg, flows
    if feed == Feed.DLP:
        flows["DLP sugar (kg/y)"] = sugar
        return sugar * a.dlp_price_per_kg_sugar, flows
    flows["Molasses sugar (kg/y)"] = sugar
    return sugar * a.molasses_price_per_kg_sugar, flows


def _pretreatment_cost(a: Assumptions, feed: Feed, cdw_kg: float) -> float:
    return _pretreatment_rate(a, feed) * cdw_kg


def _nitrogen_cost(a: Assumptions, feed: Feed,
                   cdw_kg: float) -> Tuple[float, float]:
    red = _n_reduction(a, feed)
    nh4 = a.n_fraction_of_cdw * cdw_kg / a.nh4so4_n_fraction * (1.0 - red)
    return nh4 * a.nh4so4_price_per_kg, nh4


def _harvesting_cost(a: Assumptions, pha_gross: float,
                     titer_gL: float) -> float:
    broth_m3 = pha_gross / (titer_gL / 1000.0) / 1000.0
    return broth_m3 * a.centrifuge_kwh_per_m3 * a.electricity_price


def _extraction_cost(a: Assumptions,
                     product_kg: float) -> Tuple[str, float]:
    best_name, best_cost = "", float("inf")
    for name, chem, kwh, fixed, fiber_ok in a.extraction_options:
        if a.fiber_grade_required and not fiber_ok:
            continue
        cost = (chem + kwh * a.electricity_price + fixed) * product_kg
        if cost < best_cost:
            best_cost, best_name = cost, name
    return best_name, best_cost


def _drying_cost(a: Assumptions, product_kg: float) -> float:
    wet_mass = product_kg / (1.0 - a.wet_pha_moisture)
    dry_mass = product_kg / (1.0 - a.product_moisture_fraction)
    water = max(0.0, wet_mass - dry_mass)
    return water * a.drying_kwh_per_kg_water * a.electricity_price


def _propionate_cost(a: Assumptions, product: Product,
                     product_kg: float) -> float:
    if product == Product.PHB:
        return 0.0
    return product_kg * a.propionate_kg_per_kg_phbv * a.propionate_price_per_kg


def _minor_capex(a: Assumptions,
                 cap: float) -> Tuple[float, List[Tuple[str, float, float]],
                                      List[Tuple[str, float]]]:
    included: List[Tuple[str, float, float]] = []
    excluded: List[Tuple[str, float]] = []
    annual = 0.0
    for name, base, ref, exp, life in a.minor_equipment:
        scaled = base * (cap / ref) ** exp
        if scaled <= a.capex_threshold:
            a_yr = scaled / life
            included.append((name, round(scaled), round(a_yr, 2)))
            annual += a_yr
        else:
            excluded.append((name, round(scaled)))
    return annual, included, excluded


def _labor_cost(a: Assumptions, capacity_tpy: float) -> float:
    """Annual labor cost based on production scale."""
    if capacity_tpy < 1000:
        return a.labor_small_scale
    elif capacity_tpy <= 3500:
        return a.labor_medium_scale
    else:
        return a.labor_large_scale


def calculate_npv(annual_revenue: float, annual_cost: float,
                  discount_rate: float = 0.10, years: int = 10) -> float:
    """Net present value over a fixed horizon with constant annual cash flows."""
    return sum((annual_revenue - annual_cost) / (1 + discount_rate) ** t
               for t in range(1, years + 1))


# ═══════════════════════════════════════════════════════════════════════════
#  SCENARIO  RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_scenario(cap: float, feed: Feed, mode: Mode, product: Product,
                 ts: TiterScenario,
                 a: Optional[Assumptions] = None) -> ScenarioResult:
    a = a or Assumptions()
    product_kg = cap * 1_000.0
    pha_gross = product_kg / a.extraction_recovery
    frac = _phb_frac(a, feed, ts)
    cdw_kg = pha_gross / frac

    titer = _effective_titer(a, mode, feed, ts)
    vol = _reactor_volume(a, mode, titer, pha_gross)

    sub, flows = _substrate_cost(a, feed, product, ts, pha_gross, cdw_kg)
    pt = _pretreatment_cost(a, feed, cdw_kg)
    n_cost, n_kg = _nitrogen_cost(a, feed, cdw_kg)
    ae = _aeration_kwh(a, mode, feed, vol) * a.electricity_price
    harv = _harvesting_cost(a, pha_gross, titer)
    ext_name, ext_cost = _extraction_cost(a, product_kg)
    dry = _drying_cost(a, product_kg)
    prop = _propionate_cost(a, product, product_kg)
    cx, cx_in, cx_out = _minor_capex(a, cap)

    labor = _labor_cost(a, cap)
    total = sub + pt + n_cost + ae + harv + ext_cost + dry + prop + cx + labor
    flows["(NH4)2SO4 (kg/y)"] = n_kg
    flows["Aeration (kWh/y)"] = ae / max(1e-15, a.electricity_price)

    return ScenarioResult(
        feed=feed, mode=mode, product=product, titer_scenario=ts,
        capacity_tpy=cap, extraction_method=ext_name,
        annual_product_kg=product_kg, annual_pha_gross_kg=pha_gross,
        annual_cdw_kg=cdw_kg, reactor_volume_m3=vol,
        effective_titer_gL=titer, phb_content_frac=frac,
        substrate_cost=sub, pretreatment_cost=pt, nitrogen_cost=n_cost,
        aeration_cost=ae, harvesting_cost=harv, extraction_cost=ext_cost,
        drying_cost=dry, propionate_cost=prop, minor_capex_annual=cx,
        labor_cost=labor,
        total_annual_cost=total, msp=total / product_kg,
        mass_flows=flows, capex_included=cx_in, capex_excluded=cx_out,
    )


def run_all_scenarios(
    capacities: Optional[List[float]] = None,
    assumptions: Optional[Assumptions] = None,
    verbose: bool = True,
) -> List[ScenarioResult]:
    caps = capacities or DEFAULT_CAPACITIES
    n_per_cap = len(TiterScenario) * len(Product) * len(Mode) * len(FEED_ORDER)
    total = len(caps) * n_per_cap
    if verbose:
        _log(f"[pha] Running {total} scenarios "
             f"({len(caps)} caps × {len(TiterScenario)} titer × "
             f"{len(Product)} products × {len(Mode)} modes × "
             f"{len(FEED_ORDER)} feeds) ...")
    t0 = time.perf_counter()
    results: List[ScenarioResult] = []
    for i, c in enumerate(caps):
        for ts in TiterScenario:
            for prod in Product:
                for m in Mode:
                    for f in FEED_ORDER:
                        results.append(
                            run_scenario(c, f, m, prod, ts, assumptions))
        if verbose:
            done = (i + 1) * n_per_cap
            _log(f"  [{done}/{total}]  {c:>7,.0f} t/y complete")
    if verbose:
        _log(f"[pha] {len(results)} results in "
             f"{time.perf_counter() - t0:.2f} s")
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

COST_COMPONENTS = [
    "Substrate / electrolysis",
    "Pretreatment",
    "$(NH_4)_2SO_4$",
    "Aeration",
    "Extraction",
    "Harvest & dry",
    "Propionate",
    "Minor CapEx",
    "Labor",
]

COMPONENT_COLORS = {
    "Substrate / electrolysis": "#4E79A7",
    "Pretreatment":             "#76B7B2",
    "$(NH_4)_2SO_4$":          "#F28E2B",
    "Aeration":                "#59A14F",
    "Extraction":              "#E15759",
    "Harvest & dry":           "#B07AA1",
    "Propionate":              "#FF9DA7",
    "Minor CapEx":             "#9C755F",
    "Labor":                   "#D35400",
}


def cost_per_kg(r: ScenarioResult) -> Dict[str, float]:
    d = r.annual_product_kg
    return {
        "Substrate / electrolysis": r.substrate_cost / d,
        "Pretreatment":             r.pretreatment_cost / d,
        "$(NH_4)_2SO_4$":          r.nitrogen_cost / d,
        "Aeration":                r.aeration_cost / d,
        "Extraction":              r.extraction_cost / d,
        "Harvest & dry":           (r.harvesting_cost + r.drying_cost) / d,
        "Propionate":              r.propionate_cost / d,
        "Minor CapEx":             r.minor_capex_annual / d,
        "Labor":                   r.labor_cost / d,
    }


def _filt(results: List[ScenarioResult], **kw) -> List[ScenarioResult]:
    out = results
    for k, v in kw.items():
        out = [r for r in out if getattr(r, k) == v]
    return out


def _get(results: List[ScenarioResult], cap: float, feed: Feed, mode: Mode,
         product: Product = Product.PHB,
         ts: TiterScenario = TiterScenario.OPTIMIZED) -> ScenarioResult:
    for r in results:
        if (r.capacity_tpy == cap and r.feed == feed and r.mode == mode
                and r.product == product and r.titer_scenario == ts):
            return r
    raise KeyError(f"No result for {cap}/{feed}/{mode}/{product}/{ts}")


def best_by_capacity(
    results: List[ScenarioResult],
    product: Product = Product.PHB,
    ts: TiterScenario = TiterScenario.OPTIMIZED,
) -> Dict[float, ScenarioResult]:
    filt = _filt(results, product=product, titer_scenario=ts)
    out: Dict[float, ScenarioResult] = {}
    for r in filt:
        if r.capacity_tpy not in out or r.msp < out[r.capacity_tpy].msp:
            out[r.capacity_tpy] = r
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  TEXT  REPORT
# ═══════════════════════════════════════════════════════════════════════════

def format_report(results: List[ScenarioResult]) -> str:
    lines: List[str] = []

    phb_opt = _filt(results, product=Product.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    phb_opt.sort(key=lambda r: (r.capacity_tpy, r.mode.value, r.feed.value))

    hdr = (f"{'Cap (t/y)':>10}  {'Mode':>10}  {'Feed':>10}  "
           f"{'MSP':>9}  {'Titer':>7}  {'V (m³)':>8}  {'Extraction'}")
    sep = "─" * len(hdr)
    lines.extend([sep, "PHB — Optimized Titers", sep, hdr, sep])
    for r in phb_opt:
        lines.append(
            f"{r.capacity_tpy:>10,.0f}  {r.mode.value:>10}  "
            f"{r.feed.value:>10}  ${r.msp:>7.3f}  "
            f"{r.effective_titer_gL:>6.1f}  {r.reactor_volume_m3:>8.0f}  "
            f"{r.extraction_method}")
    lines.append(sep)

    lines.append("")
    lines.append("Lowest MSP per capacity (PHB optimized):")
    for cap, r in sorted(best_by_capacity(results).items()):
        lines.append(
            f"  {cap:>7,.0f} t/y  →  {r.feed.value} / {r.mode.value}"
            f"  →  ${r.msp:.3f}/kg dry PHA")

    lines.append("")
    lines.append("PHBV premium at 3,500 t/y fed-batch (optimized):")
    for feed in FEED_ORDER:
        try:
            phb = _get(results, 3500, feed, Mode.FED_BATCH,
                       Product.PHB, TiterScenario.OPTIMIZED)
            phbv = _get(results, 3500, feed, Mode.FED_BATCH,
                        Product.PHBV, TiterScenario.OPTIMIZED)
            delta = phbv.msp - phb.msp
            lines.append(
                f"  {feed.value:>10}  PHB ${phb.msp:.3f}  "
                f"PHBV ${phbv.msp:.3f}  Δ +${delta:.3f}/kg")
        except KeyError:
            pass

    lines.append("")
    a_rpt = Assumptions()
    pv_factor = sum(1.0 / (1.0 + a_rpt.npv_discount_rate) ** t
                    for t in range(1, a_rpt.npv_years + 1))
    lines.append(f"NPV at market prices ({a_rpt.npv_years}-yr, "
                 f"{int(a_rpt.npv_discount_rate*100)}% discount):")
    for cap_val, r in sorted(best_by_capacity(results).items()):
        for bench_label, bench_price in MARKET_BENCHMARKS.items():
            rev = r.annual_product_kg * bench_price
            npv = (rev - r.total_annual_cost) * pv_factor
            lines.append(
                f"  {cap_val:>7,.0f} t/y @ {bench_label} (${bench_price:.2f}/kg): "
                f"NPV ${npv / 1e6:>8.2f} M")
        lines.append("")
    lines.append("Labor costs included:")
    for cap_val in sorted({r.capacity_tpy for r in results}):
        labor = _labor_cost(a_rpt, cap_val)
        lines.append(f"  {cap_val:>7,.0f} t/y  →  ${labor / 1e6:.1f} M/year"
                     f"  (${labor / (cap_val * 1000):.2f}/kg)")
    lines.append("")
    lines.append("Strain compatibility notes:")
    for feed, note in FEED_NOTES.items():
        lines.append(f"  {feed.value:>10}  {note}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  SENSITIVITY  ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

_FEED_KEY = {
    Feed.H2_CO2: "h2", Feed.FRUCTOSE: "fructose",
    Feed.DLP: "dlp", Feed.MOLASSES: "molasses",
}


def _sensitivity_params(feed: Feed,
                        ts: TiterScenario) -> List[Tuple[str, str]]:
    suf = "_con" if ts == TiterScenario.CONSERVATIVE else "_opt"
    fk = _FEED_KEY[feed]

    params: List[Tuple[str, str]] = [
        ("Extraction recovery", "extraction_recovery"),
        ("$(NH_4)_2SO_4$ price",    "nh4so4_price_per_kg"),
        ("Electricity price",   "electricity_price"),
        ("PHB yield",           f"yield_{fk}{suf}"),
        ("PHB titer",           f"titer_{fk}{suf}"),
        ("PHB content",         f"phb_frac_{fk}{suf}"),
    ]
    if feed == Feed.H2_CO2:
        params.append(("Electrolyser eff.", "electrolysis_kwh_per_kg_h2"))
        params.append(("Aeration power", "aeration_kwh_m3_h_gas"))
    elif feed == Feed.FRUCTOSE:
        params.append(("Fructose price", "fructose_price_per_kg"))
        params.append(("Aeration power", "aeration_kwh_m3_h_fructose"))
    elif feed == Feed.DLP:
        params.extend([
            ("DLP sugar price",   "dlp_price_per_kg_sugar"),
            ("Pretreatment (DLP)","pretreatment_dlp"),
            ("N reduction (DLP)", "n_reduction_dlp"),
            ("Aeration power",    "aeration_kwh_m3_h_dlp"),
        ])
    elif feed == Feed.MOLASSES:
        params.extend([
            ("Molasses price",     "molasses_price_per_kg_sugar"),
            ("Pretreatment",       "pretreatment_molasses"),
            ("Aeration power",     "aeration_kwh_m3_h_molasses"),
        ])
    return params


def run_sensitivity(
    cap: float, feed: Feed, mode: Mode,
    product: Product = Product.PHB,
    ts: TiterScenario = TiterScenario.OPTIMIZED,
    base: Optional[Assumptions] = None,
    delta: float = 0.20,
) -> List[Tuple[str, float, float, float]]:
    base = base or Assumptions()
    msp0 = run_scenario(cap, feed, mode, product, ts, base).msp
    params = list(_sensitivity_params(feed, ts))
    if cap < 1000:
        params.append(("Labor cost", "labor_small_scale"))
    elif cap <= 3500:
        params.append(("Labor cost", "labor_medium_scale"))
    else:
        params.append(("Labor cost", "labor_large_scale"))
    rows: List[Tuple[str, float, float, float]] = []
    for label, fld in params:
        v0 = getattr(base, fld)
        if v0 == 0.0:
            continue
        lo = run_scenario(cap, feed, mode, product, ts,
                          replace(base, **{fld: v0 * (1 - delta)})).msp
        hi = run_scenario(cap, feed, mode, product, ts,
                          replace(base, **{fld: v0 * (1 + delta)})).msp
        rows.append((label, lo, msp0, hi))
    rows.sort(key=lambda t: abs(t[3] - t[1]), reverse=True)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE  STYLE
# ═══════════════════════════════════════════════════════════════════════════

FEED_COLORS: Dict[Feed, str] = {
    Feed.H2_CO2:   "#0072B2",
    Feed.FRUCTOSE: "#E69F00",
    Feed.DLP:      "#009E73",
    Feed.MOLASSES: "#CC79A7",
}


def _apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi":        120,
        "savefig.dpi":       300,
        "savefig.bbox":      "tight",
        "font.family":       "sans-serif",
        "font.sans-serif":   ["Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size":         11,
        "axes.titlesize":    14,
        "axes.titleweight":  "600",
        "axes.labelsize":    12,
        "axes.edgecolor":    "#333333",
        "axes.linewidth":    0.8,
        "axes.grid":         True,
        "axes.axisbelow":    True,
        "axes.facecolor":    "#FAFAFA",
        "grid.alpha":        0.30,
        "grid.linewidth":    0.5,
        "figure.facecolor":  "white",
        "legend.frameon":    True,
        "legend.framealpha":  0.95,
        "legend.edgecolor":  "#CCCCCC",
    })


_DISCLAIMER = (
    "OPEX + minor CapEx (<$100 k/unit) + labor MSP proxy · fiber-grade extraction "
    "(SDS+acetone) · excludes steam, major CapEx · "
    "feedstock data: PhycoVax TEA Framework (Mar 2026)"
)


def _stamp(fig: plt.Figure) -> None:
    fig.text(0.5, -0.03, _DISCLAIMER,
             ha="center", fontsize=7, color="#777777", style="italic")


def _add_benchmarks(ax: plt.Axes, ymax: float) -> None:
    for label, price in MARKET_BENCHMARKS.items():
        if price < ymax * 1.5:
            ax.axhline(price, ls="--", lw=0.7, color="#999999", zorder=1)
            ax.text(ax.get_xlim()[1] * 0.98, price + ymax * 0.008,
                    label, fontsize=6.5, color="#666666",
                    ha="right", va="bottom")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURES
# ═══════════════════════════════════════════════════════════════════════════

# ---------- 1. MSP overview — PHB optimized (Batch | Fed-batch) ----------

def fig_msp_overview(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    sub = _filt(results, product=Product.PHB,
                titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy for r in sub})
    n_feeds = len(FEED_ORDER)
    x = np.arange(len(caps))
    w = 0.80 / n_feeds

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), sharey=True)
    for ax, mode in zip(axes, [Mode.BATCH, Mode.FED_BATCH]):
        for i, feed in enumerate(FEED_ORDER):
            vals = [_get(sub, c, feed, mode).msp for c in caps]
            offset = (i - (n_feeds - 1) / 2) * w
            bars = ax.bar(x + offset, vals, w, label=feed.value,
                          color=FEED_COLORS[feed], edgecolor="white",
                          linewidth=0.6, zorder=3)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02,
                        f"${v:.2f}", ha="center", va="bottom", fontsize=6.2)

        ymax = ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 5
        _add_benchmarks(ax, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{int(c):,}" for c in caps])
        ax.set_xlabel("Capacity (t/y dry PHA)")
        ax.set_title(mode.value, pad=10)
        ax.legend(title="Feedstock", fontsize=8, loc="upper right")

    axes[0].set_ylabel("MSP (USD / kg dry PHB)")
    fig.suptitle("Minimum Sales Price — PHB (optimized titers)",
                 fontsize=15, fontweight="bold", y=1.03)
    fig.subplots_adjust(wspace=0.08)
    _stamp(fig)
    return fig


# ---------- 2. Conservative vs Optimized --------------------------------

def fig_con_vs_opt(results: List[ScenarioResult],
                   cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(FEED_ORDER))
    w = 0.30

    for j, (ts, label, alpha) in enumerate([
        (TiterScenario.CONSERVATIVE, "Conservative", 0.55),
        (TiterScenario.OPTIMIZED,    "Optimized",    1.00),
    ]):
        vals = []
        for feed in FEED_ORDER:
            r = _get(results, cap, feed, Mode.FED_BATCH,
                     Product.PHB, ts)
            vals.append(r.msp)
        offset = (j - 0.5) * w
        bars = ax.bar(x + offset, vals, w, label=label, alpha=alpha,
                      color=[FEED_COLORS[f] for f in FEED_ORDER],
                      edgecolor="white", linewidth=0.6, zorder=3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02,
                    f"${v:.2f}", ha="center", va="bottom", fontsize=8.5,
                    fontweight="600")

    _add_benchmarks(ax, ax.get_ylim()[1])
    ax.set_xticks(x)
    ax.set_xticklabels([f.value for f in FEED_ORDER], fontsize=11)
    ax.set_ylabel("MSP (USD / kg dry PHB)")
    ax.set_title(f"Optimization opportunity — PHB fed-batch at "
                 f"{int(cap):,} t/y", pad=12)
    ax.legend(fontsize=10, loc="upper right")
    _stamp(fig)
    return fig


# ---------- 3. PHB vs PHBV comparison -----------------------------------

def fig_phb_vs_phbv(results: List[ScenarioResult],
                    cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(FEED_ORDER))
    w = 0.30

    for j, (prod, hatch) in enumerate([
        (Product.PHB,  None),
        (Product.PHBV, "//"),
    ]):
        vals = []
        for feed in FEED_ORDER:
            r = _get(results, cap, feed, Mode.FED_BATCH,
                     prod, TiterScenario.OPTIMIZED)
            vals.append(r.msp)
        offset = (j - 0.5) * w
        bars = ax.bar(x + offset, vals, w, label=prod.value,
                      color=[FEED_COLORS[f] for f in FEED_ORDER],
                      edgecolor="#333333" if hatch else "white",
                      linewidth=0.6, hatch=hatch, zorder=3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02,
                    f"${v:.2f}", ha="center", va="bottom", fontsize=8.5,
                    fontweight="600")

    _add_benchmarks(ax, ax.get_ylim()[1])
    ax.set_xticks(x)
    ax.set_xticklabels([f.value for f in FEED_ORDER], fontsize=11)
    ax.set_ylabel("MSP (USD / kg dry PHA)")
    ax.set_title(f"PHB vs PHBV — fed-batch optimized at {int(cap):,} t/y",
                 pad=12)
    ax.legend(fontsize=10, loc="upper right")
    _stamp(fig)
    return fig


# ---------- 4. Cost structure (stacked horizontal bars) ------------------

def fig_cost_structure(results: List[ScenarioResult],
                       cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    subset = _filt(results, capacity_tpy=cap, product=Product.PHB,
                   titer_scenario=TiterScenario.OPTIMIZED)
    subset.sort(key=lambda r: (list(Mode).index(r.mode),
                               FEED_ORDER.index(r.feed)))
    labels = [f"{r.feed.value} — {r.mode.value}" for r in subset]
    comps = [c for c in COST_COMPONENTS if c != "Propionate"]
    data = np.array([[cost_per_kg(r)[k] for k in comps] for r in subset])

    fig, ax = plt.subplots(figsize=(13, 7))
    y = np.arange(len(subset))
    left = np.zeros(len(subset))
    for j, comp in enumerate(comps):
        vals = data[:, j]
        ax.barh(y, vals, left=left, label=comp,
                color=COMPONENT_COLORS[comp],
                edgecolor="white", linewidth=0.5, height=0.55)
        for bi, (v, l) in enumerate(zip(vals, left)):
            if v > 0.02:
                ax.text(l + v / 2, y[bi], f"${v:.2f}",
                        ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold")
        left += vals

    for i, total in enumerate(left):
        ax.text(total + 0.01, i, f"${total:.2f}", va="center",
                fontsize=9, fontweight="600")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("MSP contribution (USD / kg dry PHB)")
    ax.set_title(f"PHB cost structure (optimized) — {int(cap):,} t/y",
                 pad=12)
    ax.legend(loc="lower right", fontsize=7.5, ncol=2)
    ax.set_xlim(0, float(left.max()) * 1.12)
    fig.subplots_adjust(left=0.24, bottom=0.15)
    _stamp(fig)
    return fig


# ---------- 5. Sensitivity tornado  -------------------------------------

def fig_sensitivity(results: List[ScenarioResult],
                    cap: float = 3_500.0,
                    delta: float = 0.20) -> plt.Figure:
    _apply_style()
    phb_opt = _filt(results, capacity_tpy=cap, product=Product.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    best = min(phb_opt, key=lambda r: r.msp)
    rows = run_sensitivity(cap, best.feed, best.mode, delta=delta)

    fig, ax = plt.subplots(figsize=(11.5, 7))
    y_arr = np.arange(len(rows))
    msp0 = rows[0][2]
    for i, (label, lo, _, hi) in enumerate(rows):
        left_val = min(lo, hi) - msp0
        width = abs(hi - lo)
        colour = "#4E79A7" if hi > lo else "#E15759"
        ax.barh(i, width, left=msp0 + left_val, height=0.55, color=colour,
                edgecolor="white", linewidth=0.5)
        ax.text(min(lo, hi) - 0.003, i, f"${min(lo, hi):.3f}",
                ha="right", va="center", fontsize=8)
        ax.text(max(lo, hi) + 0.003, i, f"${max(lo, hi):.3f}",
                ha="left", va="center", fontsize=8)

    ax.axvline(msp0, color="#333333", lw=1.2, ls="-", zorder=4)
    ax.text(msp0, len(rows) + 0.3, f"Base MSP ${msp0:.3f}/kg",
            ha="center", fontsize=9, fontweight="600")

    ax.set_yticks(y_arr)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("MSP (USD / kg dry PHB)")
    ax.set_title(
        f"Sensitivity (±{int(delta*100)}%) — {best.feed.value} / "
        f"{best.mode.value} at {int(cap):,} t/y",
        pad=12,
    )
    fig.subplots_adjust(left=0.26, bottom=0.14)
    _stamp(fig)
    return fig


# ---------- 6. Scale curve (MSP vs capacity) ----------------------------

def fig_scale_curve(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    sub = _filt(results, product=Product.PHB,
                titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy for r in sub})

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for feed in FEED_ORDER:
        msps = []
        for c in caps:
            best = min((r for r in sub
                        if r.capacity_tpy == c and r.feed == feed),
                       key=lambda r: r.msp)
            msps.append(best.msp)
        ax.plot(caps, msps, marker="o", markersize=8, linewidth=2.4,
                label=feed.value, color=FEED_COLORS[feed], zorder=3)
        for c, v in zip(caps, msps):
            ax.annotate(f"${v:.2f}", (c, v), textcoords="offset points",
                        xytext=(6, 6), fontsize=7.5)

    for label, price in MARKET_BENCHMARKS.items():
        ax.axhline(price, ls=":", lw=0.8, color="#aaaaaa", zorder=1)
        ax.text(caps[0] * 0.85, price, f"  {label} (${price:.2f})",
                fontsize=7, color="#888888", va="center")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda val, _: f"{int(val):,}"))
    ax.set_xticks(caps)
    ax.set_xlabel("Plant capacity (t/y sellable dry PHA)")
    ax.set_ylabel("MSP (USD / kg dry PHB) — best mode per feed")
    ax.set_title("PHA economies of scale (optimized titers)", pad=12)
    ax.legend(title="Feedstock", fontsize=9, loc="upper right")
    fig.subplots_adjust(bottom=0.16)
    _stamp(fig)
    return fig


# ---------- 7. NPV vs scale  -------------------------------------------

def fig_npv_vs_scale(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    a = Assumptions()
    r_disc = a.npv_discount_rate
    n_yr = a.npv_years
    pv_factor = sum(1.0 / (1.0 + r_disc) ** t for t in range(1, n_yr + 1))

    phb_opt = _filt(results, product=Product.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy for r in phb_opt})

    ref_prices = [
        ("PLA parity ($1.75/kg)",        1.75, "-",  1.00),
        ("PHB wholesale ($8.50/kg)",      8.50, "--", 0.80),
        ("Specialty biopolymer ($15/kg)", 15.0, ":",  0.60),
    ]

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        for price_label, price_val, ls, alpha in ref_prices:
            npvs = []
            for c in caps:
                subset = [r for r in phb_opt
                          if r.capacity_tpy == c and r.feed == feed]
                best = min(subset, key=lambda r: r.msp)
                npv = (best.annual_product_kg * price_val
                       - best.total_annual_cost) * pv_factor / 1e6
                npvs.append(npv)
            ax.plot(caps, npvs, linestyle=ls, linewidth=1.8,
                    marker="o", markersize=5, color=FEED_COLORS[feed],
                    alpha=alpha, zorder=3)

    ax.axhline(0, color="#333333", lw=1.0, ls="-", zorder=2)

    from matplotlib.lines import Line2D
    feed_handles = [Line2D([0], [0], color=FEED_COLORS[f], linewidth=2.0,
                           label=f.value) for f in FEED_ORDER]
    price_handles = [Line2D([0], [0], color="#555555", linestyle=ls,
                            linewidth=1.6, alpha=alpha, label=lbl)
                     for lbl, _, ls, alpha in ref_prices]
    legend1 = ax.legend(handles=feed_handles, title="Feedstock",
                        fontsize=8.5, loc="upper left")
    ax.add_artist(legend1)
    ax.legend(handles=price_handles, title="Selling price",
              fontsize=8.0, loc="lower right")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda val, _: f"{int(val):,}"))
    ax.set_xticks(caps)
    ax.set_xlabel("Plant capacity (t/y dry PHA)")
    ax.set_ylabel(f"NPV (USD millions, {n_yr}-year, {int(r_disc*100)}% discount)")
    ax.set_title(
        f"PHB NPV vs Scale — optimized titers, all feedstocks & reference prices\n"
        f"({n_yr}-yr horizon, {int(r_disc*100)}% discount, best mode per feed, $2M/yr labor)",
        pad=12,
    )
    fig.subplots_adjust(bottom=0.16)
    _stamp(fig)
    return fig


# ---------- 7. NPV analysis  --------------------------------------------

def fig_npv_analysis(results: List[ScenarioResult],
                     cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    a = Assumptions()
    r_disc = a.npv_discount_rate
    n_yr = a.npv_years
    pv_factor = sum(1.0 / (1.0 + r_disc) ** t for t in range(1, n_yr + 1))

    phb_opt = _filt(results, product=Product.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    price_max = max(MARKET_BENCHMARKS.values()) * 1.4
    prices = np.linspace(0, price_max, 300)

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        subset = [r for r in phb_opt
                  if r.capacity_tpy == cap and r.feed == feed]
        best = min(subset, key=lambda r: r.msp)
        npvs = [(best.annual_product_kg * p - best.total_annual_cost)
                * pv_factor / 1e6 for p in prices]
        ax.plot(prices, npvs, linewidth=2.4, label=feed.value,
                color=FEED_COLORS[feed], zorder=3)
        ax.plot(best.msp, 0, "o", color=FEED_COLORS[feed], markersize=10,
                zorder=5, markeredgecolor="white", markeredgewidth=1.5)
        ax.annotate(f"MSP ${best.msp:.2f}", (best.msp, 0),
                    textcoords="offset points", xytext=(8, 10),
                    fontsize=8, fontweight="600", color=FEED_COLORS[feed])

    ax.axhline(0, color="#333333", lw=1.0, ls="-", zorder=2)

    for label, price in MARKET_BENCHMARKS.items():
        if price <= price_max:
            ax.axvline(price, ls=":", lw=0.8, color="#aaaaaa", zorder=1)
            ylim = ax.get_ylim()
            ax.text(price + 0.05, ylim[1] * 0.9, label,
                    fontsize=7, color="#888888", rotation=90, va="top")

    ax.set_xlabel("Selling price (USD / kg dry PHA)")
    ax.set_ylabel(f"NPV (USD millions, {n_yr}-year, {int(r_disc*100)}% discount)")
    ax.set_title(
        f"Net Present Value vs Selling Price — PHB at {int(cap):,} t/y\n"
        f"(optimized titers, best mode per feed, includes labor)",
        pad=12,
    )
    ax.legend(title="Feedstock", fontsize=9, loc="upper left")
    fig.subplots_adjust(bottom=0.15)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE  ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

def create_all_figures(
    results: List[ScenarioResult],
    save_dir: Optional[str | Path] = None,
    show: bool = False,
    verbose: bool = True,
) -> Dict[str, plt.Figure]:
    _apply_style()
    specs = [
        "01_pha_msp_overview",
        "02_conservative_vs_optimized",
        "03_phb_vs_phbv",
        "04_pha_cost_structure",
        "05_pha_sensitivity",
        "06_pha_scale_curve",
        "07_pha_npv_vs_scale",
        "08_pha_npv_analysis",
    ]
    builders = [
        lambda: fig_msp_overview(results),
        lambda: fig_con_vs_opt(results),
        lambda: fig_phb_vs_phbv(results),
        lambda: fig_cost_structure(results),
        lambda: fig_sensitivity(results),
        lambda: fig_scale_curve(results),
        lambda: fig_npv_vs_scale(results),
        lambda: fig_npv_analysis(results),
    ]

    figs: Dict[str, plt.Figure] = {}
    t_all = time.perf_counter()
    if verbose:
        _log("[pha] Building figures ...")

    for name, builder in zip(specs, builders):
        if verbose:
            _log(f"  [fig] {name} ...")
        t0 = time.perf_counter()
        figs[name] = builder()
        if verbose:
            _log(f"  [fig] {name} done ({time.perf_counter() - t0:.1f} s)")

    if verbose:
        _log(f"[pha] Figures complete — "
             f"{time.perf_counter() - t_all:.1f} s total")

    if save_dir is not None:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        if verbose:
            _log(f"[pha] Saving PNGs to {out.resolve()} ...")
        for name, fig in figs.items():
            p = out / f"{name}.png"
            fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
            if verbose:
                _log(f"  [save] {p.name}")
        if verbose:
            _log("[pha] Save complete.")

    if show:
        plt.show()

    return figs


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY  POINT
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    _log("[pha] C. necator PHA bioplastic TEA ($2M labor, 8% NPV, 80 g/L CDW basis)")
    _log("=" * 56)
    results = run_all_scenarios()
    print()
    print(format_report(results))
    print()
    print("Major CapEx items EXCLUDED (>$100 k/unit — review later):")
    for item in MAJOR_CAPEX_EXCLUDED:
        print(f"  • {item}")
    print()
    print("Minor CapEx INCLUDED at 50 t/y (H2/CO2, Batch):")
    ref = next(r for r in results
               if r.capacity_tpy == 50 and r.feed == Feed.H2_CO2
               and r.mode == Mode.BATCH and r.product == Product.PHB
               and r.titer_scenario == TiterScenario.OPTIMIZED)
    for name, purchase, annual in ref.capex_included:
        print(f"  • {name:32s}  ${purchase:>8,.0f}  →  ${annual:>7,.0f}/y")
    for name, purchase in ref.capex_excluded:
        print(f"  ✗ {name:32s}  ${purchase:>8,.0f}  (EXCEEDS)")
    print()
    print(f"Extraction method selected: {ref.extraction_method}")
    print(f"  (fiber-grade required = {ref.extraction_method != 'NaOCl digestion'},"
          f" preserves Mw >300 kDa for thread spinning)")
    print()
    _log("[pha] Generating figures ...")
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        script_dir = Path(".")
    create_all_figures(results, save_dir=script_dir / "pha_80gL_figures")
    _log("[pha] Done.")


# ── Jupyter quick-start ────────────────────────────────────────────────────
#
# Paste this file into one cell and run.  Then in the next cell:
#
#     results = run_all_scenarios()
#     figs    = create_all_figures(results)          # inline display
#     # figs  = create_all_figures(results,
#     #             save_dir="pha_figures")           # also save PNGs
#
# To tweak an assumption:
#     a = Assumptions(yield_dlp_opt=0.42, dlp_price_per_kg_sugar=0.10)
#     results = run_all_scenarios(assumptions=a)
#     figs    = create_all_figures(results)
#
# To compare just PHB optimized fed-batch:
#     phb_opt_fb = [r for r in results
#                   if r.product.value == "PHB"
#                   and r.titer_scenario.value == "Optimized"
#                   and r.mode.value == "Fed-batch"]
#     for r in sorted(phb_opt_fb, key=lambda r: r.msp):
#         print(f"{r.feed.value:>10}  {r.capacity_tpy:>7,.0f} t/y"
#               f"  ${r.msp:.3f}/kg")

if __name__ == "__main__":
    main()
