# Payroll Process Automation Suite (PPAS)

Enterprise payroll automation platform built around validated Python
automation scripts developed during a Tata Steel internship.

PPAS centralizes payroll report generation, validation, EPFO reconciliation,
audit logging and execution history into one professional web application.

---

## Core Value

- Reduces manual Excel effort
- Improves processing speed
- Minimizes human error
- Generates audit-ready reports

---

## Architecture

```text
Streamlit Pages (UI only)
        ↓
modules/wrappers.py        → orchestration, ZIP bundles, manifests, history
        ↓
modules/module_1.py        → Payroll Report Generation Engine
modules/module_2_processing.py → Stage 1: Processing Engine
modules/module_2_validation.py → Stage 2: Validation Engine
        ↓
outputs/run_<id>/          → isolated run artifacts
database/ppas_history.db   → SQLite audit trail
```

**Design rules**
- Business logic is never modified — only wrapped.
- UI never contains business logic.
- Every run is isolated, logged and recorded.

---

## Project Structure

```text
Payroll_Process_Automation_Suite/
├── .streamlit/config.toml      # enterprise light theme
├── app.py                      # entry point + navigation
├── pages/
│   ├── Home.py                 # dashboard
│   ├── Payroll_Report_Generation.py
│   ├── Payroll_Validation.py
│   ├── History.py              # SQLite audit trail + re-downloads
│   └── About.py
├── modules/
│   ├── utils.py                # theme + UI components
│   ├── logger.py
│   ├── database.py             # SQLite layer
│   ├── wrappers.py             # orchestration
│   ├── module_1.py
│   ├── module_2_processing.py
│   └── module_2_validation.py
├── assets/custom.css
├── uploads/  outputs/  logs/  database/
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

> **Theme note:** if the browser ever shows a dark canvas, open
> **⋮ → Settings → Theme → Light** once (browser preference overrides config).

---

## Module Usage

### Module 1 — Payroll Report Generation
**Inputs:** Higher Pension Master (Approved/Rejected sheets) + raw EPFO wage
files (tab-delimited `.xls`, upload or server folder).
**Outputs:** employee workbooks, success/error/missing logs,
`Employee_Reports.zip`.

### Module 2 — Payroll Validation & Reconciliation
**Inputs:** Employee Master (officer/non-officer), 12-14 Arrear Master,
18-19 Arrear Master, EPFO combined files (folder/upload), optional Module 1
reports override (folder/upload or latest in-app run).
**Outputs:** validated reports, `Difference_Report.xlsx`,
`Validated_Reports.zip`, validation logs.

---

## History & Audit

- Every execution (success **and** failure) is stored in SQLite:
  date, module, status, employees, reports, errors, duration, outputs, inputs.
- Previous ZIP bundles are re-downloadable from the History page.
- Run manifests (`run_manifest.json`) persist machine-readable summaries.

---

## Docker Deployment

```bash
docker build -t ppas .
docker run -p 8501:8501 \
  -v ppas_outputs:/app/outputs \
  -v ppas_database:/app/database \
  ppas
```

---

## Roadmap

- Module 3 — UAN Contact Extractor (Playwright)
- Module 4 — SAP Payroll Reconciliation
- Module 5 — Payroll Analytics Dashboard
- MySQL persistence, authentication, cloud hosting

---

## Changelog

| Phase | Delivery |
|---|---|
| 1 | Structure, navigation, enterprise theme |
| 2 | Module 1 integration (uploads → progress → ZIP → summary) |
| 3 | Module 2 integration as one module; folder-path sources |
| 4 | SQLite history, failure recording, dashboard metrics, re-downloads |
| 5 | CSS polish, documentation, Docker, deployment readiness |

*Internal use only.*