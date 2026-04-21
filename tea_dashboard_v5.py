#!/usr/bin/env python3
"""
tea_dashboard_v5.py — Streamlit Cloud entry-point shim (v10 is the active model).

The existing Streamlit Cloud deployment points at this filename. v10 is the
current working model. Prior revisions are preserved in-repo so you can
diff against their behavior or revert without touching Streamlit Cloud
config:

  - tea_dashboard_v5_archive.py  (v5 frozen state)
  - tea_dashboard_v6.py          (exploratory HGP scenario, retired)
  - tea_dashboard_v7_archive.py  (v7 frozen state; revert target)
  - tea_dashboard_v7.py          (also a shim -> v10, so cloud configs
                                   that target v7.py still resolve to v10)
  - tea_dashboard_v8.py          (v8 frozen state: adds fed-batch mode)
  - tea_dashboard_v9.py          (v9 frozen state: DSP pathway selector
                                   + PHBV co-production toggle; revert
                                   target if HGP modeling is not wanted)
  - tea_dashboard_v10.py         (ACTIVE: adds human-grade SCP (HGP)
                                   toggle with co-production and HGP-alone
                                   sub-modes, on top of the full v9 feature
                                   set)

Reverting to v9 is a one-line change below: swap "tea_dashboard_v10.py"
for "tea_dashboard_v9.py", commit, push.

v10 supersedes v9:
  - Human-grade SCP (HGP) toggle. When OFF, behavior matches v9 exactly
    (feed-grade SCP + PHA/PHBV biorefinery). When ON, the non-PHA fraction
    of CDW is sold as human-grade whole-cell protein mash at the HGP
    selling price (default $8/kg; range $3-12/kg) with an incremental
    HGP-specific DSP cost line ($1.80/kg HGP default, covering endotoxin
    removal, food-grade spray drying, sanitary packaging, QA).
  - HGP production mode sub-selector: "Co-production with polymer" keeps
    the PHA stream unchanged and sells the non-PHA CDW as HGP; "HGP alone"
    operates the fermenter N-replete to suppress PHA, forcing PHB content
    to a basal 8% and selling ~92% of CDW as HGP.
  - Regulatory caveat surfaced in the sidebar and on the main page: no
    bacterial SCP is currently GRAS-approved for human food in the
    United States; EFSA novel-food review typically takes 2-3 years.
    HGP economics are pro-forma pending clearance.
  - New references: Finnigan 2019 (mycoprotein), Ritala 2017 (bacterial
    SCP review), Solar Foods 2024 (Solein investor materials), van
    Loosdrecht 2016 (protein recovery), Calysta 2023-25 (FeedKind-HP
    disclosures), Braunegg 1998 and Khanna 2005 (basal PHA under
    N-replete growth).
  - All v9 functionality (DSP pathway selector, PHBV co-production,
    continuous/fed-batch toggle, SCP price slider, CapEx sliders,
    references, memo-facing traceability, investor-memo-style figures)
    is preserved.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v10.py"
runpy.run_path(str(_active), run_name="__main__")
