from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths


APP_LOG_FILE_NAME = "ctrlv.log"


def get_app_data_dir() -> Path:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not base_dir:
        base_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base_dir)


def get_logs_dir() -> Path:
    return get_app_data_dir() / "logs"


def get_log_file_path() -> Path:
    return get_logs_dir() / APP_LOG_FILE_NAME
