"""
Page: Execution History.

Displays the SQLite execution history and allows re-downloading
previous output bundles.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules import database
from modules.utils import render_status_badge

st.title("Execution History")
st.caption("Audit trail of all module executions with downloadable outputs.")

history = database.get_history(limit=200)

if not history:
    st.info("No executions recorded yet. Run Module 1 or Module 2 to populate the history.")
    st.stop()

# ----------------------------------------------------------------------
# Overview table
# ----------------------------------------------------------------------
table_rows = []
for entry in history:
    try:
        inputs = json.loads(entry["input_files"] or "[]")
    except json.JSONDecodeError:
        inputs = []

    table_rows.append(
        {
            "Date": entry["executed_at"],
            "Module": entry["module"],
            "Status": entry["status"].title(),
            "Employees Processed": entry["employees_processed"],
            "Reports": entry["reports_generated"],
            "Errors": entry["errors"],
            "Processing Time": f"{entry['processing_time_seconds']}s",
            "Inputs": ", ".join(inputs[:3]) + ("…" if len(inputs) > 3 else ""),
            "Error Detail": entry["error_detail"] or "",
        }
    )

st.dataframe(
    pd.DataFrame(table_rows),
    use_container_width=True,
    hide_index=True,
)

# ----------------------------------------------------------------------
# Re-download previous outputs
# ----------------------------------------------------------------------
st.markdown("### Download Previous Outputs")

downloadable = [
    entry
    for entry in history
    if entry["output_zip_path"] and Path(entry["output_zip_path"]).exists()
][:10]

if not downloadable:
    st.caption("No downloadable output bundles available on disk.")

for entry in downloadable:
    zip_path = Path(entry["output_zip_path"])

    with st.container(border=True):
        col_info, col_meta, col_action = st.columns([3, 3, 2])

        with col_info:
            st.markdown(f"**{entry['module']}**")
            st.caption(entry["executed_at"])

        with col_meta:
            st.caption(
                f"Status: {entry['status']}  •  "
                f"{entry['employees_processed']} employees  •  "
                f"{entry['processing_time_seconds']}s"
            )
            if entry["extra_output_path"] and Path(entry["extra_output_path"]).exists():
                st.caption("Includes Difference Report")

        with col_action:
            st.download_button(
                label=f"Download {zip_path.name}",
                data=zip_path.read_bytes(),
                file_name=zip_path.name,
                mime="application/zip",
                key=f"download_{entry['run_id']}",
                use_container_width=True,
            )