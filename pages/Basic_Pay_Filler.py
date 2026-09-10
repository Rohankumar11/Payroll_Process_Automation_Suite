"""
Page: Basic Pay Filler (OPR utility).

Uploads the basic-pay matrix and the OPR wages workbook, fills the
Basic column, and presents results with downloads
(updated XLSX, Not_Found_Data.txt, combined ZIP).
"""

from __future__ import annotations

import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules import basic_pay_filler, database
from modules.logger import get_logger

page_logger = get_logger("ppas.page.basic_pay", "app.log")

MODULE_LABEL = "Utility — Basic Pay Filler"

st.title("Basic Pay Filler")
st.caption("Fill the Basic column of OPR wages from the basic-pay matrix.")

st.markdown("### Input Files")

left_col, right_col = st.columns(2)

with left_col:
    basic_upload = st.file_uploader(
        "Basic_OPR.xlsx (basic pay matrix)",
        type=["xlsx"],
        help="All sheets are read automatically; month columns detected dynamically.",
    )

with right_col:
    wages_upload = st.file_uploader(
        "Copy of OPR Wages updated.xlsx",
        type=["xlsx"],
        help="Wages detail workbook; the Basic column (J) will be filled.",
    )

run_clicked = st.button(
    "Fill Basic Pay",
    type="primary",
    disabled=not (basic_upload is not None and wages_upload is not None),
    use_container_width=True,
)

if run_clicked:
    run_id = f"basic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    input_names = [basic_upload.name, wages_upload.name]
    started_at = datetime.now()

    try:
        with st.spinner("Building basic matrix, filling wages, generating report…"):
            result = basic_pay_filler.fill_basic_pay(
                basic_upload.read(), wages_upload.read()
            )
    except Exception as exc:
        st.error("An unexpected error occurred while filling basic pay.")
        st.code(f"{type(exc).__name__}: {exc}")
        page_logger.exception("Basic Pay Filler error: %s", exc)
        database.record_execution(
            run_id=run_id,
            module=MODULE_LABEL,
            status="failed",
            input_files=input_names,
            error_detail=f"{type(exc).__name__}: {exc}",
        )
    else:
        result["duration_seconds"] = round(
            (datetime.now() - started_at).total_seconds(), 2
        )
        result["input_names"] = input_names
        database.record_execution(
            run_id=run_id,
            module=MODULE_LABEL,
            status="success",
            reports_generated=result["filled"],
            errors=result["missed"],
            processing_time_seconds=result["duration_seconds"],
            input_files=input_names,
        )
        st.session_state["basic_pay_result"] = result
        st.rerun()

# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------
if "basic_pay_result" in st.session_state:
    result = st.session_state["basic_pay_result"]

    st.divider()
    st.markdown("### Results")

    st.success(
        f"Completed in {result.get('duration_seconds', 0)} seconds "
        f"(matrix range {result['range_label']})."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Rows Filled", result["filled"])
    with c2:
        st.metric("Rows Not Found", result["missed"])
    with c3:
        st.metric("Total Rows Processed", result["total"])
    with c4:
        st.metric("Members With Missing", len(result["member_summary"]))

    # ---------------- downloads ----------------
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("OPR_Wages_Basic_Filled.xlsx", result["workbook"])
        archive.writestr("Not_Found_Data.txt", result["report"])

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Download Updated Wages.xlsx",
            data=result["workbook"],
            file_name="OPR_Wages_Basic_Filled.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Download Not_Found_Data.txt",
            data=result["report"].encode("utf-8"),
            file_name="Not_Found_Data.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )
    with d3:
        st.download_button(
            "Download ZIP (both)",
            data=zip_buffer.getvalue(),
            file_name="Basic_Pay_Output.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )

    # ---------------- member summary ----------------
    if result["member_summary"]:
        st.markdown("### Member Summary (missing data)")
        st.dataframe(
            pd.DataFrame(result["member_summary"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No missing data — every wages row was filled.")

    if result["row_details"]:
        with st.expander(f"Row Details ({len(result['row_details'])})"):
            st.dataframe(
                pd.DataFrame(result["row_details"]),
                use_container_width=True,
                hide_index=True,
            )