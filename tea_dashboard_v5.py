#!/usr/bin/env python3
"""
tea_dashboard_v5.py — Streamlit Cloud entry-point shim (v7 is the active model).

The existing Streamlit Cloud deployment points at this filename. v7 is the
current working model; v5 (archived) and v6 (archived) are preserved at
tea_dashboard_v5_archive.py and tea_dashboard_v6.py respectively so you can
diff against their prior behavior.

v7 supersedes v5 and v6:
  - Corrected feed-grade SCP market-price default to $2.00/kg (anchored to
    fishmeal / FeedKind / UniProtein 2024-2025 benchmarks).
  - Widened the SCP selling-price slider to $0.30-$8.00/kg so downside
    stress tests and specialty upside can both be examined.
  - The exploratory human-grade-protein scenario introduced in v6 is not
    carried into v7. The modeled scope is the SCP+PHA biorefinery (S1, S2).
  - Sidebar caption clarifies market price vs MSP and carries the benchmark
    references inline.
"""
from __future__ import annotations

import runpy
from pathlib import Path

_here = Path(__file__).resolve().parent
_active = _here / "tea_dashboard_v7.py"
runpy.run_path(str(_active), run_name="__main__")
