"""
Module 2 - Stage 1: Payroll Processing Engine.

Wraps the original working script (module_2_1.py) into callable
functions WITHOUT changing business logic.

Workflow:
    1. Load employee master (officer / non-officer) and filter NON officers.
    2. Load 12-14 and 18-19 arrear masters.
    3. For each employee:
         - Locate Module 1 report by UAN
         - Apply 12-14 Revised Salary (months <= Sep-2014)
         - Apply 18-19 Arrear (BDA_DIFF_RATE)
         - Fill empty Revised Salary with EPF Wages
         - Calculate Final TSL Total
         - Reconcile against EPFO combined uploaded wages
         - Build remarks
         - Save PROCESSED_{uan}.xlsx with formulas + summary block
    4. Write process / error logs and completed / failed registers.
"""

from __future__ import annotations

import os
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

ProgressCallback = Optional[Callable[[str, float], None]]

EPFO_WAGE_COLUMN = "Wages on which PF contribution was paid"
EPFO_MONTH_COLUMN = (
    "Wage Month (all the months from date of joining to date of leaving)"
)
CUTOFF_1214 = pd.Timestamp("2014-09-01")


# ----------------------------------------------------------------------
# Logging helper (run-scoped, original line format preserved)
# ----------------------------------------------------------------------
class _RunLogger:
    """Append-style run logger mirroring the original write_log/write_error."""

    def __init__(self, log_folder: Path) -> None:
        log_folder = Path(log_folder)
        log_folder.mkdir(parents=True, exist_ok=True)
        self.log_file = log_folder / "process_log.txt"
        self.error_file = log_folder / "error_log.txt"

    def info(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as handle:
            handle.write(f"[INFO] {timestamp} - {message}\n")
        print(message)

    def error(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.error_file, "a", encoding="utf-8") as handle:
            handle.write(f"[ERROR] {timestamp} - {message}\n")
        print(f"ERROR: {message}")


# ----------------------------------------------------------------------
# Original helper functions (preserved)
# ----------------------------------------------------------------------
def find_file_by_uan(folder_path: Path, uan: str) -> Optional[str]:
    """Locate the first non-temporary file containing the UAN."""
    files = glob(os.path.join(str(folder_path), f"*{uan}*"))
    files = [
        f for f in files
        if not os.path.basename(f).startswith("~$")
    ]
    if files:
        return files[0]
    return None


def next_month(month_str: str) -> str:
    """Return the month after month_str in %b-%y format (retained from original)."""
    dt = pd.to_datetime(month_str, format="%b-%y")
    next_dt = dt + relativedelta(months=1)
    return next_dt.strftime("%b-%y")


def read_any_file(file_path: Path) -> Optional[pd.DataFrame]:
    """Universal reader for xlsx / xls / csv (original behavior preserved)."""
    extension = os.path.splitext(str(file_path))[1].lower()
    try:
        if extension == ".xlsx":
            return pd.read_excel(file_path, engine="openpyxl")
        if extension == ".xls":
            return pd.read_excel(file_path, engine="xlrd")
        if extension == ".csv":
            try:
                return pd.read_csv(file_path, encoding="utf-8")
            except Exception:
                return pd.read_csv(file_path, encoding="latin1")
        return None
    except Exception as exc:
        print(f"ERROR READING FILE : {file_path}")
        print(str(exc))
        return None


def _safe_strip_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Type-safe column stripping.

    String columns are stripped; datetime columns (Excel date headers
    in the 12-14 master) are preserved so month detection works.
    """
    cleaned = [
        col.strip() if isinstance(col, str) else col
        for col in frame.columns
    ]
    frame.columns = cleaned
    return frame


# ----------------------------------------------------------------------
# Input loading
# ----------------------------------------------------------------------
def _load_inputs(
    master_file: Path,
    arrear_1214_file: Path,
    arrear_1819_file: Path,
    employee_limit: Optional[int],
) -> tuple:
    """Load and normalize the three master files."""
    master_df = pd.read_excel(master_file)

    # Original filter: designation column (index 5) contains "NON"
    master_df = master_df[
        master_df.iloc[:, 5].astype(str).str.upper().str.contains("NON")
    ]
    if employee_limit is not None:
        master_df = master_df.head(employee_limit)

    arrear_1214_df = pd.read_excel(arrear_1214_file)
    arrear_1214_df = _safe_strip_columns(arrear_1214_df)
    arrear_1214_df["P.No."] = (
        pd.to_numeric(arrear_1214_df["P.No."], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    arrear_1819_df = pd.read_excel(arrear_1819_file)
    arrear_1819_df.columns = arrear_1819_df.columns.astype(str).str.strip()
    arrear_1819_df["PERNR"] = (
        pd.to_numeric(arrear_1819_df["PERNR"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    return master_df, arrear_1214_df, arrear_1819_df


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def process_reports(
    master_file: Path,
    arrear_1214_file: Path,
    arrear_1819_file: Path,
    reports_folder: Path,
    combined_folder: Path,
    output_folder: Path,
    log_folder: Path,
    progress_callback: ProgressCallback = None,
    employee_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Module 2 Stage 1 entry point.

    Returns an execution summary including per-employee
    reconciliation details used for the Difference Report.
    """
    started_at = datetime.now()
    logger = _RunLogger(log_folder)

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback("Loading Master Files", 0.02)

    logger.info("Loading master files")
    
    # PATCH 1: Hardened load block to prevent silent/generic failures on bad inputs
    try:
        master_df, arrear_1214_df, arrear_1819_df = _load_inputs(
            master_file, arrear_1214_file, arrear_1819_file, employee_limit
        )
    except KeyError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load master/arrear input files: {exc}"
        ) from exc
        
    logger.info("Files loaded successfully")

    completed_files: List[str] = []
    failed_files: List[str] = []
    employee_results: List[Dict[str, Any]] = []

    total = max(len(master_df), 1)

    for position, (idx, emp) in enumerate(master_df.iterrows()):
        # PATCH 1: Initialize uan before try block to prevent UnboundLocalError in except
        uan = "UNKNOWN"
        try:
            uan = str(emp["UAN"]).strip()
            pno = str(emp["P. No."]).strip()
            pno_clean = str(int(float(pno)))
            logger.info(f"Processing UAN : {uan}")

            if progress_callback:
                progress_callback(
                    f"Processing UAN {uan}",
                    0.05 + 0.9 * (position / total),
                )

            # ---------------- locate Module 1 report ----------------
            output_file = find_file_by_uan(reports_folder, uan)
            if not output_file:
                logger.error(f"Output file not found for UAN {uan}")
                failed_files.append(uan)
                employee_results.append(
                    {"UAN": uan, "Status": "Failed", "Reason": "Report not found"}
                )
                continue

            logger.info("Output file found")
            output_df = read_any_file(output_file)
            if output_df is None:
                logger.error(f"Could not read output file for {uan}")
                failed_files.append(uan)
                employee_results.append(
                    {"UAN": uan, "Status": "Failed", "Reason": "Report unreadable"}
                )
                continue

            output_df.columns = output_df.columns.astype(str).str.strip()

            if "Revised Salary" not in output_df.columns:
                output_df["Revised Salary"] = pd.NA
            if "Arrear" not in output_df.columns:
                output_df["Arrear"] = 0

            output_df["Month_Text"] = (
                output_df["Wages Month"].astype(str).str.strip().str.upper()
            )

            # ---------------- 12-14 process ----------------
            arrear_row = arrear_1214_df[arrear_1214_df["P.No."] == pno_clean]
            if arrear_row.empty:
                logger.error(f"P.No {pno} not found in 12-14 file")
            else:
                arrear_row = arrear_row.iloc[0]
                month_columns = [
                    col for col in arrear_1214_df.columns
                    if isinstance(col, datetime)
                ]
                for month_col in month_columns:
                    try:
                        month_date = pd.to_datetime(month_col, errors="coerce")
                        if pd.isna(month_date):
                            continue
                        if month_date > CUTOFF_1214:
                            continue
                        month_key = month_date.strftime("%b-%y").upper()
                        revised_salary = arrear_row[month_col]
                        mask = output_df["Month_Text"] == month_key
                        if mask.any():
                            output_df.loc[mask, "Revised Salary"] = revised_salary
                            print(f"{month_key} pasted -> {revised_salary}")
                    except Exception as exc:
                        print(f"12-14 Error : {month_col}")
                        print(str(exc))
                logger.info(f"12-14 updated for {uan}")

            # ---------------- 18-19 process ----------------
            arrear_1819_emp = arrear_1819_df[arrear_1819_df["PERNR"] == pno_clean]
            if arrear_1819_emp.empty:
                logger.error(f"P.No {pno} not found in 18-19 file")
            else:
                for _, row in arrear_1819_emp.iterrows():
                    try:
                        month_date = pd.to_datetime(
                            row["Month"], format="%b-%y", errors="coerce"
                        )
                        if pd.isna(month_date):
                            continue
                        month_key = month_date.strftime("%b-%y").upper()
                        arrear_value = row["BDA_DIFF_RATE"]
                        mask = output_df["Month_Text"] == month_key
                        output_df.loc[mask, "Arrear"] = arrear_value
                    except Exception as exc:
                        print("18-19 Error")
                        print(str(exc))
                logger.info(f"18-19 updated for {uan}")

            # ---------------- numeric conversion ----------------
            output_df["EPF Wages"] = (
                pd.to_numeric(output_df["EPF Wages"], errors="coerce").fillna(0)
            )
            output_df["Arrear"] = (
                pd.to_numeric(output_df["Arrear"], errors="coerce").fillna(0)
            )
            output_df["Revised Salary"] = pd.to_numeric(
                output_df["Revised Salary"], errors="coerce"
            )

            mask_empty = output_df["Revised Salary"].isna()
            output_df.loc[mask_empty, "Revised Salary"] = (
                output_df.loc[mask_empty, "EPF Wages"]
            )

            final_tsl = (
                pd.to_numeric(output_df["Revised Salary"], errors="coerce")
                .fillna(0)
                .sum()
            )

            # ---------------- EPFO reconciliation ----------------
            combined_file = find_file_by_uan(combined_folder, uan)
            if not combined_file:
                logger.error(f"Combined file not found for {uan}")
                failed_files.append(uan)
                employee_results.append(
                    {"UAN": uan, "Status": "Failed", "Reason": "Combined file not found"}
                )
                continue

            combined_df = read_any_file(combined_file)
            combined_df.columns = combined_df.columns.astype(str).str.strip()

            epfo_total = (
                pd.to_numeric(combined_df[EPFO_WAGE_COLUMN], errors="coerce")
                .fillna(0)
                .sum()
            )
            difference = final_tsl - epfo_total

            # ---------------- remarks ----------------
            combined_df_clean = combined_df[combined_df[EPFO_MONTH_COLUMN].notna()]
            last_uploaded_month = combined_df_clean.iloc[-1][EPFO_MONTH_COLUMN]
            last_uploaded_month = pd.to_datetime(
                str(last_uploaded_month).strip(), format="%b-%y", errors="coerce"
            )
            if pd.isna(last_uploaded_month):
                start_month = "UNKNOWN"
            else:
                start_month = (
                    last_uploaded_month + pd.DateOffset(months=1)
                ).strftime("%b %y")

            end_month_date = pd.to_datetime(
                output_df["Wages Month"], format="%b-%y", errors="coerce"
            ).max()
            if pd.isna(end_month_date):
                end_month = "UNKNOWN"
            else:
                end_month = end_month_date.strftime("%b %y")

            remarks = f"{start_month} to {end_month} wages added and arrear added"

            output_df.drop(columns=["Month_Text"], inplace=True, errors="ignore")

            # ---------------- save ----------------
            save_path = output_folder / f"PROCESSED_{uan}.xlsx"
            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                output_df.to_excel(
                    writer, sheet_name="Processed_Data", index=False
                )
                worksheet = writer.sheets["Processed_Data"]

                headers = {}
                for cell in worksheet[1]:
                    headers[cell.value] = cell.column_letter
                epf_col = headers["EPF Wages"]
                arrear_col = headers["Arrear"]
                revised_col = headers["Revised Salary"]

                for excel_row in range(2, len(output_df) + 2):
                    revised_cell = f"{revised_col}{excel_row}"
                    current_value = worksheet[revised_cell].value
                    if current_value in [None, ""]:
                        worksheet[revised_cell] = (
                            f"={epf_col}{excel_row}+{arrear_col}{excel_row}"
                        )

                start_row = len(output_df) + 5
                worksheet[f"B{start_row}"] = "DATA UPLOADED IN EPFO"
                worksheet[f"C{start_row}"] = "FINAL DATA BY TSL"
                worksheet[f"D{start_row}"] = "DIFFERENCE"
                worksheet[f"E{start_row}"] = "REMARKS"
                worksheet[f"B{start_row + 1}"] = epfo_total
                worksheet[f"C{start_row + 1}"] = final_tsl
                worksheet[f"D{start_row + 1}"] = difference
                worksheet[f"E{start_row + 1}"] = remarks

            completed_files.append(uan)
            employee_results.append(
                {
                    "UAN": uan,
                    "Status": "Processed",
                    "EPFO Total": round(float(epfo_total), 2),
                    "Final TSL Total": round(float(final_tsl), 2),
                    "Difference": round(float(difference), 2),
                    "Remarks": remarks,
                }
            )
            logger.info(f"Saved : {save_path}")

        except Exception as exc:
            failed_files.append(uan)
            employee_results.append(
                {"UAN": uan, "Status": "Failed", "Reason": str(exc)}
            )
            logger.error(f"Unexpected error for UAN {uan} : {str(exc)}")

    # ---------------- registers ----------------
    pd.DataFrame({"Completed_UAN": completed_files}).to_excel(
        Path(log_folder) / "completed_files.xlsx", index=False
    )
    pd.DataFrame({"Failed_UAN": failed_files}).to_excel(
        Path(log_folder) / "failed_files.xlsx", index=False
    )
    logger.info("Processing completed")

    duration = (datetime.now() - started_at).total_seconds()

    return {
        "stage": "Stage 1 — Processing",
        "completed": completed_files,
        "failed": failed_files,
        "employees": employee_results,
        "duration_seconds": round(duration, 2),
    }