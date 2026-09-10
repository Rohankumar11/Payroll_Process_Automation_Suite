"""
Orchestration wrappers for Payroll Process Automation Suite.

Responsibilities:
    - Run folder management
    - Module execution orchestration
    - ZIP bundling
    - Difference report generation
    - Run manifests
    - SQLite execution history recording

No business logic lives in this layer.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import pandas as pd

from modules import database
from modules import module_1
from modules import module_2_processing
from modules import module_2_validation
from modules.logger import get_logger

ProgressCallback = Optional[Callable[[str, float], None]]

MODULE_1_LABEL = "Module 1 — Payroll Report Generation"
MODULE_2_LABEL = "Module 2 — Payroll Validation & Reconciliation"

logger = get_logger("ppas.wrappers", "app.log")


# ----------------------------------------------------------------------
# ZIP helpers
# ----------------------------------------------------------------------
def _zip_run_outputs(run_dir: Path, zip_name: str) -> Path:
    """Bundle Module 1 outputs (reports + logs) into one ZIP."""
    zip_path = run_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(run_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.name == zip_name:
                continue
            if file_path.suffix == ".json":
                continue
            if "uploads" in file_path.parts:
                continue
            archive.write(file_path, file_path.relative_to(run_dir))
    return zip_path


def _zip_selected(
    run_dir: Path,
    zip_name: str,
    include_dirs: Sequence[str],
    include_files: Sequence[Path],
) -> Path:
    """Bundle selected run folders/files into one ZIP."""
    zip_path = run_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for dir_name in include_dirs:
            base = run_dir / dir_name
            if not base.exists():
                continue
            for file_path in sorted(base.rglob("*")):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(run_dir))
        for file_path in include_files:
            if Path(file_path).exists():
                archive.write(file_path, Path(file_path).name)
    return zip_path


def _write_manifest(run_dir: Path, summary: Dict[str, Any]) -> None:
    """Persist machine-readable run manifest."""
    with open(run_dir / "run_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=4, default=str)


# ----------------------------------------------------------------------
# History helpers
# ----------------------------------------------------------------------
def record_failure(
    run_id: str,
    module: str,
    input_files: List[str],
    exc: Exception,
) -> None:
    """Record a failed execution with exception identity."""
    database.record_execution(
        run_id=run_id,
        module=module,
        status="failed",
        input_files=input_files,
        error_detail=f"{type(exc).__name__}: {exc}",
    )


# ----------------------------------------------------------------------
# Module 1
# ----------------------------------------------------------------------
def generate_reports(
    master_file: Path,
    wage_files: Sequence[Path],
    run_dir: Path,
    progress_callback: ProgressCallback = None,
) -> Dict[str, Any]:
    """Orchestrate a full Module 1 execution."""
    run_dir = Path(run_dir)

    logger.info("Module 1 run started: %s", run_dir.name)

    summary = module_1.generate_reports(
        master_file=master_file,
        wage_files=wage_files,
        output_folder=run_dir / "employee_reports",
        log_folder=run_dir / "logs",
        progress_callback=progress_callback,
    )

    if progress_callback:
        progress_callback("Creating ZIP Bundle", 0.96)

    zip_path = _zip_run_outputs(run_dir, "Employee_Reports.zip")
    summary["zip_path"] = str(zip_path)
    summary["run_dir"] = str(run_dir)

    _write_manifest(run_dir, summary)

    database.record_execution(
        run_id=run_dir.name,
        module=MODULE_1_LABEL,
        status="success",
        employees_processed=summary["employees_processed"],
        reports_generated=summary["reports_generated"],
        errors=summary["errors"],
        processing_time_seconds=summary["duration_seconds"],
        output_zip_path=summary["zip_path"],
        input_files=[Path(master_file).name]
        + [Path(wage_file).name for wage_file in wage_files],
    )

    if progress_callback:
        progress_callback("Completed", 1.0)

    logger.info(
        "Module 1 run completed: %s employee(s), %s report(s)",
        summary["employees_processed"],
        summary["reports_generated"],
    )
    return summary


# ----------------------------------------------------------------------
# Module 2 (single user-facing module, two internal stages)
# ----------------------------------------------------------------------
def run_module_2(
    master_file: Path,
    arrear_1214_file: Path,
    arrear_1819_file: Path,
    reports_folder: Path,
    combined_folder: Path,
    run_dir: Path,
    progress_callback: ProgressCallback = None,
    employee_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Orchestrate Module 2 as ONE seamless workflow.

    Internally executes Stage 1 (processing) and Stage 2 (validation)
    on an audit copy. Users never see the two-stage split.
    """
    started_at = pd.Timestamp.now()
    run_dir = Path(run_dir)
    log_folder = run_dir / "logs"
    processed_folder = run_dir / "processed"
    final_folder = run_dir / "validated"

    logger.info("Module 2 run started: %s", run_dir.name)

    def _stage1_callback(stage: str, fraction: float) -> None:
        if progress_callback:
            progress_callback(stage, 0.02 + 0.58 * fraction)

    def _stage2_callback(stage: str, fraction: float) -> None:
        if progress_callback:
            progress_callback(stage, 0.62 + 0.28 * fraction)

    # ---------------- Stage 1 ----------------
    stage1 = module_2_processing.process_reports(
        master_file=master_file,
        arrear_1214_file=arrear_1214_file,
        arrear_1819_file=arrear_1819_file,
        reports_folder=reports_folder,
        combined_folder=combined_folder,
        output_folder=processed_folder,
        log_folder=log_folder,
        progress_callback=_stage1_callback,
        employee_limit=employee_limit,
    )

    # ---------------- audit copy for Stage 2 ----------------
    if progress_callback:
        progress_callback("Preparing Validation Workspace", 0.61)

    if final_folder.exists():
        shutil.rmtree(final_folder)
    shutil.copytree(processed_folder, final_folder)

    # ---------------- Stage 2 ----------------
    stage2 = module_2_validation.validate_reports(
        processed_folder=final_folder,
        log_folder=log_folder,
        progress_callback=_stage2_callback,
    )

    # ---------------- Difference Report ----------------
    if progress_callback:
        progress_callback("Generating Summary", 0.92)

    difference_path = run_dir / "Difference_Report.xlsx"
    pd.DataFrame(stage2["files"]).to_excel(difference_path, index=False)

    # ---------------- ZIP bundle ----------------
    if progress_callback:
        progress_callback("Creating ZIP Bundle", 0.96)

    zip_path = _zip_selected(
        run_dir,
        "Validated_Reports.zip",
        include_dirs=["validated", "logs"],
        include_files=[difference_path],
    )

    duration = (pd.Timestamp.now() - started_at).total_seconds()

    difference_found = sum(
        1
        for row in stage2["files"]
        if row.get("Status") == "Validated"
        and round(row.get("Difference", 0.0), 2) != 0
    )

    summary: Dict[str, Any] = {
        "module": MODULE_2_LABEL,
        "status": "success",
        "reports_processed": len(stage1["completed"]),
        "reports_validated": stage2["validated"],
        "reports_corrected": stage2["corrected"],
        "difference_found": difference_found,
        "failed_stage1": stage1["failed"],
        "files": stage2["files"],
        "processing_time_seconds": round(duration, 2),
        "zip_path": str(zip_path),
        "difference_report_path": str(difference_path),
        "run_dir": str(run_dir),
    }

    _write_manifest(run_dir, summary)

    database.record_execution(
        run_id=run_dir.name,
        module=MODULE_2_LABEL,
        status="success",
        employees_processed=summary["reports_processed"],
        reports_generated=summary["reports_validated"],
        errors=len(stage1["failed"]) + stage2["errors"],
        processing_time_seconds=summary["processing_time_seconds"],
        output_zip_path=summary["zip_path"],
        extra_output_path=str(difference_path),
        input_files=[
            Path(master_file).name,
            Path(arrear_1214_file).name,
            Path(arrear_1819_file).name,
            str(combined_folder),
            str(reports_folder),
        ],
    )

    if progress_callback:
        progress_callback("Completed", 1.0)

    logger.info(
        "Module 2 run completed: %s validated, %s corrected",
        stage2["validated"],
        stage2["corrected"],
    )
    return summary