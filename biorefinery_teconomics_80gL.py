#!/usr/bin/env python3
"""
Technoeconomic Model — Combined Biorefinery: PHA Bioplastic + SCP Co-production
=================================================================================

Concept:
  C. necator fermentation → CDW (containing intracellular PHB/PHBV)
    → Extract PHB/PHBV  → fiber-grade bioplastic powder
    → Process residual  → SCP powder (animal feed grade, ~55% protein)

Two sellable co-products from each batch:
  1. PHB or PHBV bioplastic (fiber-grade, high Mw for thread spinning)
  2. Residual cell biomass as SCP (animal feed grade, dried powder)

Capacity basis: tonnes CDW per year (fermenter output)
  PHB output  = CDW × PHB_content × extraction_recovery
  SCP output  = (CDW − PHB_recovered) × scp_recovery

Feedstock cases (PhycoVax TEA Framework, March 2026):
  1. H₂/CO₂ — autotrophic baseline
  2. Fructose (HFCS-90) — H16 native
  3. DLP (delactosed permeate) — requires DSM545
  4. Blackstrap molasses — partial H16

Modes      : Batch  and  Fed-batch
Polymers   : PHB  and  PHBV (with propionate co-feed)
Titer scen.: Conservative (PDF)  and  Optimized (literature)
Capacities : 50  /  350  /  3,500  /  7,000  t/y CDW

Output     : PHB MSP with SCP credit, standalone PHB MSP,
             SCP MSP with PHB credit, blended MSP,
             combined revenue per batch at market prices
             Net Present Value (NPV) at 8% discount over 10 years
             (all costs include labor)

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
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ═══════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def _log(msg: str) -> None:
    print(msg, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  ASSUMPTIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Assumptions:
    """All tuneable parameters for the combined biorefinery model."""

    # ── Product specification — PHA ──────────────────────────────────────
    extraction_recovery: float = 0.88
    pha_product_moisture: float = 0.05

    # ── Product specification — SCP (animal feed) ────────────────────────
    scp_recovery: float = 0.85
    scp_wash_cost_per_kg: float = 0.05
    scp_cake_moisture: float = 0.78
    scp_product_moisture: float = 0.08
    scp_drying_kwh_per_kg_water: float = 1.15
    scp_protein_fraction: float = 0.55

    # ── Market prices (for co-product credit calculations) ───────────────
    phb_market_price: float = 1.75
    scp_market_price: float = 2.00

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

    # ── PHBV co-substrate ────────────────────────────────────────────────
    phbv_yield_factor: float = 0.92
    propionate_kg_per_kg_phbv: float = 0.08
    propionate_price_per_kg: float = 1.20

    # ── CO₂ / H₂ ────────────────────────────────────────────────────────
    co2_kg_per_kg_cdw: float = 1.83
    co2_price_per_kg: float = 0.00
    electricity_price: float = 0.03
    electrolysis_kwh_per_kg_h2: float = 52.0

    # ── Sugar prices ─────────────────────────────────────────────────────
    fructose_price_per_kg: float = 0.375
    dlp_price_per_kg_sugar: float = 0.13
    molasses_price_per_kg_sugar: float = 0.155

    # ── Pretreatment ($/kg CDW) ──────────────────────────────────────────
    pretreatment_fructose: float = 0.00
    pretreatment_dlp: float = 0.07
    pretreatment_molasses: float = 0.02

    # ── Nitrogen ─────────────────────────────────────────────────────────
    n_fraction_of_cdw: float = 0.08
    nh4so4_n_fraction: float = 0.212
    nh4so4_price_per_kg: float = 0.42
    n_reduction_fructose: float = 0.00
    n_reduction_dlp: float = 1.00
    n_reduction_molasses: float = 0.20

    # ── Aeration ─────────────────────────────────────────────────────────
    aeration_kwh_m3_h_gas: float = 0.55
    aeration_kwh_m3_h_fructose: float = 0.85
    aeration_kwh_m3_h_dlp: float = 0.85
    aeration_kwh_m3_h_molasses: float = 0.95

    # ── Harvesting ───────────────────────────────────────────────────────
    centrifuge_kwh_per_m3: float = 1.2

    # ── PHA extraction (fiber-grade) ─────────────────────────────────────
    extraction_options: Tuple[Tuple[str, float, float, float, bool], ...] = (
        ("NaOCl digestion",       0.18, 1.5, 0.08, False),
        ("SDS + acetone wash",    0.35, 2.5, 0.10, True),
        ("Chloroform extraction", 0.55, 4.5, 0.18, True),
        ("Enzymatic lysis",       0.45, 2.0, 0.10, True),
    )
    fiber_grade_required: bool = True

    # ── PHA drying ───────────────────────────────────────────────────────
    pha_drying_kwh_per_kg_water: float = 1.2
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
        ("SCP wash / rinse tank",       6_000, 50, 0.60, 15),
    )

    # ── Labor (annual cost by production scale) ─────────────────────────
    labor_small_scale: float = 2_000_000.0    # <1,000 t/y CDW
    labor_medium_scale: float = 2_000_000.0   # 3,500 t/y CDW (capped at $2 M)
    labor_large_scale: float = 2_000_000.0    # 7,000 t/y CDW (capped at $2 M)

    # ── NPV parameters ──────────────────────────────────────────────────────
    npv_discount_rate: float = 0.08
    npv_years: int = 10

    hours_per_year: float = 8_760.0


DEFAULT_CAPACITIES: List[float] = [50.0, 350.0, 3_500.0, 7_000.0]

MAJOR_CAPEX_EXCLUDED: Tuple[str, ...] = (
    "Production bioreactor(s) + SIP/CIP sterility",
    "Industrial disc-stack centrifuge(s) (harvest + SCP wash)",
    "PHA extraction vessels + solvent recovery column",
    "Spray dryer / belt dryer (PHA line)",
    "Belt dryer (SCP line)",
    "Electrolyser stack + rectifiers (H₂ case)",
    "Cold storage / warehouse",
    "Wastewater treatment system",
    "Lactase UF recycle skid (DLP only)",
)

MARKET_BENCHMARKS: Dict[str, float] = {
    "PHB wholesale (current)": 8.50,
    "PHB at PLA price (modelled)": 1.75,
    "PLA (polylactic acid)":   1.75,
    "Conventional PE":         1.20,
}


# ═══════════════════════════════════════════════════════════════════════════
#  ENUMS  &  RESULT
# ═══════════════════════════════════════════════════════════════════════════

class Mode(str, Enum):
    BATCH = "Batch"
    FED_BATCH = "Fed-batch"

class Feed(str, Enum):
    H2_CO2 = "$H_2/CO_2$"
    FRUCTOSE = "Fructose"
    DLP = "DLP"
    MOLASSES = "Molasses"

class PolymerType(str, Enum):
    PHB = "PHB"
    PHBV = "PHBV"

class TiterScenario(str, Enum):
    CONSERVATIVE = "Conservative"
    OPTIMIZED = "Optimized"

FEED_ORDER = [Feed.H2_CO2, Feed.FRUCTOSE, Feed.DLP, Feed.MOLASSES]

FEED_NOTES: Dict[Feed, str] = {
    Feed.H2_CO2:   "Autotrophic — H16 wild-type",
    Feed.FRUCTOSE: "HFCS-90 — H16 native, TRL 6–7",
    Feed.DLP:      "Delactosed permeate — needs DSM545 + lactase, TRL 4–5",
    Feed.MOLASSES: "Blackstrap cane — partial H16, TRL 5–6",
}


@dataclass
class ScenarioResult:
    feed: Feed
    mode: Mode
    polymer: PolymerType
    titer_scenario: TiterScenario
    capacity_tpy_cdw: float
    extraction_method: str

    annual_cdw_kg: float
    annual_pha_product_kg: float
    annual_scp_product_kg: float
    annual_total_product_kg: float
    reactor_volume_m3: float
    effective_phb_titer_gL: float
    phb_content_frac: float

    substrate_cost: float
    pretreatment_cost: float
    nitrogen_cost: float
    aeration_cost: float
    harvesting_cost: float
    extraction_cost: float
    pha_drying_cost: float
    propionate_cost: float
    scp_processing_cost: float
    scp_drying_cost: float
    minor_capex_annual: float
    labor_cost: float

    total_annual_cost: float

    pha_msp_with_scp_credit: float
    pha_msp_standalone: float
    scp_msp_with_pha_credit: float
    blended_msp: float
    biorefinery_advantage: float

    pha_revenue_at_market: float
    scp_revenue_at_market: float
    total_revenue_at_market: float
    gross_margin: float

    batches_per_year: float
    cdw_per_batch_kg: float
    pha_per_batch_kg: float
    scp_per_batch_kg: float
    cost_per_batch: float
    revenue_per_batch: float

    mass_flows: Dict[str, float]
    capex_included: List[Tuple[str, float, float]]
    capex_excluded: List[Tuple[str, float]]


# ═══════════════════════════════════════════════════════════════════════════
#  PARAMETER  LOOKUPS
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
    return {Feed.H2_CO2: a.aeration_kwh_m3_h_gas,
            Feed.FRUCTOSE: a.aeration_kwh_m3_h_fructose,
            Feed.DLP: a.aeration_kwh_m3_h_dlp,
            Feed.MOLASSES: a.aeration_kwh_m3_h_molasses}[feed]

def _n_reduction(a: Assumptions, feed: Feed) -> float:
    return {Feed.H2_CO2: 0.0, Feed.FRUCTOSE: a.n_reduction_fructose,
            Feed.DLP: a.n_reduction_dlp, Feed.MOLASSES: a.n_reduction_molasses}[feed]

def _pretreatment_rate(a: Assumptions, feed: Feed) -> float:
    return {Feed.H2_CO2: 0.0, Feed.FRUCTOSE: a.pretreatment_fructose,
            Feed.DLP: a.pretreatment_dlp, Feed.MOLASSES: a.pretreatment_molasses}[feed]


# ═══════════════════════════════════════════════════════════════════════════
#  MODEL  CORE
# ═══════════════════════════════════════════════════════════════════════════

def _effective_phb_titer(a: Assumptions, mode: Mode, feed: Feed,
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

def _reactor_volume(a: Assumptions, mode: Mode, cdw_titer_gL: float,
                    annual_cdw_kg: float) -> float:
    cycle = _cycle_h(a, mode)
    batches = a.hours_per_year / cycle
    cdw_per_batch = annual_cdw_kg / batches
    working_L = cdw_per_batch / (cdw_titer_gL / 1000.0)
    return (working_L / 1000.0) / a.working_volume_fraction

def _aeration_kwh(a: Assumptions, mode: Mode, feed: Feed,
                  vessel_m3: float) -> float:
    coeff = _aeration_coeff(a, feed)
    broth = vessel_m3 * a.working_volume_fraction
    ferm_h = _fermentation_h(a, mode)
    batches = a.hours_per_year / _cycle_h(a, mode)
    return batches * broth * coeff * ferm_h

def _substrate_cost(a: Assumptions, feed: Feed, polymer: PolymerType,
                    ts: TiterScenario, cdw_kg: float,
                    phb_frac: float) -> Tuple[float, Dict[str, float]]:
    y = _pha_yield(a, feed, ts)
    if polymer == PolymerType.PHBV:
        y *= a.phbv_yield_factor
    pha_intra = cdw_kg * phb_frac

    flows: Dict[str, float] = {}
    if feed == Feed.H2_CO2:
        h2 = pha_intra / y
        kwh = h2 * a.electrolysis_kwh_per_kg_h2
        co2 = cdw_kg * a.co2_kg_per_kg_cdw
        cost = kwh * a.electricity_price + co2 * a.co2_price_per_kg
        flows["H2 (kg/y)"] = h2
        flows["CO2 (kg/y)"] = co2
        flows["Electrolysis (kWh/y)"] = kwh
        return cost, flows
    sugar = pha_intra / y
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

def _harvesting_cost(a: Assumptions, cdw_kg: float,
                     cdw_titer_gL: float) -> float:
    broth_m3 = cdw_kg / (cdw_titer_gL / 1000.0) / 1000.0
    return broth_m3 * a.centrifuge_kwh_per_m3 * a.electricity_price

def _extraction_cost(a: Assumptions, pha_product_kg: float) -> Tuple[str, float]:
    best_name, best_cost = "", float("inf")
    for name, chem, kwh, fixed, fiber_ok in a.extraction_options:
        if a.fiber_grade_required and not fiber_ok:
            continue
        cost = (chem + kwh * a.electricity_price + fixed) * pha_product_kg
        if cost < best_cost:
            best_cost, best_name = cost, name
    return best_name, best_cost

def _pha_drying_cost(a: Assumptions, pha_product_kg: float) -> float:
    wet = pha_product_kg / (1.0 - a.wet_pha_moisture)
    dry = pha_product_kg / (1.0 - a.pha_product_moisture)
    water = max(0.0, wet - dry)
    return water * a.pha_drying_kwh_per_kg_water * a.electricity_price

def _scp_drying_cost(a: Assumptions, scp_product_kg: float) -> float:
    wet = scp_product_kg / (1.0 - a.scp_cake_moisture)
    dry = scp_product_kg / (1.0 - a.scp_product_moisture)
    water = max(0.0, wet - dry)
    return water * a.scp_drying_kwh_per_kg_water * a.electricity_price

def _propionate_cost(a: Assumptions, polymer: PolymerType,
                     pha_product_kg: float) -> float:
    if polymer == PolymerType.PHB:
        return 0.0
    return pha_product_kg * a.propionate_kg_per_kg_phbv * a.propionate_price_per_kg

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

def run_scenario(cap_cdw: float, feed: Feed, mode: Mode,
                 polymer: PolymerType, ts: TiterScenario,
                 a: Optional[Assumptions] = None) -> ScenarioResult:
    a = a or Assumptions()
    cdw_kg = cap_cdw * 1_000.0

    frac = _phb_frac(a, feed, ts)
    pha_intra = cdw_kg * frac
    pha_product = pha_intra * a.extraction_recovery
    residual = cdw_kg - pha_product
    scp_product = residual * a.scp_recovery
    total_product = pha_product + scp_product

    phb_titer = _effective_phb_titer(a, mode, feed, ts)
    cdw_titer = phb_titer / frac
    vol = _reactor_volume(a, mode, cdw_titer, cdw_kg)

    sub, flows = _substrate_cost(a, feed, polymer, ts, cdw_kg, frac)
    pt = _pretreatment_cost(a, feed, cdw_kg)
    n_cost, n_kg = _nitrogen_cost(a, feed, cdw_kg)
    ae = _aeration_kwh(a, mode, feed, vol) * a.electricity_price
    harv = _harvesting_cost(a, cdw_kg, cdw_titer)
    ext_name, ext_cost = _extraction_cost(a, pha_product)
    pha_dry = _pha_drying_cost(a, pha_product)
    prop = _propionate_cost(a, polymer, pha_product)
    scp_proc = scp_product * a.scp_wash_cost_per_kg
    scp_dry = _scp_drying_cost(a, scp_product)
    cx, cx_in, cx_out = _minor_capex(a, cap_cdw)

    labor = _labor_cost(a, cap_cdw)
    total = (sub + pt + n_cost + ae + harv + ext_cost + pha_dry
             + prop + scp_proc + scp_dry + cx + labor)

    standalone_cost = total - scp_proc - scp_dry

    scp_rev = scp_product * a.scp_market_price
    pha_rev = pha_product * a.phb_market_price
    pha_msp_credit = (total - scp_rev) / max(1.0, pha_product)
    pha_msp_standalone = standalone_cost / max(1.0, pha_product)
    scp_msp_credit = (total - pha_rev) / max(1.0, scp_product)
    blended = total / max(1.0, total_product)
    advantage = pha_msp_standalone - pha_msp_credit

    total_rev = pha_rev + scp_rev
    margin = total_rev - total

    cycle = _cycle_h(a, mode)
    batches = a.hours_per_year / cycle

    flows["(NH4)2SO4 (kg/y)"] = n_kg
    flows["Aeration (kWh/y)"] = ae / max(1e-15, a.electricity_price)
    flows["PHA product (kg/y)"] = pha_product
    flows["SCP product (kg/y)"] = scp_product

    return ScenarioResult(
        feed=feed, mode=mode, polymer=polymer, titer_scenario=ts,
        capacity_tpy_cdw=cap_cdw, extraction_method=ext_name,
        annual_cdw_kg=cdw_kg, annual_pha_product_kg=pha_product,
        annual_scp_product_kg=scp_product,
        annual_total_product_kg=total_product,
        reactor_volume_m3=vol, effective_phb_titer_gL=phb_titer,
        phb_content_frac=frac,
        substrate_cost=sub, pretreatment_cost=pt, nitrogen_cost=n_cost,
        aeration_cost=ae, harvesting_cost=harv, extraction_cost=ext_cost,
        pha_drying_cost=pha_dry, propionate_cost=prop,
        scp_processing_cost=scp_proc, scp_drying_cost=scp_dry,
        minor_capex_annual=cx, labor_cost=labor, total_annual_cost=total,
        pha_msp_with_scp_credit=pha_msp_credit,
        pha_msp_standalone=pha_msp_standalone,
        scp_msp_with_pha_credit=scp_msp_credit,
        blended_msp=blended, biorefinery_advantage=advantage,
        pha_revenue_at_market=pha_rev, scp_revenue_at_market=scp_rev,
        total_revenue_at_market=total_rev, gross_margin=margin,
        batches_per_year=batches, cdw_per_batch_kg=cdw_kg / batches,
        pha_per_batch_kg=pha_product / batches,
        scp_per_batch_kg=scp_product / batches,
        cost_per_batch=total / batches, revenue_per_batch=total_rev / batches,
        mass_flows=flows, capex_included=cx_in, capex_excluded=cx_out,
    )


def run_all_scenarios(
    capacities: Optional[List[float]] = None,
    assumptions: Optional[Assumptions] = None,
    verbose: bool = True,
) -> List[ScenarioResult]:
    caps = capacities or DEFAULT_CAPACITIES
    n_per_cap = (len(TiterScenario) * len(PolymerType)
                 * len(Mode) * len(FEED_ORDER))
    total = len(caps) * n_per_cap
    if verbose:
        _log(f"[bio] Running {total} scenarios ...")
    t0 = time.perf_counter()
    results: List[ScenarioResult] = []
    for i, c in enumerate(caps):
        for ts in TiterScenario:
            for poly in PolymerType:
                for m in Mode:
                    for f in FEED_ORDER:
                        results.append(
                            run_scenario(c, f, m, poly, ts, assumptions))
        if verbose:
            done = (i + 1) * n_per_cap
            _log(f"  [{done}/{total}]  {c:>7,.0f} t/y CDW complete")
    if verbose:
        _log(f"[bio] {len(results)} results in "
             f"{time.perf_counter() - t0:.2f} s")
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

COST_COMPONENTS = [
    "Substrate", "Pretreatment", "$(NH_4)_2SO_4$", "Aeration",
    "Harvesting", "PHA extraction", "PHA drying", "Propionate",
    "SCP processing", "SCP drying", "Minor CapEx", "Labor",
]

COMPONENT_COLORS = {
    "Substrate":       "#4E79A7", "Pretreatment":    "#76B7B2",
    "$(NH_4)_2SO_4$": "#F28E2B", "Aeration":         "#59A14F",
    "Harvesting":      "#EDC948", "PHA extraction":  "#E15759",
    "PHA drying":      "#B07AA1", "Propionate":      "#FF9DA7",
    "SCP processing":  "#9C755F", "SCP drying":      "#BAB0AC",
    "Minor CapEx":     "#8CD17D",
    "Labor":           "#D35400",
}


def cost_breakdown(r: ScenarioResult) -> Dict[str, float]:
    return {
        "Substrate":       r.substrate_cost,
        "Pretreatment":    r.pretreatment_cost,
        "$(NH_4)_2SO_4$": r.nitrogen_cost,
        "Aeration":        r.aeration_cost,
        "Harvesting":      r.harvesting_cost,
        "PHA extraction":  r.extraction_cost,
        "PHA drying":      r.pha_drying_cost,
        "Propionate":      r.propionate_cost,
        "SCP processing":  r.scp_processing_cost,
        "SCP drying":      r.scp_drying_cost,
        "Minor CapEx":     r.minor_capex_annual,
        "Labor":           r.labor_cost,
    }


def _filt(results: List[ScenarioResult], **kw) -> List[ScenarioResult]:
    out = results
    for k, v in kw.items():
        out = [r for r in out if getattr(r, k) == v]
    return out


def _get(results: List[ScenarioResult], cap: float, feed: Feed, mode: Mode,
         polymer: PolymerType = PolymerType.PHB,
         ts: TiterScenario = TiterScenario.OPTIMIZED) -> ScenarioResult:
    for r in results:
        if (r.capacity_tpy_cdw == cap and r.feed == feed and r.mode == mode
                and r.polymer == polymer and r.titer_scenario == ts):
            return r
    raise KeyError(f"No result for {cap}/{feed}/{mode}/{polymer}/{ts}")


def best_by_capacity(
    results: List[ScenarioResult],
    polymer: PolymerType = PolymerType.PHB,
    ts: TiterScenario = TiterScenario.OPTIMIZED,
) -> Dict[float, ScenarioResult]:
    filt = _filt(results, polymer=polymer, titer_scenario=ts)
    out: Dict[float, ScenarioResult] = {}
    for r in filt:
        if (r.capacity_tpy_cdw not in out
                or r.pha_msp_with_scp_credit
                < out[r.capacity_tpy_cdw].pha_msp_with_scp_credit):
            out[r.capacity_tpy_cdw] = r
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  TEXT  REPORT
# ═══════════════════════════════════════════════════════════════════════════

def format_report(results: List[ScenarioResult]) -> str:
    lines: List[str] = []
    phb_opt = _filt(results, polymer=PolymerType.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    phb_opt.sort(key=lambda r: (r.capacity_tpy_cdw, r.mode.value,
                                r.feed.value))

    hdr = (f"{'CDW t/y':>9}  {'Mode':>10}  {'Feed':>10}  "
           f"{'PHA t/y':>8}  {'SCP t/y':>8}  "
           f"{'PHA MSP':>8}  {'w/ SCP':>8}  {'Advtg':>7}")
    sep = "─" * len(hdr)
    lines.extend([sep, "PHB + SCP Biorefinery — Optimized Titers", sep,
                  hdr, sep])
    for r in phb_opt:
        lines.append(
            f"{r.capacity_tpy_cdw:>9,.0f}  {r.mode.value:>10}  "
            f"{r.feed.value:>10}  "
            f"{r.annual_pha_product_kg / 1000:>8,.0f}  "
            f"{r.annual_scp_product_kg / 1000:>8,.0f}  "
            f"${r.pha_msp_standalone:>6.2f}  "
            f"${r.pha_msp_with_scp_credit:>6.2f}  "
            f"−${r.biorefinery_advantage:>5.2f}")
    lines.append(sep)

    lines.append("")
    lines.append("Lowest PHA MSP (with SCP credit) per capacity:")
    for cap, r in sorted(best_by_capacity(results).items()):
        lines.append(
            f"  {cap:>7,.0f} t/y CDW  →  {r.feed.value} / {r.mode.value}"
            f"  →  ${r.pha_msp_with_scp_credit:.3f}/kg PHA"
            f"  (saves ${r.biorefinery_advantage:.3f} vs standalone)")

    lines.append("")
    lines.append("Revenue per batch at 3,500 t/y CDW (PHB optimized, fed-batch):")
    for feed in FEED_ORDER:
        try:
            r = _get(results, 3500, feed, Mode.FED_BATCH)
            lines.append(
                f"  {feed.value:>10}  "
                f"PHA {r.pha_per_batch_kg:>8,.0f} kg × $1.75 = "
                f"${r.pha_per_batch_kg * 1.75:>10,.0f}  |  "
                f"SCP {r.scp_per_batch_kg:>8,.0f} kg × $2.00 = "
                f"${r.scp_per_batch_kg * 2.00:>8,.0f}  |  "
                f"Cost ${r.cost_per_batch:>9,.0f}  |  "
                f"Margin ${r.revenue_per_batch - r.cost_per_batch:>9,.0f}")
        except KeyError:
            pass

    lines.append("")
    a_rpt = Assumptions()
    pv_factor = sum(1.0 / (1.0 + a_rpt.npv_discount_rate) ** t
                    for t in range(1, a_rpt.npv_years + 1))
    lines.append(f"NPV at market prices ({a_rpt.npv_years}-yr, "
                 f"{int(a_rpt.npv_discount_rate*100)}% discount, "
                 f"PHB @ ${a_rpt.phb_market_price}/kg, "
                 f"SCP @ ${a_rpt.scp_market_price}/kg):")
    for cap_val, r in sorted(best_by_capacity(results).items()):
        npv = (r.total_revenue_at_market - r.total_annual_cost) * pv_factor
        lines.append(
            f"  {cap_val:>7,.0f} t/y CDW: NPV ${npv / 1e6:>8.2f} M  "
            f"(margin ${r.gross_margin / 1e6:.2f} M/yr)")
    lines.append("")
    lines.append("Labor costs included:")
    for cap_val in sorted({r.capacity_tpy_cdw for r in results}):
        labor = _labor_cost(a_rpt, cap_val)
        lines.append(f"  {cap_val:>7,.0f} t/y CDW  →  ${labor / 1e6:.1f} M/year")
    lines.append("")
    lines.append("Strain notes:")
    for feed, note in FEED_NOTES.items():
        lines.append(f"  {feed.value:>10}  {note}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  SENSITIVITY
# ═══════════════════════════════════════════════════════════════════════════

_FK = {Feed.H2_CO2: "h2", Feed.FRUCTOSE: "fructose",
       Feed.DLP: "dlp", Feed.MOLASSES: "molasses"}


def _sens_params(feed: Feed, ts: TiterScenario) -> List[Tuple[str, str]]:
    suf = "_con" if ts == TiterScenario.CONSERVATIVE else "_opt"
    fk = _FK[feed]
    params: List[Tuple[str, str]] = [
        ("Extraction recovery", "extraction_recovery"),
        ("SCP market price",    "scp_market_price"),
        ("$(NH_4)_2SO_4$ price",    "nh4so4_price_per_kg"),
        ("Electricity price",   "electricity_price"),
        ("PHB yield",           f"yield_{fk}{suf}"),
        ("PHB titer",           f"titer_{fk}{suf}"),
        ("PHB content",         f"phb_frac_{fk}{suf}"),
        ("SCP recovery",        "scp_recovery"),
    ]
    if feed == Feed.H2_CO2:
        params.append(("Electrolyser eff.", "electrolysis_kwh_per_kg_h2"))
    elif feed == Feed.FRUCTOSE:
        params.append(("Fructose price", "fructose_price_per_kg"))
    elif feed == Feed.DLP:
        params.extend([("DLP price", "dlp_price_per_kg_sugar"),
                       ("Pretreatment", "pretreatment_dlp"),
                       ("N reduction", "n_reduction_dlp")])
    elif feed == Feed.MOLASSES:
        params.extend([("Molasses price", "molasses_price_per_kg_sugar"),
                       ("Pretreatment", "pretreatment_molasses")])
    return params


def run_sensitivity(
    cap: float, feed: Feed, mode: Mode,
    polymer: PolymerType = PolymerType.PHB,
    ts: TiterScenario = TiterScenario.OPTIMIZED,
    base: Optional[Assumptions] = None, delta: float = 0.20,
) -> List[Tuple[str, float, float, float]]:
    base = base or Assumptions()
    msp0 = run_scenario(cap, feed, mode, polymer, ts,
                        base).pha_msp_with_scp_credit
    params = list(_sens_params(feed, ts))
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
        lo = run_scenario(cap, feed, mode, polymer, ts,
                          replace(base, **{fld: v0 * (1 - delta)})
                          ).pha_msp_with_scp_credit
        hi = run_scenario(cap, feed, mode, polymer, ts,
                          replace(base, **{fld: v0 * (1 + delta)})
                          ).pha_msp_with_scp_credit
        rows.append((label, lo, msp0, hi))
    rows.sort(key=lambda t: abs(t[3] - t[1]), reverse=True)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE  STYLE
# ═══════════════════════════════════════════════════════════════════════════

FEED_COLORS: Dict[Feed, str] = {
    Feed.H2_CO2: "#0072B2", Feed.FRUCTOSE: "#E69F00",
    Feed.DLP: "#009E73", Feed.MOLASSES: "#CC79A7",
}

def _apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 11, "axes.titlesize": 14, "axes.titleweight": "600",
        "axes.labelsize": 12, "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8, "axes.grid": True, "axes.axisbelow": True,
        "axes.facecolor": "#FAFAFA", "grid.alpha": 0.30,
        "grid.linewidth": 0.5, "figure.facecolor": "white",
        "legend.frameon": True, "legend.framealpha": 0.95,
        "legend.edgecolor": "#CCCCCC",
    })

_DISC = ("Combined biorefinery MSP proxy · OPEX + minor CapEx (<$100 k) + labor · "
         "excludes steam, major CapEx · "
         "PHB @ $1.75/kg (PLA parity), SCP @ $2.00/kg")

def _stamp(fig: plt.Figure) -> None:
    fig.text(0.5, -0.03, _DISC, ha="center", fontsize=7,
             color="#777777", style="italic")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 0 — PROCESS  FLOW  CHART
# ═══════════════════════════════════════════════════════════════════════════

def fig_process_flow() -> plt.Figure:
    _apply_style()
    fig, ax = plt.subplots(figsize=(18, 8.5))
    ax.set_xlim(-0.5, 18.5)
    ax.set_ylim(0, 8.5)
    ax.set_aspect("equal")
    ax.axis("off")

    C_INPUT   = "#E0E0E0"
    C_PROCESS = "#D4E6F1"
    C_PHA     = "#82E0AA"
    C_SCP     = "#F9E79F"
    C_ARROW   = "#555555"

    def _box(x, y, w, h, txt, color, fs=8.5):
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                             boxstyle="round,pad=0.12", facecolor=color,
                             edgecolor="#333333", linewidth=1.3, zorder=2)
        ax.add_patch(box)
        ax.text(x, y, txt, ha="center", va="center", fontsize=fs,
                fontweight="600", zorder=3, linespacing=1.35)

    def _arrow(x1, y1, x2, y2, curved=False):
        kw: dict = dict(arrowstyle="-|>", color=C_ARROW,
                        linewidth=1.6, mutation_scale=14, zorder=1)
        if curved:
            kw["connectionstyle"] = "arc3,rad=0.25"
        arr = FancyArrowPatch((x1, y1), (x2, y2), **kw)
        ax.add_patch(arr)

    bw, bh = 2.3, 1.35

    top_y = 5.8
    _box(1.5,  top_y, bw, bh, "Feedstock\nPreparation", C_INPUT)
    _box(4.5,  top_y, bw, bh, "Fermentation\n(growth phase,\nthen N-limitation)",
         C_PROCESS, fs=7.8)
    _box(7.7,  top_y, bw, bh, "Cell Harvest\n(centrifuge)", C_PROCESS)
    _box(10.9, top_y, bw, bh, "PHB/PHBV\nExtraction\n(SDS + acetone)",
         C_PROCESS, fs=7.8)
    _box(14.1, top_y, bw, bh, "PHA Drying\n(belt dryer)", C_PROCESS)
    _box(17.0, top_y, bw, bh, "PHB/PHBV\nPowder\n(fiber-grade)", C_PHA)

    bot_y = 2.4
    _box(10.9, bot_y, bw, bh, "SCP Wash\n(remove SDS /\nacetone residuals)",
         C_PROCESS, fs=7.8)
    _box(14.1, bot_y, bw, bh, "SCP Drying\n(belt dryer)", C_PROCESS)
    _box(17.0, bot_y, bw, bh, "SCP Powder\n(animal feed\n~55% protein)",
         C_SCP, fs=7.8)

    for x1, x2 in [(2.65, 3.35), (5.65, 6.55), (8.85, 9.75),
                    (12.05, 12.95), (15.25, 15.85)]:
        _arrow(x1, top_y, x2, top_y)

    _arrow(10.9, top_y - bh / 2 - 0.05, 10.9, bot_y + bh / 2 + 0.05)

    for x1, x2 in [(12.05, 12.95), (15.25, 15.85)]:
        _arrow(x1, bot_y, x2, bot_y)

    ax.text(10.0, (top_y + bot_y) / 2, "Residual\nbiomass",
            ha="center", va="center", fontsize=8, color="#666666",
            style="italic")

    ax.text(9.25, 7.8,
            "Combined Biorefinery — PHB/PHBV + SCP Co-production",
            ha="center", fontsize=15, fontweight="bold")
    ax.text(9.25, 7.25,
            "Two sellable products from one fermentation batch",
            ha="center", fontsize=10, color="#555555")

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_INPUT,
               markersize=12, label="Input"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_PROCESS,
               markersize=12, label="Process step"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_PHA,
               markersize=12, label="PHA product"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_SCP,
               markersize=12, label="SCP product"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
              framealpha=0.9, ncol=4, bbox_to_anchor=(0.15, -0.02))

    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.04)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 1 — PHA MSP WITH SCP CREDIT
# ═══════════════════════════════════════════════════════════════════════════

def fig_msp_overview(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    sub = _filt(results, polymer=PolymerType.PHB,
                titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy_cdw for r in sub})
    n_feeds = len(FEED_ORDER)
    x = np.arange(len(caps))
    w = 0.80 / n_feeds

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), sharey=True)
    for ax, mode in zip(axes, [Mode.BATCH, Mode.FED_BATCH]):
        for i, feed in enumerate(FEED_ORDER):
            vals = [_get(sub, c, feed, mode).pha_msp_with_scp_credit
                    for c in caps]
            offset = (i - (n_feeds - 1) / 2) * w
            bars = ax.bar(x + offset, vals, w, label=feed.value,
                          color=FEED_COLORS[feed], edgecolor="white",
                          linewidth=0.6, zorder=3)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02,
                        f"${v:.2f}", ha="center", va="bottom", fontsize=6.2)
        for label, price in MARKET_BENCHMARKS.items():
            if price < ax.get_ylim()[1] * 2:
                ax.axhline(price, ls="--", lw=0.7, color="#999999", zorder=1)
                ax.text(len(caps) - 0.5, price + 0.01, label,
                        fontsize=6.5, color="#666666", ha="right", va="bottom")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{int(c):,}" for c in caps])
        ax.set_xlabel("CDW capacity (t/y)")
        ax.set_title(mode.value, pad=10)
        ax.legend(title="Feedstock", fontsize=8, loc="upper right")

    axes[0].set_ylabel("PHB MSP with SCP credit (USD / kg)")
    fig.suptitle("PHB Minimum Sales Price — biorefinery (optimized)",
                 fontsize=15, fontweight="bold", y=1.03)
    fig.subplots_adjust(wspace=0.08)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 2 — BIOREFINERY ADVANTAGE
# ═══════════════════════════════════════════════════════════════════════════

def fig_biorefinery_advantage(results: List[ScenarioResult],
                              cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    x = np.arange(len(FEED_ORDER))
    w = 0.30

    for j, (mode, hatch) in enumerate([(Mode.BATCH, None),
                                        (Mode.FED_BATCH, "//")]):
        standalone = []
        combined = []
        for feed in FEED_ORDER:
            r = _get(results, cap, feed, mode)
            standalone.append(r.pha_msp_standalone)
            combined.append(r.pha_msp_with_scp_credit)
        off = (j - 0.5) * w
        ax.bar(x + off, standalone, w * 0.45, label=f"Standalone ({mode.value})",
               color="#CCCCCC", edgecolor="#999999", linewidth=0.6, zorder=3)
        bars = ax.bar(x + off, combined, w * 0.45,
                      label=f"With SCP credit ({mode.value})",
                      color=[FEED_COLORS[f] for f in FEED_ORDER],
                      edgecolor="white", linewidth=0.6, hatch=hatch, zorder=4)
        for bar_idx, (sa, co) in enumerate(zip(standalone, combined)):
            ax.annotate(f"−${sa - co:.2f}",
                        xy=(x[bar_idx] + off, co),
                        xytext=(0, -14), textcoords="offset points",
                        ha="center", fontsize=7.5, fontweight="bold",
                        color="#D35400")

    ax.set_xticks(x)
    ax.set_xticklabels([f.value for f in FEED_ORDER], fontsize=11)
    ax.set_ylabel("PHB MSP (USD / kg)")
    ax.set_title(f"Biorefinery advantage — {int(cap):,} t/y CDW (optimized)",
                 pad=12)
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 3 — REVENUE PER BATCH
# ═══════════════════════════════════════════════════════════════════════════

def fig_revenue_per_batch(results: List[ScenarioResult],
                          cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    sub = _filt(results, capacity_tpy_cdw=cap, polymer=PolymerType.PHB,
                titer_scenario=TiterScenario.OPTIMIZED)
    sub.sort(key=lambda r: (FEED_ORDER.index(r.feed),
                            list(Mode).index(r.mode)))
    labels = [f"{r.feed.value}\n{r.mode.value}" for r in sub]
    pha_rev = np.array([r.pha_per_batch_kg * 1.75 for r in sub])
    scp_rev = np.array([r.scp_per_batch_kg * 2.00 for r in sub])
    costs   = np.array([r.cost_per_batch for r in sub])

    fig, ax = plt.subplots(figsize=(14, 6.5))
    x = np.arange(len(sub))
    ax.bar(x, pha_rev / 1000, 0.55, label="PHA revenue",
           color="#82E0AA", edgecolor="white", linewidth=0.5, zorder=3)
    ax.bar(x, scp_rev / 1000, 0.55, bottom=pha_rev / 1000,
           label="SCP revenue", color="#F9E79F", edgecolor="white",
           linewidth=0.5, zorder=3)
    ax.scatter(x, costs / 1000, color="#E15759", s=80, zorder=5,
               label="Total cost", marker="D", edgecolors="white",
               linewidths=0.8)

    for i in range(len(sub)):
        total = (pha_rev[i] + scp_rev[i]) / 1000
        margin = total - costs[i] / 1000
        ax.text(i, total + 2, f"${total:,.0f}k", ha="center",
                fontsize=7.5, fontweight="600")
        ax.text(i, costs[i] / 1000 - 3,
                f"margin\n{margin / total * 100:.0f}%",
                ha="center", fontsize=7, color="#E15759", fontweight="600")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("USD ($k) per batch")
    ax.set_title(f"Revenue & cost per batch — {int(cap):,} t/y CDW "
                 f"(PHB optimized, market prices)", pad=12)
    ax.legend(fontsize=9, loc="upper right")
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 4 — COST STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

def fig_cost_structure(results: List[ScenarioResult],
                       cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    subset = _filt(results, capacity_tpy_cdw=cap, polymer=PolymerType.PHB,
                   titer_scenario=TiterScenario.OPTIMIZED)
    subset.sort(key=lambda r: (list(Mode).index(r.mode),
                               FEED_ORDER.index(r.feed)))
    labels = [f"{r.feed.value} — {r.mode.value}" for r in subset]
    comps = [c for c in COST_COMPONENTS if c != "Propionate"]
    data = np.array([[cost_breakdown(r)[k] / r.annual_pha_product_kg
                      for k in comps] for r in subset])

    fig, ax = plt.subplots(figsize=(14, 7))
    y = np.arange(len(subset))
    left = np.zeros(len(subset))
    for j, comp in enumerate(comps):
        vals = data[:, j]
        ax.barh(y, vals, left=left, label=comp,
                color=COMPONENT_COLORS[comp], edgecolor="white",
                linewidth=0.5, height=0.55)
        for bi, (v, l) in enumerate(zip(vals, left)):
            if v > 0.02:
                ax.text(l + v / 2, y[bi], f"${v:.2f}", ha="center",
                        va="center", fontsize=6, color="white",
                        fontweight="bold")
        left += vals

    scp_credits = np.array([r.scp_revenue_at_market / r.annual_pha_product_kg
                            for r in subset])
    for i in range(len(subset)):
        ax.text(left[i] + 0.01, i,
                f"${left[i]:.2f}  >>  ${left[i] - scp_credits[i]:.2f} w/ SCP",
                va="center", fontsize=8, fontweight="600")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Cost per kg PHA produced (USD)")
    ax.set_title(f"Cost structure — {int(cap):,} t/y CDW (PHB optimized)",
                 pad=12)
    ax.legend(loc="lower right", fontsize=7, ncol=3)
    ax.set_xlim(0, float(left.max()) * 1.18)
    fig.subplots_adjust(left=0.22, bottom=0.14)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 5 — SENSITIVITY TORNADO
# ═══════════════════════════════════════════════════════════════════════════

def fig_sensitivity(results: List[ScenarioResult],
                    cap: float = 3_500.0,
                    delta: float = 0.20) -> plt.Figure:
    _apply_style()
    phb_opt = _filt(results, capacity_tpy_cdw=cap, polymer=PolymerType.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    best = min(phb_opt, key=lambda r: r.pha_msp_with_scp_credit)
    rows = run_sensitivity(cap, best.feed, best.mode, delta=delta)

    fig, ax = plt.subplots(figsize=(12, 7))
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
    ax.axvline(msp0, color="#333333", lw=1.2, zorder=4)
    ax.text(msp0, len(rows) + 0.3, f"Base ${msp0:.3f}/kg (w/ SCP credit)",
            ha="center", fontsize=9, fontweight="600")
    ax.set_yticks(y_arr)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("PHB MSP with SCP credit (USD / kg)")
    ax.set_title(
        f"Sensitivity (±{int(delta*100)}%) — {best.feed.value} / "
        f"{best.mode.value} at {int(cap):,} t/y CDW", pad=12)
    fig.subplots_adjust(left=0.24, bottom=0.14)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 6 — SCALE CURVE
# ═══════════════════════════════════════════════════════════════════════════

def fig_scale_curve(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    sub = _filt(results, polymer=PolymerType.PHB,
                titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy_cdw for r in sub})

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for feed in FEED_ORDER:
        msps = []
        for c in caps:
            best = min((r for r in sub
                        if r.capacity_tpy_cdw == c and r.feed == feed),
                       key=lambda r: r.pha_msp_with_scp_credit)
            msps.append(best.pha_msp_with_scp_credit)
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
    ax.set_xlabel("CDW capacity (t/y)")
    ax.set_ylabel("PHB MSP with SCP credit (USD / kg)")
    ax.set_title("Biorefinery economies of scale (optimized)", pad=12)
    ax.legend(title="Feedstock", fontsize=9, loc="upper right")
    fig.subplots_adjust(bottom=0.16)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 7 — NPV VS SCALE
# ═══════════════════════════════════════════════════════════════════════════

def fig_npv_vs_scale(results: List[ScenarioResult]) -> plt.Figure:
    """NPV (USD M) vs CDW capacity for each feedstock at three PHA price points."""
    from matplotlib.lines import Line2D

    _apply_style()
    a = Assumptions()
    r_disc = a.npv_discount_rate
    n_yr   = a.npv_years
    pv_factor = sum(1.0 / (1.0 + r_disc) ** t for t in range(1, n_yr + 1))

    phb_opt = _filt(results,
                    polymer=PolymerType.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    caps = sorted({r.capacity_tpy_cdw for r in phb_opt})

    # (label, pha_selling_price, linestyle, alpha)
    ref_prices = [
        ("PHA @ $1.75/kg — PLA parity",   1.75, "-",  1.00),
        ("PHA @ $8.50/kg — wholesale",     8.50, "--", 0.80),
        ("PHA @ $15.00/kg — specialty",   15.00, ":",  0.60),
    ]

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        for price_label, pha_price, ls, al in ref_prices:
            npvs: List[float] = []
            for c in caps:
                subset = [r for r in phb_opt
                          if r.capacity_tpy_cdw == c and r.feed == feed]
                if not subset:
                    npvs.append(float("nan"))
                    continue
                best    = min(subset, key=lambda r: r.pha_msp_with_scp_credit)
                scp_rev = best.annual_scp_product_kg * a.scp_market_price
                npv     = (best.annual_pha_product_kg * pha_price
                           + scp_rev
                           - best.total_annual_cost) * pv_factor / 1e6
                npvs.append(npv)
            ax.plot(caps, npvs,
                    linestyle=ls, linewidth=1.8,
                    marker="o", markersize=5,
                    color=FEED_COLORS[feed], alpha=al, zorder=3)

    ax.axhline(0, color="#333333", lw=1.0, zorder=2)

    # Two-legend layout: colour = feedstock, linestyle = price scenario
    feed_handles = [
        Line2D([0], [0], color=FEED_COLORS[f], linewidth=2.2, label=f.value)
        for f in FEED_ORDER
    ]
    price_handles = [
        Line2D([0], [0], color="#555555",
               linestyle=ls, linewidth=1.8, alpha=al, label=lbl)
        for lbl, _, ls, al in ref_prices
    ]
    leg1 = ax.legend(handles=feed_handles, title="Feedstock",
                     fontsize=8.5, loc="upper left")
    ax.add_artist(leg1)
    ax.legend(handles=price_handles,
              title=f"PHA price  (SCP @ ${a.scp_market_price:.2f}/kg credit)",
              fontsize=8.0, loc="lower right")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda val, _: f"{int(val):,}"))
    ax.set_xticks(caps)
    ax.set_xlabel("CDW capacity (t/y)")
    ax.set_ylabel(
        f"NPV (USD millions, {n_yr}-year, {int(r_disc * 100)}% discount)")
    ax.set_title(
        f"Biorefinery NPV vs Scale — PHB optimised, all feedstocks\n"
        f"({n_yr}-yr, {int(r_disc * 100)}% discount, "
        f"SCP @ ${a.scp_market_price:.2f}/kg credit, $2M/yr labor)",
        pad=12,
    )
    fig.subplots_adjust(bottom=0.16)
    _stamp(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE 8 — NPV ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def fig_npv_analysis(results: List[ScenarioResult],
                     cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    a = Assumptions()
    r_disc = a.npv_discount_rate
    n_yr = a.npv_years
    pv_factor = sum(1.0 / (1.0 + r_disc) ** t for t in range(1, n_yr + 1))

    phb_opt = _filt(results, polymer=PolymerType.PHB,
                    titer_scenario=TiterScenario.OPTIMIZED)
    price_max = max(MARKET_BENCHMARKS.values()) * 1.4
    prices = np.linspace(0, price_max, 300)

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        subset = [r for r in phb_opt
                  if r.capacity_tpy_cdw == cap and r.feed == feed]
        best = min(subset, key=lambda r: r.pha_msp_with_scp_credit)
        scp_rev = best.annual_scp_product_kg * a.scp_market_price
        npvs = [(best.annual_pha_product_kg * p + scp_rev
                 - best.total_annual_cost) * pv_factor / 1e6
                for p in prices]
        ax.plot(prices, npvs, linewidth=2.4, label=feed.value,
                color=FEED_COLORS[feed], zorder=3)
        msp = best.pha_msp_with_scp_credit
        ax.plot(msp, 0, "o", color=FEED_COLORS[feed], markersize=10,
                zorder=5, markeredgecolor="white", markeredgewidth=1.5)
        ax.annotate(f"MSP ${msp:.2f}", (msp, 0),
                    textcoords="offset points", xytext=(8, 10),
                    fontsize=8, fontweight="600", color=FEED_COLORS[feed])

    ax.axhline(0, color="#333333", lw=1.0, ls="-", zorder=2)

    ax.autoscale_view()
    ylo, yhi = ax.get_ylim()
    y_label = ylo + (yhi - ylo) * 0.92
    for label, price in MARKET_BENCHMARKS.items():
        if price <= price_max:
            ax.axvline(price, ls=":", lw=0.8, color="#aaaaaa", zorder=1)
            ax.text(price + 0.05, y_label, label,
                    fontsize=7, color="#888888", rotation=90, va="top")

    ax.set_xlabel("PHA selling price (USD / kg)")
    ax.set_ylabel(f"NPV (USD millions, {n_yr}-year, {int(r_disc*100)}% discount)")
    ax.set_title(
        f"Biorefinery NPV vs PHA Selling Price — {int(cap):,} t/y CDW\n"
        f"(SCP @ ${a.scp_market_price:.2f}/kg credit, includes labor)",
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
        "00_process_flow",
        "01_pha_msp_with_scp_credit",
        "02_biorefinery_advantage",
        "03_revenue_per_batch",
        "04_cost_structure",
        "05_sensitivity",
        "06_scale_curve",
        "07_npv_vs_scale",
        "08_npv_analysis",
    ]
    builders = [
        fig_process_flow,
        lambda: fig_msp_overview(results),
        lambda: fig_biorefinery_advantage(results),
        lambda: fig_revenue_per_batch(results),
        lambda: fig_cost_structure(results),
        lambda: fig_sensitivity(results),
        lambda: fig_scale_curve(results),
        lambda: fig_npv_vs_scale(results),
        lambda: fig_npv_analysis(results),
    ]
    figs: Dict[str, plt.Figure] = {}
    t_all = time.perf_counter()
    if verbose:
        _log("[bio] Building figures ...")
    for name, builder in zip(specs, builders):
        if verbose:
            _log(f"  [fig] {name} ...")
        t0 = time.perf_counter()
        figs[name] = builder()
        if verbose:
            _log(f"  [fig] {name} done ({time.perf_counter() - t0:.1f} s)")
    if verbose:
        _log(f"[bio] Figures complete — "
             f"{time.perf_counter() - t_all:.1f} s total")
    if save_dir is not None:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        if verbose:
            _log(f"[bio] Saving PNGs to {out.resolve()} ...")
        for name, fig in figs.items():
            p = out / f"{name}.png"
            fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
            if verbose:
                _log(f"  [save] {p.name}")
        if verbose:
            _log("[bio] Save complete.")
    if show:
        plt.show()
    return figs


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY  POINT
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    _log("[bio] Combined biorefinery TEA — PHA + SCP ($2M labor, 8% NPV, 80 g/L CDW basis)")
    _log("=" * 60)
    results = run_all_scenarios()
    print()
    print(format_report(results))
    print()
    print("Major CapEx EXCLUDED (>$100 k/unit):")
    for item in MAJOR_CAPEX_EXCLUDED:
        print(f"  • {item}")
    print()
    _log("[bio] Generating figures ...")
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        script_dir = Path(".")
    create_all_figures(results, save_dir=script_dir / "biorefinery_80gL_figures")
    _log("[bio] Done.")


# ── Jupyter quick-start ────────────────────────────────────────────────────
#
# Paste this file into one cell and run.  Then in the next cell:
#
#     results = run_all_scenarios()
#     figs    = create_all_figures(results)
#
# Key results for investors:
#     for r in sorted(results, key=lambda r: r.pha_msp_with_scp_credit):
#         if (r.polymer.value == "PHB"
#             and r.titer_scenario.value == "Optimized"
#             and r.mode.value == "Fed-batch"):
#             print(f"{r.feed.value:>10} {r.capacity_tpy_cdw:>7,.0f} t/y CDW"
#                   f"  PHB ${r.pha_msp_with_scp_credit:.2f}/kg"
#                   f"  (saves ${r.biorefinery_advantage:.2f})"
#                   f"  margin {r.gross_margin / r.total_revenue_at_market * 100:.0f}%")

if __name__ == "__main__":
    main()
