from __future__ import annotations

import logging
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from app.core.clipboard_monitor import ClipboardMonitor
from app.core.clipboard_parser import ClipboardParser
from app.core.history_store import HistoryStore
from app.services.app_lifecycle import AppLifecycleController
from app.services.clipboard_service import ClipboardService
from app.services.settings_service import SettingsService
from app.ui.main_window import MainWindow
from app.version import APP_NAME, VERSION
from app.ui.panel import PanelController
from app.ui.styles import APP_STYLE
from app.utils.logging_config import configure_logging

LOGGER = logging.getLogger(__name__)


def create_application(argv: Sequence[str]) -> QApplication:
    configure_logging()
    LOGGER.info("Starting %s application v%s", APP_NAME, VERSION)

    app = QApplication(list(argv))
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setStyleSheet(APP_STYLE)

    clipboard = app.clipboard()
    parser = ClipboardParser(preview_limit=90, thumbnail_size=48)
    store = HistoryStore(max_items=100)
    service = ClipboardService(clipboard=clipboard)
    monitor = ClipboardMonitor(clipboard=clipboard, parser=parser, store=store)
    settings_service = SettingsService()

    window = MainWindow(
        store=store,
        service=service,
        monitor=monitor,
    )
    panel_controller = PanelController(window=window, settings_service=settings_service)

    tray_settings = settings_service.load_tray_settings()
    panel_controller.set_always_on_top(tray_settings.always_on_top)
    panel_controller.set_auto_hide_enabled(tray_settings.auto_hide_enabled)

    lifecycle = AppLifecycleController(
        app=app,
        window=window,
        panel_controller=panel_controller,
        monitor=monitor,
        settings_service=settings_service,
    )
    app._lifecycle = lifecycle  # type: ignore[attr-defined]

    lifecycle.show_sidebar()

    return app
