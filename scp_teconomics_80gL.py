#!/usr/bin/env python3
"""
Technoeconomic Model — Single-Cell Protein via Cupriavidus necator
==================================================================

Feedstock cases (sourced from PhycoVax TEA Framework, March 2026):
  1. Autotrophic — H₂ / CO₂  (H₂ via renewable electrolysis)
  2. Fructose (HFCS-90) — native H16 metabolism, $0.375/kg, TRL 6–7
  3. DLP (delactosed permeate) — $0.13/kg sugar, requires DSM545 strain,
     built-in N/P reduces supplementation, CA supply (Hilmar), TRL 4–5
  4. Blackstrap molasses (cane) — $0.155/kg sugar, partial H16 use,
     simple pretreatment, TRL 5–6

Capacities : 50  /  350  /  3,500  /  7,000  t/y sellable dry SCP
Modes      : Batch  and  Continuous fermentation

Output     : Minimum Sales Price (MSP) in USD / kg dry SCP
             (OPEX + annualised minor CapEx < $100 k / unit + labor)
             Net Present Value (NPV) at 8% discount over 10 years

Data sources:
  - PhycoVax Inc. TEA Question Framework (March 2026, CONFIDENTIAL)
  - Wang et al. 2022, Processes 10:17 (DLP pricing, enzyme reuse TEA)
  - PubMed 40669633 (2025) — whey permeate / DSM545 yields
  - Dalsasso et al. / ResearchGate 2019 — molasses 11.7 g/L PHB
  - IMARC Group — molasses USA $290–295/MT Q2-Q3 2025
  - Ishizaki et al. 2001; Matassa 2016 — H₂/CO₂ autotrophic yields

Usage
-----
Jupyter — paste entire file into **one** cell, run.  Next cell:

    results = run_all_scenarios()
    figs    = create_all_figures(results)

Terminal:
    python3 scp_teconomics_80gL.py

Dependencies: numpy, matplotlib
    pip install numpy matplotlib
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
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
#  ASSUMPTIONS  —  edit values here to change model inputs
# ═══════════════════════════════════════════════════════════════════════════
#
#  Yield notes (biomass, NOT PHB — this is an SCP model):
#    PHB yields from the PhycoVax document are converted to approximate
#    biomass yields by dividing by the typical PHB content fraction (~0.60):
#      Y_DCW ≈ Y_PHB / PHB_fraction_of_CDW
#
#  Y_X/H₂  — 3.0 kg DCW / kg H₂ (Ishizaki 2001; Matassa 2016)
#  Y_X/fructose — PHB 0.25–0.35 g/g at ~60% CDW → DCW ~0.50 g/g
#  Y_X/DLP — PHB 0.30–0.38 g/g at ~60% CDW → DCW ~0.55 g/g
#                 (PubMed 40669633: "comparable or higher than pure sugars")
#  Y_X/molasses — PHB 0.15–0.25 g/g at ~56% CDW → DCW ~0.33 g/g
#                 (inhibitors reduce effective yield; Dalsasso et al.)
#
#  Electrolysis — PEM: 50–55 kWh / kg H₂.  Default 52.
#  (NH₄)₂SO₄  — US bulk ~$420/MT (IMARC 2025).
#  DLP pricing — $0.13/kg sugar (Wang et al. 2022, Processes 10:17).
#  Molasses — $290–295/MT whole (IMARC Q2-Q3 2025); 50% sugars
#             → ~$0.155/kg available sugar midpoint.
#  Fructose (HFCS-90) — $0.30–0.45/kg (PhycoVax table) → $0.375 midpoint.

@dataclass
class Assumptions:
    """All tuneable model parameters.  Modify and re-run."""

    # ── Product specification ──────────────────────────────────────────────
    recovery_fraction: float = 0.95
    product_moisture_fraction: float = 0.08

    # ── Fermentation ───────────────────────────────────────────────────────
    titer_g_per_L: float = 80.0
    protein_fraction_of_dcw: float = 0.50

    # ── Batch ──────────────────────────────────────────────────────────────
    batch_time_h: float = 72.0
    turnaround_h: float = 48.0
    working_volume_fraction: float = 0.90

    # ── Continuous ─────────────────────────────────────────────────────────
    residence_time_h: float = 24.0

    # ── Biomass yields (kg DCW / kg substrate consumed) ────────────────────
    yield_h2: float = 3.0
    yield_fructose: float = 0.50
    yield_dlp: float = 0.55
    yield_molasses: float = 0.33

    # ── CO₂ (autotrophic case) ─────────────────────────────────────────────
    co2_kg_per_kg_dcw: float = 1.83
    co2_price_per_kg: float = 0.00

    # ── Hydrogen / electrolysis ────────────────────────────────────────────
    electricity_price: float = 0.03
    electrolysis_kwh_per_kg_h2: float = 52.0

    # ── Sugar feedstock prices ($/kg available fermentable sugar) ──────────
    fructose_price_per_kg: float = 0.375
    dlp_price_per_kg_sugar: float = 0.13
    molasses_price_per_kg_sugar: float = 0.155

    # ── Pretreatment cost ($/kg DCW produced) ──────────────────────────────
    #    Fructose (HFCS-90): none needed — native H16 metabolism.
    #    DLP: lactase hydrolysis — $0.07/kg product with enzyme reuse via UF
    #         (Wang et al. 2022: $0.53/kg without reuse, 86% reduction with UF).
    #    Molasses: dilution + pH adjustment — cheap, ~$0.02/kg DCW.
    pretreatment_fructose: float = 0.00
    pretreatment_dlp: float = 0.07
    pretreatment_molasses: float = 0.02

    # ── Nitrogen — (NH₄)₂SO₄ ──────────────────────────────────────────────
    n_fraction_of_dcw: float = 0.08
    nh4so4_n_fraction: float = 0.212
    nh4so4_price_per_kg: float = 0.42

    # ── Nitrogen supplement reduction (fraction) per feed ──────────────────
    #    DLP has C/N ~21.6 (near-ideal); rich in N, P, minerals (UC Davis).
    #    Molasses has moderate built-in N.  Pure fructose has zero N (C/N = ∞).
    n_supplement_reduction_fructose: float = 0.00
    n_supplement_reduction_dlp: float = 1.00
    n_supplement_reduction_molasses: float = 0.20

    # ── Aeration / agitation (kWh per m³ broth per hour) ───────────────────
    aeration_kwh_m3_h_gas: float = 0.55
    aeration_kwh_m3_h_fructose: float = 0.85
    aeration_kwh_m3_h_dlp: float = 0.85
    aeration_kwh_m3_h_molasses: float = 0.95

    # ── Downstream processing options ──────────────────────────────────────
    downstream_options: Tuple[Tuple[str, float, float], ...] = (
        ("Centrifuge + belt dryer",  1.15, 0.08),
        ("Disc-stack + spray dryer", 1.45, 0.12),
        ("Ceramic MF + air dryer",   1.60, 0.10),
    )
    cake_moisture_fraction: float = 0.78

    # ── Minor CapEx (per-unit cost ≤ threshold → include, annualise) ───────
    capex_threshold: float = 100_000.0
    minor_equipment: Tuple[Tuple[str, float, float, float, float], ...] = (
        ("Feed & media pumps (×3)",    3_500,  50, 0.60, 10),
        ("pH control system",          8_000,  50, 0.40,  8),
        ("DO & gas analysers",         5_000,  50, 0.30,  8),
        ("Media prep tank (SS)",      12_000,  50, 0.60, 15),
        ("Piping, valves, fittings",  15_000,  50, 0.60, 20),
        ("Process control (PLC/HMI)", 20_000,  50, 0.30, 10),
        ("CIP skid (small)",          25_000,  50, 0.60, 12),
        ("Water purification (RO)",   15_000,  50, 0.60, 12),
    )

    # ── Labor (annual cost by production scale) ─────────────────────────
    labor_small_scale: float = 2_000_000.0    # <1,000 t/y
    labor_medium_scale: float = 2_000_000.0   # 3,500 t/y (capped at $2 M)
    labor_large_scale: float = 2_000_000.0    # 7,000 t/y (capped at $2 M)

    # ── NPV parameters ──────────────────────────────────────────────────────
    npv_discount_rate: float = 0.08
    npv_years: int = 10

    # ── Schedule ───────────────────────────────────────────────────────────
    hours_per_year: float = 8_760.0


DEFAULT_CAPACITIES: List[float] = [50.0, 350.0, 3_500.0, 7_000.0]

MAJOR_CAPEX_EXCLUDED: Tuple[str, ...] = (
    "Production bioreactor(s)",
    "Industrial centrifuge / decanter",
    "Spray dryer or belt / drum dryer",
    "MF/UF membrane skid",
    "Electrolyser stack + rectifiers",
    "CO₂ compression / liquefaction",
    "Cold storage / warehouse",
    "Wastewater treatment system",
    "Lactase UF recycle skid (DLP only, ~$1 M at scale)",
)

PROTEIN_BENCHMARKS: Dict[str, float] = {
    "Soy protein concentrate":  1.00,
    "Fishmeal":                 1.75,
    "Whey protein concentrate": 4.00,
    "Spirulina (bulk)":         8.00,
}


# ═══════════════════════════════════════════════════════════════════════════
#  ENUMS  &  RESULT DATA CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Mode(str, Enum):
    BATCH = "Batch"
    CONTINUOUS = "Continuous"


class Feed(str, Enum):
    H2_CO2 = "$H_2/CO_2$"
    FRUCTOSE = "Fructose"
    DLP = "DLP"
    MOLASSES = "Molasses"


FEED_ORDER = [Feed.H2_CO2, Feed.FRUCTOSE, Feed.DLP, Feed.MOLASSES]

FEED_NOTES: Dict[Feed, str] = {
    Feed.H2_CO2:  "Autotrophic baseline — H16 wild-type",
    Feed.FRUCTOSE: "HFCS-90 — H16 native metabolism, no pretreatment, TRL 6–7",
    Feed.DLP:      "Delactosed permeate — requires DSM545 strain + lactase, TRL 4–5",
    Feed.MOLASSES: "Blackstrap cane molasses — partial H16 use (fructose fraction), TRL 5–6",
}


@dataclass
class ScenarioResult:
    feed: Feed
    mode: Mode
    capacity_tpy: float
    downstream: str

    annual_product_kg: float
    annual_dcw_kg: float
    reactor_volume_m3: float

    substrate_cost: float
    pretreatment_cost: float
    nitrogen_cost: float
    aeration_cost: float
    downstream_cost: float
    minor_capex_annual: float
    labor_cost: float

    total_annual_cost: float
    msp: float

    mass_flows: Dict[str, float]
    capex_included: List[Tuple[str, float, float]]
    capex_excluded: List[Tuple[str, float]]


# ═══════════════════════════════════════════════════════════════════════════
#  MODEL  CORE
# ═══════════════════════════════════════════════════════════════════════════

def _reactor_volume(a: Assumptions, mode: Mode, annual_dcw_kg: float) -> float:
    titer = a.titer_g_per_L
    if mode == Mode.BATCH:
        cycle = a.batch_time_h + a.turnaround_h
        batches = a.hours_per_year / cycle
        working = (annual_dcw_kg / batches) / titer
        return working / a.working_volume_fraction
    working = annual_dcw_kg * a.residence_time_h / (titer * a.hours_per_year)
    return working / a.working_volume_fraction


def _aeration_coeff(a: Assumptions, feed: Feed) -> float:
    return {
        Feed.H2_CO2:  a.aeration_kwh_m3_h_gas,
        Feed.FRUCTOSE: a.aeration_kwh_m3_h_fructose,
        Feed.DLP:      a.aeration_kwh_m3_h_dlp,
        Feed.MOLASSES: a.aeration_kwh_m3_h_molasses,
    }[feed]


def _aeration_kwh(a: Assumptions, mode: Mode, feed: Feed,
                  vessel_m3: float) -> float:
    coeff = _aeration_coeff(a, feed)
    broth = vessel_m3 * a.working_volume_fraction
    if mode == Mode.BATCH:
        cycle = a.batch_time_h + a.turnaround_h
        batches = a.hours_per_year / cycle
        return batches * broth * coeff * a.batch_time_h
    return broth * coeff * a.hours_per_year


def _substrate_cost(a: Assumptions, feed: Feed,
                    dcw_kg: float) -> Tuple[float, Dict[str, float]]:
    flows: Dict[str, float] = {}
    if feed == Feed.H2_CO2:
        h2 = dcw_kg / a.yield_h2
        kwh = h2 * a.electrolysis_kwh_per_kg_h2
        co2 = dcw_kg * a.co2_kg_per_kg_dcw
        cost = kwh * a.electricity_price + co2 * a.co2_price_per_kg
        flows["H2 (kg/y)"] = h2
        flows["CO2 (kg/y)"] = co2
        flows["Electrolysis (kWh/y)"] = kwh
        return cost, flows
    if feed == Feed.FRUCTOSE:
        sugar = dcw_kg / a.yield_fructose
        flows["Fructose (kg/y)"] = sugar
        return sugar * a.fructose_price_per_kg, flows
    if feed == Feed.DLP:
        sugar = dcw_kg / a.yield_dlp
        flows["DLP sugar (kg/y)"] = sugar
        return sugar * a.dlp_price_per_kg_sugar, flows
    sugar = dcw_kg / a.yield_molasses
    flows["Molasses sugar (kg/y)"] = sugar
    return sugar * a.molasses_price_per_kg_sugar, flows


def _pretreatment_cost(a: Assumptions, feed: Feed, dcw_kg: float) -> float:
    pt = {
        Feed.H2_CO2:  0.0,
        Feed.FRUCTOSE: a.pretreatment_fructose,
        Feed.DLP:      a.pretreatment_dlp,
        Feed.MOLASSES: a.pretreatment_molasses,
    }[feed]
    return pt * dcw_kg


def _n_reduction(a: Assumptions, feed: Feed) -> float:
    return {
        Feed.H2_CO2:  0.0,
        Feed.FRUCTOSE: a.n_supplement_reduction_fructose,
        Feed.DLP:      a.n_supplement_reduction_dlp,
        Feed.MOLASSES: a.n_supplement_reduction_molasses,
    }[feed]


def _nitrogen_cost(a: Assumptions, feed: Feed, dcw_kg: float) -> Tuple[float, float]:
    reduction = _n_reduction(a, feed)
    nh4 = a.n_fraction_of_dcw * dcw_kg / a.nh4so4_n_fraction * (1.0 - reduction)
    return nh4 * a.nh4so4_price_per_kg, nh4


def _downstream_cost(a: Assumptions, dcw_kg: float) -> Tuple[str, float, Dict[str, float]]:
    product = dcw_kg * a.recovery_fraction
    w_cake = product * a.cake_moisture_fraction / max(1e-9, 1.0 - a.cake_moisture_fraction)
    w_final = product * a.product_moisture_fraction / max(1e-9, 1.0 - a.product_moisture_fraction)
    water = max(0.0, w_cake - w_final)

    best_name, best_cost = "", float("inf")
    options: Dict[str, float] = {}
    for name, kwh_w, fix_kg in a.downstream_options:
        c = water * kwh_w * a.electricity_price + product * fix_kg
        options[name] = c
        if c < best_cost:
            best_cost, best_name = c, name
    return best_name, best_cost, options


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

def run_scenario(cap: float, feed: Feed, mode: Mode,
                 a: Optional[Assumptions] = None) -> ScenarioResult:
    a = a or Assumptions()
    product_kg = cap * 1_000.0
    dcw_kg = product_kg / a.recovery_fraction

    vol = _reactor_volume(a, mode, dcw_kg)
    sub, flows = _substrate_cost(a, feed, dcw_kg)
    pt = _pretreatment_cost(a, feed, dcw_kg)
    n_cost, n_kg = _nitrogen_cost(a, feed, dcw_kg)
    ae = _aeration_kwh(a, mode, feed, vol) * a.electricity_price
    ds_name, ds_cost, _ = _downstream_cost(a, dcw_kg)
    cx, cx_in, cx_out = _minor_capex(a, cap)

    labor = _labor_cost(a, cap)
    total = sub + pt + n_cost + ae + ds_cost + cx + labor
    flows["(NH4)2SO4 (kg/y)"] = n_kg
    flows["Aeration (kWh/y)"] = ae / max(1e-15, a.electricity_price)

    return ScenarioResult(
        feed=feed, mode=mode, capacity_tpy=cap, downstream=ds_name,
        annual_product_kg=product_kg, annual_dcw_kg=dcw_kg,
        reactor_volume_m3=vol,
        substrate_cost=sub, pretreatment_cost=pt, nitrogen_cost=n_cost,
        aeration_cost=ae, downstream_cost=ds_cost, minor_capex_annual=cx,
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
    total = len(caps) * len(Mode) * len(FEED_ORDER)
    if verbose:
        _log(f"[scp] Running {total} scenarios "
             f"({len(caps)} capacities × {len(Mode)} modes × {len(FEED_ORDER)} feeds) ...")
    t0 = time.perf_counter()
    results: List[ScenarioResult] = []
    for i, c in enumerate(caps):
        for m in Mode:
            for f in FEED_ORDER:
                results.append(run_scenario(c, f, m, assumptions))
        if verbose:
            done = (i + 1) * len(Mode) * len(FEED_ORDER)
            _log(f"  [{done}/{total}]  {c:>7,.0f} t/y complete")
    if verbose:
        _log(f"[scp] {len(results)} results in {time.perf_counter() - t0:.2f} s")
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS  —  cost decomposition  &  scenario lookup
# ═══════════════════════════════════════════════════════════════════════════

COST_COMPONENTS = [
    "Substrate / electrolysis",
    "Pretreatment",
    "$(NH_4)_2SO_4$",
    "Aeration",
    "Downstream",
    "Minor CapEx",
    "Labor",
]

COMPONENT_COLORS = {
    "Substrate / electrolysis": "#4E79A7",
    "Pretreatment":             "#76B7B2",
    "$(NH_4)_2SO_4$":          "#F28E2B",
    "Aeration":                "#59A14F",
    "Downstream":              "#B07AA1",
    "Minor CapEx":             "#E15759",
    "Labor":                   "#D35400",
}


def cost_per_kg(r: ScenarioResult) -> Dict[str, float]:
    d = r.annual_product_kg
    return {
        "Substrate / electrolysis": r.substrate_cost / d,
        "Pretreatment":             r.pretreatment_cost / d,
        "$(NH_4)_2SO_4$":          r.nitrogen_cost / d,
        "Aeration":                r.aeration_cost / d,
        "Downstream":              r.downstream_cost / d,
        "Minor CapEx":             r.minor_capex_annual / d,
        "Labor":                   r.labor_cost / d,
    }


def _get(results: List[ScenarioResult],
         cap: float, feed: Feed, mode: Mode) -> ScenarioResult:
    for r in results:
        if r.capacity_tpy == cap and r.feed == feed and r.mode == mode:
            return r
    raise KeyError(f"No result for {cap} / {feed} / {mode}")


def best_by_capacity(results: List[ScenarioResult]) -> Dict[float, ScenarioResult]:
    out: Dict[float, ScenarioResult] = {}
    for r in results:
        if r.capacity_tpy not in out or r.msp < out[r.capacity_tpy].msp:
            out[r.capacity_tpy] = r
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  TEXT  REPORT
# ═══════════════════════════════════════════════════════════════════════════

def format_report(results: List[ScenarioResult]) -> str:
    hdr = (f"{'Cap (t/y)':>10}  {'Mode':>12}  {'Feed':>10}  "
           f"{'MSP ($/kg)':>10}  {'V (m³)':>8}  {'Downstream'}")
    sep = "─" * len(hdr)
    lines = [sep, hdr, sep]
    for r in sorted(results, key=lambda x: (x.capacity_tpy, x.mode.value, x.feed.value)):
        lines.append(
            f"{r.capacity_tpy:>10,.0f}  {r.mode.value:>12}  {r.feed.value:>10}  "
            f"${r.msp:>9.3f}  {r.reactor_volume_m3:>8.1f}  {r.downstream}"
        )
    lines.append(sep)
    lines.append("")
    lines.append("Lowest MSP per capacity:")
    for cap, r in sorted(best_by_capacity(results).items()):
        lines.append(
            f"  {cap:>7,.0f} t/y  →  {r.feed.value} / {r.mode.value}"
            f"  →  ${r.msp:.3f}/kg dry SCP"
        )
    lines.append("")
    a = Assumptions()
    pv_factor = sum(1.0 / (1.0 + a.npv_discount_rate) ** t
                    for t in range(1, a.npv_years + 1))
    lines.append(f"NPV at market prices ({a.npv_years}-yr, {int(a.npv_discount_rate*100)}% discount):")
    for cap_val, r in sorted(best_by_capacity(results).items()):
        for bench_label, bench_price in PROTEIN_BENCHMARKS.items():
            rev = r.annual_product_kg * bench_price
            npv = (rev - r.total_annual_cost) * pv_factor
            lines.append(
                f"  {cap_val:>7,.0f} t/y @ {bench_label} (${bench_price:.2f}/kg): "
                f"NPV ${npv / 1e6:>8.2f} M")
        lines.append("")
    lines.append("Labor costs included:")
    for cap_val in sorted({r.capacity_tpy for r in results}):
        labor = _labor_cost(a, cap_val)
        lines.append(f"  {cap_val:>7,.0f} t/y  →  ${labor / 1e6:.1f} M/year "
                     f" (${labor / (cap_val * 1000):.2f}/kg)")
    lines.append("")
    lines.append("Strain compatibility notes:")
    for feed, note in FEED_NOTES.items():
        lines.append(f"  {feed.value:>10}  {note}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  SENSITIVITY  ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

SENSITIVITY_PARAMS_COMMON = [
    ("Recovery fraction",   "recovery_fraction"),
    ("$(NH_4)_2SO_4$ price",    "nh4so4_price_per_kg"),
    ("Electricity price",   "electricity_price"),
    ("Cake moisture",       "cake_moisture_fraction"),
    ("Titer (g/L)",         "titer_g_per_L"),
]

SENSITIVITY_PARAMS_FEED: Dict[Feed, List[Tuple[str, str]]] = {
    Feed.H2_CO2: [
        ("$H_2$ yield",            "yield_h2"),
        ("Electrolyser eff.",     "electrolysis_kwh_per_kg_h2"),
        ("Aeration power (gas)",  "aeration_kwh_m3_h_gas"),
    ],
    Feed.FRUCTOSE: [
        ("Fructose yield",             "yield_fructose"),
        ("Fructose price",             "fructose_price_per_kg"),
        ("Aeration power (fructose)",  "aeration_kwh_m3_h_fructose"),
    ],
    Feed.DLP: [
        ("DLP yield",             "yield_dlp"),
        ("DLP sugar price",       "dlp_price_per_kg_sugar"),
        ("Pretreatment (DLP)",    "pretreatment_dlp"),
        ("N reduction (DLP)",     "n_supplement_reduction_dlp"),
        ("Aeration power (DLP)",  "aeration_kwh_m3_h_dlp"),
    ],
    Feed.MOLASSES: [
        ("Molasses yield",             "yield_molasses"),
        ("Molasses sugar price",       "molasses_price_per_kg_sugar"),
        ("Pretreatment (molasses)",    "pretreatment_molasses"),
        ("Aeration power (molasses)",  "aeration_kwh_m3_h_molasses"),
    ],
}


def run_sensitivity(
    cap: float,
    feed: Feed,
    mode: Mode,
    base: Optional[Assumptions] = None,
    delta: float = 0.20,
) -> List[Tuple[str, float, float, float]]:
    """
    Vary each parameter ± delta (fractional).
    Returns [(display_name, msp_at_-δ, msp_base, msp_at_+δ), …]
    sorted by |swing| descending.
    """
    base = base or Assumptions()
    msp0 = run_scenario(cap, feed, mode, base).msp
    params = list(SENSITIVITY_PARAMS_COMMON) + SENSITIVITY_PARAMS_FEED[feed]
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
        lo = run_scenario(cap, feed, mode, replace(base, **{fld: v0 * (1 - delta)})).msp
        hi = run_scenario(cap, feed, mode, replace(base, **{fld: v0 * (1 + delta)})).msp
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
    "OPEX + minor CapEx (<$100 k/unit) + labor MSP proxy  ·  "
    "excludes steam, major CapEx, electrolyser BOP  ·  "
    "feedstock data: PhycoVax TEA Framework (Mar 2026)"
)


def _stamp(fig: plt.Figure) -> None:
    fig.text(0.5, -0.03, _DISCLAIMER,
             ha="center", fontsize=7.5, color="#777777", style="italic")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURES
# ═══════════════════════════════════════════════════════════════════════════

# ---------- 1. MSP overview (grouped bars, batch | continuous) -----------

def fig_msp_overview(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    caps = sorted({r.capacity_tpy for r in results})
    n_feeds = len(FEED_ORDER)
    x = np.arange(len(caps))
    w = 0.80 / n_feeds

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.0), sharey=True)
    for ax, mode in zip(axes, [Mode.BATCH, Mode.CONTINUOUS]):
        for i, feed in enumerate(FEED_ORDER):
            vals = [_get(results, c, feed, mode).msp for c in caps]
            offset = (i - (n_feeds - 1) / 2) * w
            bars = ax.bar(x + offset, vals, w, label=feed.value,
                          color=FEED_COLORS[feed], edgecolor="white",
                          linewidth=0.6, zorder=3)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.01,
                        f"${v:.2f}", ha="center", va="bottom", fontsize=6.5,
                        rotation=0)

        for label, price in PROTEIN_BENCHMARKS.items():
            if price < ax.get_ylim()[1] * 1.6:
                ax.axhline(price, ls="--", lw=0.7, color="#999999", zorder=1)
                ax.text(len(caps) - 0.5, price + 0.01, label,
                        fontsize=6.5, color="#666666", ha="right", va="bottom")

        ax.set_xticks(x)
        ax.set_xticklabels([f"{int(c):,}" for c in caps])
        ax.set_xlabel("Capacity (t/y dry SCP)")
        ax.set_title(mode.value, pad=10)
        ax.legend(title="Feedstock", fontsize=8, loc="upper right")

    axes[0].set_ylabel("MSP (USD / kg dry SCP)")
    fig.suptitle("Minimum Sales Price — all scenarios",
                 fontsize=15, fontweight="bold", y=1.03)
    fig.subplots_adjust(wspace=0.08)
    _stamp(fig)
    return fig


# ---------- 2. Cost structure (stacked horizontal bars) ------------------

def fig_cost_structure(results: List[ScenarioResult],
                       cap: float = 3_500.0) -> plt.Figure:
    _apply_style()
    subset = [r for r in results if r.capacity_tpy == cap]
    subset.sort(key=lambda r: (list(Mode).index(r.mode),
                               FEED_ORDER.index(r.feed)))
    labels = [f"{r.feed.value} — {r.mode.value}" for r in subset]
    data = np.array([[cost_per_kg(r)[k] for k in COST_COMPONENTS]
                     for r in subset])

    fig, ax = plt.subplots(figsize=(12, 6.8))
    y = np.arange(len(subset))
    left = np.zeros(len(subset))
    for j, comp in enumerate(COST_COMPONENTS):
        vals = data[:, j]
        bars = ax.barh(y, vals, left=left, label=comp,
                       color=COMPONENT_COLORS[comp],
                       edgecolor="white", linewidth=0.5, height=0.55)
        for bar_i, (bar, v) in enumerate(zip(bars, vals)):
            if v > 0.015:
                ax.text(left[bar_i] + v / 2, bar.get_y() + bar.get_height() / 2,
                        f"${v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold")
        left += vals

    for i, total in enumerate(left):
        ax.text(total + 0.01, i, f"${total:.2f}", va="center", fontsize=9,
                fontweight="600")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("MSP contribution (USD / kg dry SCP)")
    ax.set_title(f"Cost structure — {int(cap):,} t/y", pad=12)
    ax.legend(loc="lower right", fontsize=7.5, ncol=3)
    ax.set_xlim(0, float(left.max()) * 1.12)
    fig.subplots_adjust(left=0.28, bottom=0.15)
    _stamp(fig)
    return fig


# ---------- 3. Sensitivity tornado  -------------------------------------

def fig_sensitivity(results: List[ScenarioResult],
                    cap: float = 3_500.0,
                    delta: float = 0.20) -> plt.Figure:
    _apply_style()
    best = min((r for r in results if r.capacity_tpy == cap), key=lambda r: r.msp)
    rows = run_sensitivity(cap, best.feed, best.mode, delta=delta)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    y = np.arange(len(rows))
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

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("MSP (USD / kg dry SCP)")
    ax.set_title(
        f"Sensitivity (±{int(delta*100)}%) — {best.feed.value} / {best.mode.value}"
        f" at {int(cap):,} t/y",
        pad=12,
    )
    fig.subplots_adjust(left=0.28, bottom=0.14)
    _stamp(fig)
    return fig


# ---------- 4. Scale curve (MSP vs capacity, best mode per feed) ---------

def fig_scale_curve(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    caps = sorted({r.capacity_tpy for r in results})

    fig, ax = plt.subplots(figsize=(11, 6.0))
    for feed in FEED_ORDER:
        msps = []
        for c in caps:
            best = min((r for r in results
                        if r.capacity_tpy == c and r.feed == feed),
                       key=lambda r: r.msp)
            msps.append(best.msp)
        ax.plot(caps, msps, marker="o", markersize=8, linewidth=2.4,
                label=feed.value, color=FEED_COLORS[feed], zorder=3)
        for c, v in zip(caps, msps):
            ax.annotate(f"${v:.2f}", (c, v), textcoords="offset points",
                        xytext=(6, 6), fontsize=7.5)

    for label, price in PROTEIN_BENCHMARKS.items():
        ax.axhline(price, ls=":", lw=0.8, color="#aaaaaa", zorder=1)
        ax.text(caps[0] * 0.85, price, f"  {label} (${price:.2f})",
                fontsize=7, color="#888888", va="center")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"))
    ax.set_xticks(caps)
    ax.set_xlabel("Plant capacity (t/y sellable dry SCP)")
    ax.set_ylabel("MSP (USD / kg dry SCP) — best of batch / continuous")
    ax.set_title("Economies of scale", pad=12)
    ax.legend(title="Feedstock", fontsize=9, loc="upper right")
    fig.subplots_adjust(bottom=0.16)
    _stamp(fig)
    return fig


# ---------- 5. Minor CapEx detail by capacity  --------------------------

def fig_capex_detail(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    caps = sorted({r.capacity_tpy for r in results})
    ref = [next(r for r in results
                if r.capacity_tpy == c and r.feed == Feed.H2_CO2
                and r.mode == Mode.BATCH) for c in caps]

    names_all = sorted({n for r in ref for n, _, _ in r.capex_included})
    cmap = plt.cm.get_cmap("tab10")
    name_color = {n: cmap(i) for i, n in enumerate(names_all)}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5),
                                    gridspec_kw={"width_ratios": [3, 2]})
    x = np.arange(len(caps))
    bottom = np.zeros(len(caps))
    legend_patches: List[Patch] = []
    plotted = set()
    for name in names_all:
        vals = []
        for r in ref:
            hit = [a for n, _, a in r.capex_included if n == name]
            vals.append(hit[0] if hit else 0.0)
        arr = np.array(vals)
        ax1.bar(x, arr, bottom=bottom, width=0.55,
                color=name_color[name], edgecolor="white", linewidth=0.5)
        bottom += arr
        if name not in plotted:
            legend_patches.append(Patch(facecolor=name_color[name], label=name))
            plotted.add(name)

    for i, tot in enumerate(bottom):
        ax1.text(i, tot + 20, f"${tot:,.0f}/y", ha="center", fontsize=8.5,
                 fontweight="600")

    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{int(c):,}" for c in caps])
    ax1.set_xlabel("Capacity (t/y)")
    ax1.set_ylabel("Annualised minor CapEx (USD / y)")
    ax1.set_title("Minor CapEx included (<$100 k / unit)", pad=10)
    ax1.legend(handles=legend_patches, fontsize=7.5, loc="upper left", ncol=2)

    per_kg = [r.minor_capex_annual / r.annual_product_kg for r in ref]
    ax2.bar(x, per_kg, width=0.55, color="#E15759", edgecolor="white",
            linewidth=0.5)
    for i, v in enumerate(per_kg):
        ax2.text(i, v + 0.002, f"${v:.3f}", ha="center", fontsize=8.5,
                 fontweight="600")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{int(c):,}" for c in caps])
    ax2.set_xlabel("Capacity (t/y)")
    ax2.set_ylabel("Minor CapEx (USD / kg dry SCP)")
    ax2.set_title("Per-unit impact", pad=10)

    fig.suptitle("Minor CapEx — scale dependence",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.subplots_adjust(wspace=0.30)
    _stamp(fig)
    return fig


# ---------- 6. NPV vs scale  -------------------------------------------

def fig_npv_vs_scale(results: List[ScenarioResult]) -> plt.Figure:
    _apply_style()
    a = Assumptions()
    r_disc = a.npv_discount_rate
    n_yr = a.npv_years
    pv_factor = sum(1.0 / (1.0 + r_disc) ** t for t in range(1, n_yr + 1))
    caps = sorted({r.capacity_tpy for r in results})

    ref_prices = [
        ("Soy protein ($1.00/kg)",    1.00, "-",  1.00),
        ("Fishmeal ($1.75/kg)",        1.75, "--", 0.80),
        ("Whey protein ($4.00/kg)",    4.00, ":",  0.65),
        ("Spirulina ($8.00/kg)",       8.00, "-.", 0.50),
    ]

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        for price_label, price_val, ls, alpha in ref_prices:
            npvs = []
            for c in caps:
                subset = [r for r in results if r.capacity_tpy == c and r.feed == feed]
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
        lambda x, _: f"{int(x):,}"))
    ax.set_xticks(caps)
    ax.set_xlabel("Plant capacity (t/y dry SCP)")
    ax.set_ylabel(f"NPV (USD millions, {n_yr}-year, {int(r_disc*100)}% discount)")
    ax.set_title(
        f"NPV vs Scale — all feedstocks & benchmark selling prices\n"
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

    price_max = max(PROTEIN_BENCHMARKS.values()) * 1.4
    prices = np.linspace(0, price_max, 300)

    fig, ax = plt.subplots(figsize=(12, 6.5))

    for feed in FEED_ORDER:
        subset = [r for r in results if r.capacity_tpy == cap and r.feed == feed]
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

    for label, price in PROTEIN_BENCHMARKS.items():
        if price <= price_max:
            ax.axvline(price, ls=":", lw=0.8, color="#aaaaaa", zorder=1)
            ylim = ax.get_ylim()
            ax.text(price + 0.05, ylim[1] * 0.9, label,
                    fontsize=7, color="#888888", rotation=90, va="top")

    ax.set_xlabel("Selling price (USD / kg dry SCP)")
    ax.set_ylabel(f"NPV (USD millions, {n_yr}-year, {int(r_disc*100)}% discount)")
    ax.set_title(
        f"Net Present Value vs Selling Price — {int(cap):,} t/y\n"
        f"(best mode per feed, includes labor, {int(r_disc*100)}% discount, "
        f"{n_yr}-year horizon)",
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
    """
    Build all investor-ready figures.

    Returns dict[name → Figure].  Pass ``save_dir`` to write 300 dpi PNGs.
    In Jupyter the figures render inline automatically.
    """
    _apply_style()
    specs: List[Tuple[str, ...]] = [
        ("01_msp_overview",),
        ("02_cost_structure",),
        ("03_sensitivity_tornado",),
        ("04_scale_curve",),
        ("05_capex_detail",),
        ("06_npv_vs_scale",),
        ("07_npv_analysis",),
    ]
    builders = [
        lambda: fig_msp_overview(results),
        lambda: fig_cost_structure(results),
        lambda: fig_sensitivity(results),
        lambda: fig_scale_curve(results),
        lambda: fig_capex_detail(results),
        lambda: fig_npv_vs_scale(results),
        lambda: fig_npv_analysis(results),
    ]

    figs: Dict[str, plt.Figure] = {}
    t_all = time.perf_counter()
    if verbose:
        _log("[scp] Building figures (first run may take 10–30 s for font cache) ...")

    for (name,), builder in zip(specs, builders):
        if verbose:
            _log(f"  [fig] {name} ...")
        t0 = time.perf_counter()
        figs[name] = builder()
        if verbose:
            _log(f"  [fig] {name} done ({time.perf_counter() - t0:.1f} s)")

    if verbose:
        _log(f"[scp] Figures complete — {time.perf_counter() - t_all:.1f} s total")

    if save_dir is not None:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        if verbose:
            _log(f"[scp] Saving PNGs to {out.resolve()} ...")
        for name, fig in figs.items():
            p = out / f"{name}.png"
            fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
            if verbose:
                _log(f"  [save] {p.name}")
        if verbose:
            _log("[scp] Save complete.")

    if show:
        plt.show()

    return figs


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY  POINT
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    _log("[scp] C. necator SCP technoeconomic model ($2M labor, 8% NPV, 80 g/L CDW)")
    _log("=" * 56)
    results = run_all_scenarios()
    print()
    print(format_report(results))
    print()
    print("Major CapEx items EXCLUDED (>$100 k/unit — review later):")
    for item in MAJOR_CAPEX_EXCLUDED:
        print(f"  • {item}")
    print()
    print("Minor CapEx INCLUDED at smallest capacity (50 t/y):")
    ref = next(r for r in results
               if r.capacity_tpy == 50 and r.feed == Feed.H2_CO2
               and r.mode == Mode.BATCH)
    for name, purchase, annual in ref.capex_included:
        print(f"  • {name:30s}  purchase ${purchase:>8,.0f}   →  ${annual:>7,.0f}/y")
    for name, purchase in ref.capex_excluded:
        print(f"  ✗ {name:30s}  purchase ${purchase:>8,.0f}   (EXCEEDS threshold)")
    print()
    _log("[scp] Generating figures ...")
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        script_dir = Path(".")
    create_all_figures(results, save_dir=script_dir / "scp_80gL_figures")
    _log("[scp] Done.")


# ── Jupyter quick-start ────────────────────────────────────────────────────
#
# Paste this file into one cell and run.  Then in the next cell:
#
#     results = run_all_scenarios()
#     figs    = create_all_figures(results)          # inline display
#     # figs  = create_all_figures(results,
#     #             save_dir="scp_figures")           # also save PNGs
#
# To tweak an assumption:
#     a = Assumptions(yield_dlp=0.45, dlp_price_per_kg_sugar=0.10)
#     results = run_all_scenarios(assumptions=a)
#     figs    = create_all_figures(results)

if __name__ == "__main__":
    main()
