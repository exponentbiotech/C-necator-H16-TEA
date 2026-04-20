#!/usr/bin/env python3
"""
tea_dashboard_v7.py — Streamlit Cloud entry-point shim (v9 is the active model).

This file was promoted to a shim so that Streamlit Cloud serves the current
active model regardless of which filename the cloud app is configured
against. The original v7 code is preserved verbatim in
tea_dashboard_v7_archive.py so that revert is a one-line change (see
below).

Reverting to v7 is a one-line change below: swap "tea_dashboard_v9.py" for
"tea_dashboard_v7_archive.py", commit, push.

v9 supersedes v7 and v8:
  - DSP pathway selector (NaOCl baseline, NaOH hot alkali, Mechanical +
    enzymatic — new v9 default). Each pathway has its own DSP cost
    lines and phase-scaled CapEx adder.
  - Explicit PHBV co-production with co-substrate cost line and
    HV-scaled selling price.
  - All continuous / fed-batch mode functionality preserved from v8
    (Kim 1994, Ryu 1997, Budde 2011 anchors).
  - All SCP price slider / CapEx slider / reference-trace functionality
    preserved from v7.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v9.py"
runpy.run_path(str(_active), run_name="__main__")
