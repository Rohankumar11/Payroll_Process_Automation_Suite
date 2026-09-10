"""
Payroll Process Automation Suite (PPAS)
Main application entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules.utils import apply_enterprise_theme, render_sidebar_footer

CUSTOM_CSS_PATH = ROOT_DIR / "assets" / "custom.css"

st.set_page_config(
    page_title="Payroll Process Automation Suite",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_enterprise_theme()

if CUSTOM_CSS_PATH.exists():
    st.markdown(
        f"<style>{CUSTOM_CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

HOME_PAGE = st.Page("pages/Home.py", title="Home", icon="🏠", default=True)

REPORT_GENERATION_PAGE = st.Page(
    "pages/Payroll_Report_Generation.py",
    title="Payroll Report Generation",
    icon="📄",
)

VALIDATION_PAGE = st.Page(
    "pages/Payroll_Validation.py",
    title="Payroll Validation & Reconciliation",
    icon="✅",
)

BASIC_PAY_PAGE = st.Page(
    "pages/Basic_Pay_Filler.py",
    title="Basic Pay Filler",
    icon="🧮",
)

HISTORY_PAGE = st.Page("pages/History.py", title="History", icon="🕘")

ABOUT_PAGE = st.Page("pages/About.py", title="About", icon="ℹ️")

navigation = st.navigation(
    [
        HOME_PAGE,
        REPORT_GENERATION_PAGE,
        VALIDATION_PAGE,
        BASIC_PAY_PAGE,
        HISTORY_PAGE,
        ABOUT_PAGE,
    ]
)

navigation.run()

render_sidebar_footer()