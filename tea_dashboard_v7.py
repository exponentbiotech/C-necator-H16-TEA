#!/usr/bin/env python3
"""
tea_dashboard_v7.py — Streamlit Cloud entry-point shim (v10 is the active model).

This file was promoted to a shim so that Streamlit Cloud serves the current
active model regardless of which filename the cloud app is configured
against. The original v7 code is preserved verbatim in
tea_dashboard_v7_archive.py so that revert is a one-line change (see
below).

Reverting to v9 is a one-line change below: swap "tea_dashboard_v10.py" for
"tea_dashboard_v9.py", commit, push. Reverting all the way to v7 is the
same one-line change but pointing at "tea_dashboard_v7_archive.py".

v10 supersedes v9:
  - Human-grade SCP (HGP) toggle. When OFF, behavior matches v9 exactly
    (feed-grade SCP + PHA/PHBV biorefinery). When ON, the non-PHA fraction
    of CDW is sold as human-grade whole-cell protein mash at the HGP
    selling price (default $8/kg) with an HGP-specific DSP cost line
    (endotoxin removal + food-grade spray drying + QA, default $1.80/kg HGP).
  - HGP sub-mode selector: "Co-production with polymer" keeps PHA unchanged;
    "HGP alone" runs the fermenter N-replete and forces PHB to ~8% basal.
  - Regulatory caveat surfaced in the sidebar and on the main page: no
    bacterial SCP is currently GRAS-approved for human food in the US;
    EFSA novel-food review typically takes 2-3 years.
  - New references: Finnigan 2019, Ritala 2017, Solar Foods 2024, van
    Loosdrecht 2016, Calysta 2023-25, Braunegg 1998, Khanna 2005.
  - All v9 functionality (DSP pathway selector, PHBV co-production,
    continuous/fed-batch mode, SCP price slider, CapEx sliders,
    references, investor-memo-style figures) is preserved.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v10.py"
runpy.run_path(str(_active), run_name="__main__")
