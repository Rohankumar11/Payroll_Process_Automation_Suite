"""
Page: Payroll Report Generation (Module 1).

UI responsibilities only:
    - Collect inputs (uploads or read-only server folders)
    - Save uploads into the run folder
    - Execute wrappers.generate_reports()
    - Display progress, summary cards, logs and downloads
    - Record failures into SQLite history

No business logic lives in this file.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules import wrappers
from modules.logger import get_logger
from modules.utils import render_input_source

page_logger = get_logger("ppas.page.module_1", "app.log")


# ----------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------
def _save_upload(upload: Any, destination: Path) -> Path:
    """Persist a Streamlit upload to disk for processing."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(upload.read())
    return destination


def render_results(summary: dict) -> None:
    """Render execution summary, downloads and log previews."""
    st.success(
        f"Processing completed in {summary['duration_seconds']} seconds."
    )

    card_1, card_2, card_3, card_4 = st.columns(4)
    with card_1:
        st.metric("Employees Processed", summary["employees_processed"])
    with card_2:
        st.metric("Reports Generated", summary["reports_generated"])
    with card_3:
        st.metric("Missing Members", summary["missing_members"])
    with card_4:
        st.metric("Errors", summary["errors"])

    zip_path = Path(summary["zip_path"])

    if zip_path.exists():
        st.download_button(
            label="Download Employee_Reports.zip",
            data=zip_path.read_bytes(),
            file_name="Employee_Reports.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
    else:
        st.warning("The output bundle for this run is no longer available on disk.")

    if summary["missing_member_logs"]:
        with st.expander(f"Missing Member ID Log ({summary['missing_members']})"):
            st.code("\n".join(summary["missing_member_logs"]))

    if summary["error_logs"]:
        with st.expander(f"Error Log ({summary['errors']})"):
            st.code("\n".join(summary["error_logs"]))


# ----------------------------------------------------------------------
# Page layout
# ----------------------------------------------------------------------
st.title("Payroll Report Generation")
st.caption("Generate employee-wise payroll reports from raw EPFO wage files.")

st.markdown("### Input Files")

master_column, wage_column = st.columns(2)

with master_column:
    master_upload = st.file_uploader(
        "Higher Pension Master",
        type=["xlsx", "xls"],
        help=(
            "Excel workbook containing the sheets "
            "'Approved Application' and 'Rejected Application'."
        ),
    )

with wage_column:
    wage_source = render_input_source(
        label="Raw EPFO Wage Files",
        key="m1_wages",
        upload_types=["xls"],
        help_text=(
            "EPFO wage exports (tab-delimited .xls). "
            "Folder mode reads your local input folder directly (read-only)."
        ),
        folder_file_filter=".xls",
    )

inputs_ready = master_upload is not None and wage_source["ready"]

run_clicked = st.button(
    "Generate Reports",
    type="primary",
    disabled=not inputs_ready,
    use_container_width=True,
)

if run_clicked:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT_DIR / "outputs" / f"run_{run_id}"
    upload_dir = run_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # Persist master upload
    # ------------------------------------------------------------
    master_path = _save_upload(
        master_upload,
        upload_dir / f"master{Path(master_upload.name).suffix}",
    )

    # ------------------------------------------------------------
    # Resolve wage file paths (upload or read-only folder)
    # ------------------------------------------------------------
    wage_paths: List[Path] = []

    if wage_source["mode"] == "upload":
        seen_names = set()
        for upload in wage_source["uploads"]:
            original_name = Path(upload.name).name
            if original_name in seen_names:
                stem = Path(original_name).stem
                suffix = Path(original_name).suffix
                original_name = f"{stem}_{len(seen_names)}{suffix}"
            seen_names.add(original_name)
            wage_paths.append(_save_upload(upload, upload_dir / original_name))
    else:
        wage_paths = [
            item
            for item in sorted(wage_source["folder"].iterdir())
            if item.is_file()
            and not item.name.startswith("~$")
            and item.name.lower().endswith(".xls")
        ]

    # ------------------------------------------------------------
    # History metadata (Module 1 ONLY - no Module 2 variables here)
    # ------------------------------------------------------------
    input_names = [master_upload.name] + [path.name for path in wage_paths]
    module_label = "Module 1 — Payroll Report Generation"

    progress_bar = st.progress(0, text="Initializing run")

    def _update_progress(stage: str, fraction: float) -> None:
        progress_bar.progress(min(max(fraction, 0.0), 1.0), text=stage)

    try:
        summary = wrappers.generate_reports(
            master_file=master_path,
            wage_files=wage_paths,
            run_dir=run_dir,
            progress_callback=_update_progress,
        )
    except ValueError as exc:
        progress_bar.empty()
        if "Worksheet named" in str(exc):
            st.error(
                "Invalid Higher Pension Master. The workbook must contain "
                "the sheets 'Approved Application' and 'Rejected Application'."
            )
        else:
            st.error(f"Invalid input file detected: {exc}")
        page_logger.error("Module 1 ValueError: %s", exc)
        wrappers.record_failure(run_dir.name, module_label, input_names, exc)
    except KeyError as exc:
        progress_bar.empty()
        st.error(
            f"A required column is missing in an input file: {exc}. "
            "Please verify the input file format."
        )
        page_logger.error("Module 1 KeyError: %s", exc)
        wrappers.record_failure(run_dir.name, module_label, input_names, exc)
    except Exception as exc:
        progress_bar.empty()
        st.error(
            "An unexpected error occurred while generating reports. "
            "Technical details have been written to the application log."
        )
        st.code(f"{type(exc).__name__}: {exc}")
        st.caption(
            "Full traceback saved to logs/app.log — "
            "share it with the development team if the issue persists."
        )
        page_logger.exception("Module 1 unexpected error: %s", exc)
        wrappers.record_failure(run_dir.name, module_label, input_names, exc)
    else:
        st.session_state["module_1_result"] = summary
        st.rerun()

# ----------------------------------------------------------------------
# Persisted results from the latest run in this session
# ----------------------------------------------------------------------
if "module_1_result" in st.session_state:
    st.divider()
    st.markdown("### Latest Execution Results")
    render_results(st.session_state["module_1_result"])