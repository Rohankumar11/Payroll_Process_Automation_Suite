"""
About page for Payroll Process Automation Suite.

Final enterprise documentation page covering problem, workflow,
architecture, audit/logging, deployment and roadmap.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


st.title("About")
st.caption("Payroll Process Automation Suite • v1.0.0")

st.subheader("Business Problem")
st.markdown(
    """
    Payroll and HR teams historically process EPFO wage revisions, arrears and
    reconciliation through repetitive, manual Excel workflows:

    - Reading raw EPFO wage exports
    - Mapping UAN ↔ Member ID across pension application sheets
    - Cleaning wage months and rounding wage values
    - Applying 12-14 revised salary and 18-19 arrears
    - Reconciling TSL totals against EPFO uploaded wages
    - Validating final salary values and rebuilding summary blocks

    These steps are slow, error-prone and difficult to audit.
    """
)

st.subheader("Automation Workflow")
st.markdown(
    """
    **Module 1 — Payroll Report Generation**
    Raw EPFO wage files + Higher Pension master → employee-wise payroll
    workbooks with formulas, formatting and logs.

    **Module 2 — Payroll Validation & Reconciliation** *(one user-facing module,
    two internal stages)*
    - *Stage 1 (Processing):* applies 12-14 revised salary, 18-19 arrears,
      calculates Final TSL totals and EPFO differences with remarks.
    - *Stage 2 (Validation):* recalculates salary/arrear consistency, removes
      duplicate summaries and writes one clean reconciliation block.

    Output: audit-ready validated reports, difference report and ZIP bundles.
    """
)

st.subheader("Technology Stack")
st.markdown(
    """
    | Layer | Technology |
    |---|---|
    | Frontend | Streamlit |
    | Backend | Python 3.10+ |
    | Data | pandas, numpy, openpyxl |
    | Files | pathlib, shutil, zipfile |
    | Persistence | sqlite3 (history), JSON manifests |
    | Logging | logging module + run-scoped text logs |
    | Future | PyMuPDF, Playwright, MySQL, Docker, Cloud |
    """
)

st.subheader("System Architecture")
st.markdown(
    """
    ```text
    Streamlit Pages (UI only)
            ↓
    modules/wrappers.py   (orchestration, ZIP, manifests, history)
            ↓
    modules/module_1.py / module_2_processing.py / module_2_validation.py
    (pure business logic - zero Streamlit imports)
            ↓
    outputs/run_<id>/  (employee_reports | processed | validated | logs | ZIP)
    database/ppas_history.db  (audit trail)
    ```

    Every execution is isolated in its own run folder and recorded in SQLite
    with inputs, outputs, durations, counts and error details.
    """
)

st.subheader("Logging & Audit Trail")
st.markdown(
    """
    - `logs/app.log` — application-level logger (all modules and pages)
    - Run-scoped logs — `process_log.txt`, `error_log.txt`,
      `validation_log.txt`, `success_log.txt`, `missing_memberid.txt`
    - Registers — `completed_files.xlsx`, `failed_files.xlsx`
    - History page — SQLite-backed execution table with re-download support
    """
)

st.subheader("Deployment")
st.markdown(
    """
    - **Local / internal server:** `streamlit run app.py`
      (headless mode pre-configured in `.streamlit/config.toml`)
    - **Docker:** `docker build -t ppas . && docker run -p 8501:8501 ppas`
    - **Cloud-ready:** Streamlit Community Cloud compatible
      (root `app.py` + `requirements.txt`)
    """
)

st.subheader("Future Enhancements")
st.markdown(
    """
    - **Module 3 — UAN Contact Extractor** (Playwright, EPFO portal)
    - **Module 4 — SAP Payroll Reconciliation**
    - **Module 5 — Payroll Analytics Dashboard**
    - MySQL persistence layer (drop-in replacement for SQLite)
    - Role-based authentication (HR / Payroll / Admin)
    """
)

st.subheader("Version History")
st.markdown(
    """
    | Version | Milestone |
    |---|---|
    | v1.0.0 | Phase 1 — Structure, navigation, enterprise theme |
    | v1.0.0 | Phase 2 — Module 1 integration |
    | v1.0.0 | Phase 3 — Module 2 integration (single-module UX) |
    | v1.0.0 | Phase 4 — SQLite history, logging, re-downloads |
    | v1.0.0 | Phase 5 — UI polish, documentation, Docker deployment |
    """
)

st.subheader("Developer Information")
st.markdown(
    """
    Developed as an enterprise-grade automation platform around production
    Python scripts created during a **Tata Steel internship**.

    Design principles: zero modification of validated business logic,
    strict UI/logic separation, audit-ready outputs, and incremental
    scalability for future payroll modules.
    """
)