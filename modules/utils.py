"""
Shared UI utilities for Payroll Process Automation Suite.

This module contains reusable UI helpers only.
No business logic should be placed here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import streamlit as st

APP_VERSION = "v1.0.0"


def apply_enterprise_theme() -> None:
    """
    Apply the enterprise visual theme.

    The theme uses:
    - White background
    - Navy blue primary color
    - Grey secondary elements
    - Clean corporate typography

    Note:
        The base light theme is enforced via .streamlit/config.toml.
        This function only refines spacing, cards, badges and navigation.
    """
    st.markdown(
        """
        <style>
            :root {
                --ppas-navy: #0F2B52;
                --ppas-dark-navy: #0A1F3D;
                --ppas-grey: #5F6B7A;
                --ppas-light-grey: #F4F6F9;
                --ppas-border: #D8DEE7;
                --ppas-white: #FFFFFF;
                --ppas-success: #1E6F4F;
                --ppas-warning: #8A5A00;
            }

            html, body, [class*="css"] {
                font-family: "Segoe UI", Arial, sans-serif;
            }

            h1, h2, h3, h4, h5, h6 {
                color: var(--ppas-navy);
                font-weight: 650;
            }

            .block-container {
                padding-top: 2.2rem;
                padding-bottom: 2rem;
                max-width: 1300px;
            }

            /* -------------------------------------
               Sidebar shell
            ------------------------------------- */
            section[data-testid="stSidebar"] {
                background-color: #FBFCFE;
                border-right: 1px solid var(--ppas-border);
            }

            /* Sidebar navigation items */
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span {
                color: #26303B !important;
                font-weight: 600;
            }

            /* Active navigation item - navy pill */
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {
                background-color: var(--ppas-navy) !important;
                color: var(--ppas-white) !important;
                border-radius: 8px;
            }

            /* Sidebar footer brand block */
            .ppas-sidebar-footer {
                padding: 4px 6px 8px 6px;
            }

            .ppas-sidebar-title {
                font-size: 0.95rem;
                font-weight: 700;
                color: var(--ppas-navy);
                line-height: 1.35;
            }

            .ppas-sidebar-subtitle {
                font-size: 0.76rem;
                color: var(--ppas-grey);
                margin-top: 4px;
            }

            .ppas-sidebar-meta {
                font-size: 0.68rem;
                color: #8A94A1;
                margin-top: 8px;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }

            /* -------------------------------------
               Metrics (dashboard cards)
            ------------------------------------- */
            .stMetric {
                background-color: var(--ppas-white);
                border: 1px solid var(--ppas-border);
                border-radius: 12px;
                padding: 18px 16px;
                box-shadow: 0 2px 8px rgba(15, 43, 82, 0.04);
            }

            .stMetricLabel {
                color: var(--ppas-grey) !important;
                font-size: 0.85rem !important;
                font-weight: 600;
            }

            .stMetricValue {
                color: var(--ppas-navy) !important;
                font-weight: 750 !important;
            }

            /* -------------------------------------
               Buttons
            ------------------------------------- */
            .stButton > button,
            .stDownloadButton > button,
            .stFormSubmitButton > button {
                background-color: var(--ppas-navy);
                color: var(--ppas-white);
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 0.45rem 1rem;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            .stFormSubmitButton > button:hover {
                background-color: var(--ppas-dark-navy);
                color: var(--ppas-white);
            }

            .stButton > button:disabled,
            .stDownloadButton > button:disabled,
            .stFormSubmitButton > button:disabled {
                background-color: #AEB8C4;
                color: #F7F9FB;
            }

            /* -------------------------------------
               Components
            ------------------------------------- */
            .stAlert {
                border-radius: 10px;
            }

            [data-testid="stFileUploadDropzone"] {
                border-radius: 12px;
                border: 1.5px dashed #B8C2CF;
                background-color: #FBFCFE;
            }

            [data-testid="stDataFrame"] {
                border: 1px solid var(--ppas-border);
                border-radius: 10px;
            }

            .ppas-badge {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                background-color: transparent;
            }

            hr {
                border-top: 1px solid var(--ppas-border);
            }

            header[data-testid="stHeader"] {
                background-color: transparent;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    """
    Render the application identity block as a sidebar footer.

    Design decision:
        st.navigation() pins the page menu to the top of the sidebar.
        The product identity is therefore rendered as a corporate
        footer (name, subtitle, version, usage classification),
        matching internal enterprise tooling conventions.
    """
    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
        <div class="ppas-sidebar-footer">
            <div class="ppas-sidebar-title">
                Payroll Process Automation Suite
            </div>
            <div class="ppas-sidebar-subtitle">
                Enterprise Payroll Automation Platform
            </div>
            <div class="ppas-sidebar-meta">
                {APP_VERSION} &bull; Internal Use Only
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_dashboard_summary() -> Dict[str, Union[int, str]]:
    """
    Return dashboard summary metrics from SQLite execution history.

    Falls back to zero values when no history exists yet.
    """
    from modules import database

    try:
        return database.get_dashboard_stats()
    except Exception:
        return {
            "reports_generated": 0,
            "employees_processed": 0,
            "successful_executions": 0,
            "processing_time_saved": "0 hrs",
        }


def render_status_badge(status: str) -> None:
    """
    Render a small status badge.

    Examples:
        Ready
        In Progress
        Coming Soon
    """
    normalized_status = status.strip().lower()

    color_map = {
        "ready": "#1E6F4F",
        "in progress": "#8A5A00",
        "coming soon": "#444B55",
    }

    color = color_map.get(normalized_status, "#444B55")

    st.markdown(
        f"""
        <span class="ppas-badge" style="border: 1px solid {color}; color: {color};">
            {status}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_module_card(
    title: str,
    description: str,
    status: str,
    page_path: str,
    cta_label: str,
    icon: str = "",
) -> None:
    """
    Render a professional module card.

    Each card represents a functional module of PPAS.
    """
    with st.container(border=True):
        if icon:
            st.markdown(f"#### {icon} {title}")
        else:
            st.markdown(f"#### {title}")

        st.markdown(description)
        render_status_badge(status)

        st.page_link(
            page_path,
            label=cta_label,
            icon="➡️",
            use_container_width=True,
        )


def render_input_source(
    label: str,
    key: str,
    upload_types: Sequence[str],
    help_text: str = "",
    folder_file_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Render an enterprise input-source control.

    Users can provide multi-file inputs either as:
        - Uploads (files / ZIP), or
        - A read-only folder path on the application server.

    Folder mode mirrors the original automation workflow
    (input_files / output_files / Combined_zipped_files).

    Args:
        label:
            Visible control label.
        key:
            Unique Streamlit widget key prefix.
        upload_types:
            Allowed upload extensions (without dot handling by Streamlit).
        help_text:
            Tooltip help text.
        folder_file_filter:
            Optional suffix filter for folder mode, e.g. ".xls".

    Returns:
        Dictionary:
            mode       : "upload" | "folder"
            uploads    : list of UploadedFile | None
            folder     : Path | None (validated, read-only)
            ready      : bool
            file_count : int
    """
    upload_label = "Upload (ZIP / files)"
    folder_label = "Server folder path"

    result: Dict[str, Any] = {
        "mode": None,
        "uploads": None,
        "folder": None,
        "ready": False,
        "file_count": 0,
    }

    selected_mode = st.radio(
        label,
        [upload_label, folder_label],
        horizontal=True,
        help=help_text,
        key=f"{key}_mode",
    )

    if selected_mode == upload_label:
        result["mode"] = "upload"
        result["uploads"] = st.file_uploader(
            "Files",
            type=list(upload_types),
            accept_multiple_files=True,
            label_visibility="collapsed",
            key=f"{key}_upload",
        )
        result["ready"] = bool(result["uploads"])
        result["file_count"] = len(result["uploads"] or [])
        return result

    # ---------------- folder mode (read-only) ----------------
    result["mode"] = "folder"
    path_text = st.text_input(
        "Folder path on this machine",
        placeholder=r"C:\Payroll_Data\folder_name",
        label_visibility="collapsed",
        key=f"{key}_path",
    )

    if path_text and path_text.strip():
        candidate = Path(path_text.strip())

        if candidate.is_dir():
            matching_files = [
                item
                for item in sorted(candidate.iterdir())
                if item.is_file()
                and not item.name.startswith("~$")
                and (
                    folder_file_filter is None
                    or item.name.lower().endswith(folder_file_filter)
                )
            ]
            result["file_count"] = len(matching_files)

            if matching_files:
                result["folder"] = candidate
                result["ready"] = True
                st.caption(
                    f"✅ Detected {len(matching_files)} file(s) "
                    "in the folder (read-only)."
                )
            else:
                st.warning("Folder exists but contains no matching files.")
        else:
            st.warning("Folder not found on this machine.")

    return result