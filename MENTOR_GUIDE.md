# Payroll Process Automation Suite — User Guide

A self-contained payroll automation application.
All processing happens **on this computer** — no data leaves the machine.

---

## 1. Requirements

- Windows 10/11
- Python 3.10+ (python.org — tick **"Add Python to PATH"**)
- Internet connection for the **first run only** (downloads libraries)

## 2. Start the Application

1. Unzip the folder anywhere (e.g. `D:\PPAS`).
2. Double-click **`install_and_run.bat`**.
3. Wait for the browser to open (`http://localhost:8501`).
4. Keep the black console window open while working.

> If the screen looks dark: click **⋮ (top right) → Settings → Theme → Light** — one time only.

To stop the app: close the black window.

## 3. The Pages

### 🏠 Home
Live dashboard: reports generated, employees processed,
successful executions, estimated manual time saved.

### 📄 Payroll Report Generation (Module 1)
**Inputs**
- *Higher Pension Master* — Excel file with sheets
  `Approved Application` and `Rejected Application`.
- *Raw EPFO Wage Files* — the tab-delimited `.xls` wage exports.
  Either upload them, or choose **Server folder path** and paste the
  folder that contains them (read-only; nothing is modified there).

**Run** → progress bar → summary cards →
**Download Employee_Reports.zip** (one workbook per employee + logs).

### ✅ Payroll Validation & Reconciliation (Module 2)
**Inputs**
- *Employee Master (Officer / Non-Officer)*
- *12-14 Arrear Master*
- *18-19 Arrear Master*
- *EPFO Combined Uploaded Files* — usually a folder
  (use **Server folder path**, e.g. `D:\EPFO_work\Combined_zipped_files`)
- *Module 1 Employee Reports* — optional:
  - if you ran Module 1 in this session, it is picked up **automatically**;
  - otherwise paste your `output_files` folder path.

**Run** → summary cards → downloads:
- **Validated_Reports.zip** (final audit-ready workbooks + logs)
- **Difference_Report.xlsx** (EPFO total vs TSL total per employee)

### 🧮 Basic Pay Filler
Upload *Basic_OPR.xlsx* (pay matrix) + *OPR wages workbook* →
the **Basic** column is filled month-by-month.
Downloads: updated wages file, `Not_Found_Data.txt` (missing-data report),
or both as ZIP.

### 🕘 History
Every run (success or failure) is recorded with date, counts, duration.
Previous ZIP bundles can be re-downloaded here.

### ℹ️ About
Architecture, version history and roadmap.

## 4. Where Are My Outputs?

Inside the app folder: `outputs\run_<date_time>\`
(each run is isolated: `employee_reports/`, `processed/`, `validated/`,
`logs/`, ZIP bundles). Original input folders are **never modified**.

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| "python is not recognized" | Reinstall Python with **Add to PATH**, retry |
| Installation fails | Check internet/proxy; run the .bat again |
| Browser didn't open | Visit http://localhost:8501 manually |
| Dark screen | ⋮ → Settings → Theme → Light |
| Red error box | Note the code line shown; full details in `logs\app.log` |
| Folder path "not found" | Paths must exist **on this computer**; use upload mode otherwise |

## 6. Support Information

- Application log: `logs\app.log`
- Execution database: `database\ppas_history.db`
- Version: v1.0.0