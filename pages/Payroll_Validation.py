"""
Page: Payroll Validation & Reconciliation (Module 2).

The UI exposes Module 2 as ONE module.
Internally the wrappers execute Stage 1 (processing) and
Stage 2 (validation) seamlessly.

All multi-file inputs support uploads (ZIP/files) or read-only
server folder paths, matching the original automation workflow.
"""

from __future__ import annotations

import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, List

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules import wrappers
from modules.logger import get_logger
from modules.utils import render_input_source

page_logger = get_logger("ppas.page.module_2", "app.log")


# ----------------------------------------------------------------------
# Upload helpers
# ----------------------------------------------------------------------
def _unique_name(name: str, seen: set) -> str:
    """Deduplicate upload file names within one run."""
    if name not in seen:
        seen.add(name)
        return name
    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 1
    while f"{stem}_{counter}{suffix}" in seen:
        counter += 1
    final_name = f"{stem}_{counter}{suffix}"
    seen.add(final_name)
    return final_name


def _collect_uploads(uploads: List[Any], destination: Path) -> Path:
    """
    Persist uploads into destination.

    ZIP uploads are extracted (flat, temp files skipped).
    Other uploads are saved with their original names.
    """
    destination.mkdir(parents=True, exist_ok=True)
    seen = set()

    for upload in uploads:
        original_name = Path(upload.name).name
        payload = upload.read()

        if original_name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                for member in archive.namelist():
                    if member.endswith("/"):
                        continue
                    base = Path(member).name
                    if not base or base.startswith("~$"):
                        continue
                    target = destination / _unique_name(base, seen)
                    target.write_bytes(archive.read(member))
        else:
            target = destination / _unique_name(original_name, seen)
            target.write_bytes(payload)

    return destination


def render_results(summary: dict) -> None:
    """Render Module 2 execution results."""
    st.success(
        f"Processing completed in {summary['processing_time_seconds']} seconds."
    )

    card_1, card_2, card_3, card_4 = st.columns(4)
    with card_1:
        st.metric("Reports Validated", summary["reports_validated"])
    with card_2:
        st.metric("Reports Corrected", summary["reports_corrected"])
    with card_3:
        st.metric("Difference Found", summary["difference_found"])
    with card_4:
        st.metric("Processing Time", f"{summary['processing_time_seconds']}s")

    zip_path = Path(summary["zip_path"])
    difference_path = Path(summary["difference_report_path"])

    download_1, download_2 = st.columns(2)
    with download_1:
        if zip_path.exists():
            st.download_button(
                label="Download Validated_Reports.zip",
                data=zip_path.read_bytes(),
                file_name="Validated_Reports.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
            )
    with download_2:
        if difference_path.exists():
            st.download_button(
                label="Download Difference_Report.xlsx",
                data=difference_path.read_bytes(),
                file_name="Difference_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

    if summary["files"]:
        with st.expander("Reconciliation Summary"):
            st.dataframe(
                pd.DataFrame(summary["files"]),
                use_container_width=True,
                hide_index=True,
            )

    if summary["failed_stage1"]:
        with st.expander(f"Stage Failures ({len(summary['failed_stage1'])})"):
            st.code("\n".join(summary["failed_stage1"]))


# ----------------------------------------------------------------------
# Page layout
# ----------------------------------------------------------------------
st.title("Payroll Validation & Reconciliation")
st.caption("Validate payroll reports and reconcile them with EPFO uploaded data.")

module1_available = "module_1_result" in st.session_state

if module1_available:
    st.info(
        "Latest Module 1 run detected. Its employee reports will be used "
        "automatically unless you provide an override source below."
    )

st.markdown("### Input Files")

row1_left, row1_right = st.columns(2)
with row1_left:
    master_upload = st.file_uploader(
        "Employee Master (Officer / Non-Officer)",
        type=["xlsx", "xls"],
        help="Workbook containing UAN, P. No. and designation (column 6).",
    )
with row1_right:
    arrear_1214_upload = st.file_uploader(
        "12-14 Arrear Master",
        type=["xlsx", "xls"],
        help="Arrear master with P.No. and monthly (date-header) columns.",
    )

row2_left, row2_right = st.columns(2)
with row2_left:
    arrear_1819_upload = st.file_uploader(
        "18-19 Arrear Master",
        type=["xlsx", "xls"],
        help="Arrear master with PERNR, Month and BDA_DIFF_RATE columns.",
    )
with row2_right:
    combined_source = render_input_source(
        label="EPFO Combined Uploaded Files",
        key="m2_combined",
        upload_types=["zip", "xlsx", "xls", "csv"],
        help_text=(
            "Combined EPFO wage files. Folder mode reads your local "
            "Combined_zipped_files directory directly (read-only)."
        ),
    )

row3_left, _ = st.columns(2)
with row3_left:
    reports_source = render_input_source(
        label="Module 1 Employee Reports (optional override)",
        key="m2_reports",
        upload_types=["zip", "xlsx"],
        help_text=(
            "Optional. Overrides the latest Module 1 run outputs. "
            "Folder mode reads a local employee-reports folder (read-only)."
        ),
        folder_file_filter=".xlsx",
    )

reports_ready = reports_source["ready"] or module1_available
inputs_ready = (
    master_upload is not None
    and arrear_1214_upload is not None
    and arrear_1819_upload is not None
    and combined_source["ready"]
    and reports_ready
)

run_clicked = st.button(
    "Validate Reports",
    type="primary",
    disabled=not inputs_ready,
    use_container_width=True,
)

if run_clicked:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT_DIR / "outputs" / f"run_m2_{run_id}"
    upload_dir = run_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    master_path = upload_dir / f"master{Path(master_upload.name).suffix}"
    master_path.write_bytes(master_upload.read())

    arrear_1214_path = upload_dir / f"arrear_1214{Path(arrear_1214_upload.name).suffix}"
    arrear_1214_path.write_bytes(arrear_1214_upload.read())

    arrear_1819_path = upload_dir / f"arrear_1819{Path(arrear_1819_upload.name).suffix}"
    arrear_1819_path.write_bytes(arrear_1819_upload.read())

    # ---------------- combined source resolution ----------------
    if combined_source["mode"] == "upload":
        combined_folder = _collect_uploads(
            combined_source["uploads"], upload_dir / "combined"
        )
    else:
        combined_folder = combined_source["folder"]

    # ---------------- reports source resolution ----------------
    if reports_source["ready"]:
        if reports_source["mode"] == "upload":
            reports_folder = _collect_uploads(
                reports_source["uploads"], upload_dir / "reports"
            )
        else:
            reports_folder = reports_source["folder"]
    else:
        reports_folder = (
            Path(st.session_state["module_1_result"]["run_dir"]) / "employee_reports"
        )

    progress_bar = st.progress(0, text="Initializing run")

    def _update_progress(stage: str, fraction: float) -> None:
        progress_bar.progress(min(max(fraction, 0.0), 1.0), text=stage)

    try:
        summary = wrappers.run_module_2(
            master_file=master_path,
            arrear_1214_file=arrear_1214_path,
            arrear_1819_file=arrear_1819_path,
            reports_folder=reports_folder,
            combined_folder=combined_folder,
            run_dir=run_dir,
            progress_callback=_update_progress,
        )
    except KeyError as exc:
        progress_bar.empty()
        st.error(
            f"A required column is missing in an input file: {exc}. "
            "Please verify the master/arrear file formats."
        )
        page_logger.error("Module 2 KeyError: %s", exc)
    except ValueError as exc:
        progress_bar.empty()
        st.error(f"Invalid input file detected: {exc}")
        page_logger.error("Module 2 ValueError: %s", exc)
    except Exception as exc:
        # PATCH 2: Surface exception identity on-screen for immediate diagnosis
        progress_bar.empty()
        st.error(
            "An unexpected error occurred during validation. "
            "Technical details have been written to the application log."
        )
        st.code(f"{type(exc).__name__}: {exc}")
        st.caption(
            "Full traceback saved to logs/app.log — "
            "share it with the development team if the issue persists."
        )
        page_logger.exception("Module 2 unexpected error: %s", exc)
    else:
        st.session_state["module_2_result"] = summary
        st.rerun()

if "module_2_result" in st.session_state:
    st.divider()
    st.markdown("### Latest Execution Results")
    render_results(st.session_state["module_2_result"])