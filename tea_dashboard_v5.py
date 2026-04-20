#!/usr/bin/env python3
"""
tea_dashboard_v5.py — Streamlit Cloud entry-point shim (v8 is the active model).

The existing Streamlit Cloud deployment points at this filename. v8 is the
current working model. Prior revisions are preserved in-repo so you can
diff against their behavior or revert without touching Streamlit Cloud
config:

  - tea_dashboard_v5_archive.py  (v5 frozen state)
  - tea_dashboard_v6.py          (exploratory HGP scenario, retired)
  - tea_dashboard_v7.py          (previous live model: continuous only)
  - tea_dashboard_v8.py          (ACTIVE: adds fed-batch mode toggle)

Reverting to v7 is a one-line change below: swap "tea_dashboard_v8.py" for
"tea_dashboard_v7.py", commit, push.

v8 supersedes v7:
  - Adds a global fermentation-mode toggle (continuous OR fed-batch). The
    continuous branch behaves identically to v7 (60 g/L CDW, 24 h HRT,
    85% uptime, 60% PHB), so v8-continuous == v7 numerically.
  - Fed-batch mode exposes endpoint CDW titer (60-250 g/L, default 150),
    PHB content (default 68%), cycle time (36-120 h, default 76), duty
    cycle (40-85%, default 68%), and an OTR-retrofit CapEx adder
    (0-15 M$, default 0; typical brewery-vessel retrofit $4-12M).
  - Fed-batch defaults are literature-anchored (Kim 1994 BB 43:892,
    Ryu 1997 BB 55:28, Budde 2011 AEM 77:2847).
  - All other v7 functionality (SCP price slider, scenario definitions,
    CapEx sliders, references, memo-facing traceability) is preserved.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v8.py"
runpy.run_path(str(_active), run_name="__main__")
