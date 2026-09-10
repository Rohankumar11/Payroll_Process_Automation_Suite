"""
Logging utilities for Payroll Process Automation Suite.

This module provides a standardized logger for application events,
module execution, warnings, and errors.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_FORMAT = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"


def get_logger(
    name: str,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Return a configured application logger.

    Args:
        name:
            Logger name, usually the module or page name.
        log_file:
            Optional log filename to store inside the logs folder.

    Returns:
        Configured Python logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file:
            file_handler = logging.FileHandler(
                LOG_DIR / log_file,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger