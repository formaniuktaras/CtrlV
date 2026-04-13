from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from app.utils.log_paths import get_log_file_path, get_logs_dir

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_ctrlv_logging_configured", False):
        return

    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = get_log_file_path()

    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT)

    rotating_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=1_500_000,
        backupCount=5,
        encoding="utf-8",
    )
    rotating_handler.setLevel(level)
    rotating_handler.setFormatter(formatter)
    root_logger.addHandler(rotating_handler)

    if _should_enable_console_logging():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    root_logger._ctrlv_logging_configured = True  # type: ignore[attr-defined]
    root_logger.info("Logging initialized. File: %s", log_file)


def _should_enable_console_logging() -> bool:
    return bool(os.environ.get("CTRLV_CONSOLE_LOG")) or (hasattr(sys, "ps1") and sys.stdout is not None)
