#!/usr/bin/env python3
"""
tea_dashboard_v5.py — Streamlit Cloud entry-point shim (v6 is the active model).

The existing Streamlit Cloud deployment points at this filename. v6 is the
current working model; v5 (archived) is preserved at tea_dashboard_v5_archive.py
so you can still diff against the previous behavior.

v6 adds:
  - Corrected SCP market price (default $1.80/kg feed-grade, $5.00/kg HGP)
  - New scenario S3_HGP (human-grade protein, food-grade DSP, zero PHB)
  - Clearer UI distinction between market price and MSP
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v6.py"
runpy.run_path(str(_active), run_name="__main__")
