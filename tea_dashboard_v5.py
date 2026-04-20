#!/usr/bin/env python3
"""
tea_dashboard_v5.py — Streamlit Cloud entry-point shim (v9 is the active model).

The existing Streamlit Cloud deployment points at this filename. v9 is the
current working model. Prior revisions are preserved in-repo so you can
diff against their behavior or revert without touching Streamlit Cloud
config:

  - tea_dashboard_v5_archive.py  (v5 frozen state)
  - tea_dashboard_v6.py          (exploratory HGP scenario, retired)
  - tea_dashboard_v7_archive.py  (v7 frozen state; revert target)
  - tea_dashboard_v7.py          (also a shim -> v9, so cloud configs
                                   that target v7.py still resolve to v9)
  - tea_dashboard_v8.py          (v8 frozen state: adds fed-batch mode)
  - tea_dashboard_v9.py          (ACTIVE: adds DSP pathway selector
                                   + PHBV co-production toggle)

Reverting to v7 is a one-line change below: swap "tea_dashboard_v9.py"
for "tea_dashboard_v7_archive.py", commit, push.

v9 supersedes v8:
  - DSP pathway selector. NaOCl hypochlorite (v7/v8 baseline), NaOH hot
    alkali, and Mechanical + enzymatic (modern CMO standard, new v9
    default). Each pathway defines its own $/kg PHA extraction cost,
    $/kg CDW downstream cost, and phase-scaled CapEx adder. Literature
    anchors: Kessler 2001, Yu 2007, Hahn 1994.
  - Explicit PHBV co-production. Global toggle drives both S1 and S2.
    Co-substrate selector (propionate / valerate / levulinate) with
    literature defaults. HV-content slider. PHBV selling price
    auto-scales with HV content (Tianan / Kaneka / Danimer anchors);
    manual-override checkbox unlocks a flat price slider.
  - All v8 functionality (continuous / fed-batch mode, SCP price slider,
    CapEx sliders, references, memo-facing traceability) is preserved.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v9.py"
runpy.run_path(str(_active), run_name="__main__")
