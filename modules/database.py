"""
SQLite persistence layer for Payroll Process Automation Suite.

Stores one row per module execution:
    timestamp, module, status, employees processed,
    reports generated, errors, duration, output paths,
    input files and error details.

Also provides aggregate statistics for the Home dashboard.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATABASE_DIR = Path("database")
DATABASE_PATH = DATABASE_DIR / "ppas_history.db"

# Documented estimation constant:
# average manual effort (minutes) saved per employee processed.
MANUAL_MINUTES_PER_EMPLOYEE = 5


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection, creating the database folder if needed."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the execution history table when missing."""
    connection = _connect()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                executed_at TEXT NOT NULL,
                module TEXT NOT NULL,
                status TEXT NOT NULL,
                employees_processed INTEGER DEFAULT 0,
                reports_generated INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                processing_time_seconds REAL DEFAULT 0,
                output_zip_path TEXT,
                extra_output_path TEXT,
                input_files TEXT,
                error_detail TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def record_execution(
    run_id: str,
    module: str,
    status: str,
    employees_processed: int = 0,
    reports_generated: int = 0,
    errors: int = 0,
    processing_time_seconds: float = 0.0,
    output_zip_path: Optional[str] = None,
    extra_output_path: Optional[str] = None,
    input_files: Optional[List[str]] = None,
    error_detail: Optional[str] = None,
) -> None:
    """Persist one execution record (idempotent per run_id)."""
    init_db()
    connection = _connect()
    try:
        connection.execute(
            """
            INSERT OR REPLACE INTO execution_history (
                run_id, executed_at, module, status,
                employees_processed, reports_generated, errors,
                processing_time_seconds, output_zip_path,
                extra_output_path, input_files, error_detail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                module,
                status,
                employees_processed,
                reports_generated,
                errors,
                processing_time_seconds,
                output_zip_path,
                extra_output_path,
                json.dumps(input_files or [], default=str),
                error_detail,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_history(limit: int = 200) -> List[Dict[str, Any]]:
    """Return execution history, newest first."""
    init_db()
    connection = _connect()
    try:
        cursor = connection.execute(
            """
            SELECT * FROM execution_history
            ORDER BY executed_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_dashboard_stats() -> Dict[str, Any]:
    """Aggregate statistics for the Home dashboard cards."""
    init_db()
    connection = _connect()
    try:
        cursor = connection.execute(
            """
            SELECT
                COALESCE(SUM(reports_generated), 0) AS total_reports,
                COALESCE(SUM(employees_processed), 0) AS total_employees,
                COUNT(CASE WHEN status = 'success' THEN 1 END) AS success_count
            FROM execution_history
            """
        )
        row = cursor.fetchone()
    finally:
        connection.close()

    total_employees = int(row["total_employees"])
    saved_minutes = total_employees * MANUAL_MINUTES_PER_EMPLOYEE
    saved_hours = saved_minutes / 60.0

    if saved_hours >= 1:
        time_saved_label = f"{saved_hours:,.1f} hrs"
    else:
        time_saved_label = f"{saved_minutes:,.0f} min"

    return {
        "reports_generated": int(row["total_reports"]),
        "employees_processed": total_employees,
        "successful_executions": int(row["success_count"]),
        "processing_time_saved": time_saved_label,
    }