from __future__ import annotations

import logging
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from app.core.clipboard_monitor import ClipboardMonitor
from app.core.clipboard_parser import ClipboardParser
from app.core.history_store import HistoryStore
from app.services.clipboard_service import ClipboardService
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLE
from app.utils.logging_config import configure_logging

LOGGER = logging.getLogger(__name__)


def create_application(argv: Sequence[str]) -> QApplication:
    configure_logging()
    LOGGER.info("Starting CtrlV application")

    app = QApplication(list(argv))
    app.setApplicationName("CtrlV")
    app.setOrganizationName("CtrlV")
    app.setStyleSheet(APP_STYLE)

    clipboard = app.clipboard()
    parser = ClipboardParser(preview_limit=90, thumbnail_size=48)
    store = HistoryStore(max_items=100)
    service = ClipboardService(clipboard=clipboard)
    monitor = ClipboardMonitor(clipboard=clipboard, parser=parser, store=store)

    window = MainWindow(
        store=store,
        service=service,
        monitor=monitor,
    )
    window.show()

    return app
