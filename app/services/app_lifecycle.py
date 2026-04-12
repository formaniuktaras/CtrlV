from __future__ import annotations

import logging

from PySide6.QtCore import QObject
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from app.core.clipboard_monitor import ClipboardMonitor
from app.services.settings_service import SettingsService
from app.services.tray_service import TrayMenuState, TrayService
from app.ui.main_window import MainWindow
from app.ui.panel import PanelController

LOGGER = logging.getLogger(__name__)


class AppLifecycleController(QObject):
    """Coordinates application lifecycle, tray integration and shutdown flow."""

    def __init__(
        self,
        app: QApplication,
        window: MainWindow,
        panel_controller: PanelController,
        monitor: ClipboardMonitor,
        settings_service: SettingsService,
    ) -> None:
        super().__init__(window)
        self._app = app
        self._window = window
        self._panel_controller = panel_controller
        self._monitor = monitor
        self._settings_service = settings_service

        self._tray_settings = self._settings_service.load_tray_settings()
        self._tray_service = TrayService(parent_widget=self._window)
        self._tray_enabled = self._tray_service.initialize()
        self._quitting = False

        self._wire_window_signals()
        self._wire_tray_signals()

        self._app.setQuitOnLastWindowClosed(not self._tray_enabled)

        if self._tray_enabled:
            self._sync_tray_menu()
        else:
            LOGGER.warning("System tray is unavailable. Running without tray integration.")

    def show_sidebar(self) -> None:
        self._panel_controller.show_panel()
        self._sync_tray_menu()

    def hide_sidebar(self) -> None:
        self._panel_controller.hide_panel()
        self._sync_tray_menu()

    def toggle_sidebar(self) -> None:
        self._panel_controller.toggle_panel()
        self._sync_tray_menu()

    def quit_application(self) -> None:
        if self._quitting:
            return

        self._quitting = True
        LOGGER.info("Quit requested. Shutting down services.")

        self._panel_controller.shutdown()
        self._window.shutdown()
        self._monitor.shutdown()
        self._settings_service.save_tray_settings(self._tray_settings)
        self._tray_service.shutdown()

        self._app.quit()

    def _wire_window_signals(self) -> None:
        self._window.close_requested.connect(self._on_window_close_requested)
        self._panel_controller.visibility_changed.connect(lambda _: self._sync_tray_menu())

    def _wire_tray_signals(self) -> None:
        self._tray_service.toggle_sidebar_requested.connect(self.toggle_sidebar)
        self._tray_service.clear_history_requested.connect(self._window.clear_history)
        self._tray_service.quit_requested.connect(self.quit_application)
        self._tray_service.always_on_top_toggled.connect(self._on_always_on_top_toggled)
        self._tray_service.auto_hide_toggled.connect(self._on_auto_hide_toggled)

    def _on_window_close_requested(self, event: object) -> None:
        close_event = event if isinstance(event, QCloseEvent) else None
        if close_event is None:
            return

        if self._quitting:
            close_event.accept()
            return

        if not self._tray_enabled or not self._tray_settings.close_to_tray_enabled:
            close_event.accept()
            self.quit_application()
            return

        close_event.ignore()
        self.hide_sidebar()

    def _on_always_on_top_toggled(self, enabled: bool) -> None:
        self._panel_controller.set_always_on_top(enabled)
        self._tray_settings.always_on_top = enabled
        self._settings_service.save_tray_settings(self._tray_settings)
        self._sync_tray_menu()

    def _on_auto_hide_toggled(self, enabled: bool) -> None:
        self._panel_controller.set_auto_hide_enabled(enabled)
        self._tray_settings.auto_hide_enabled = enabled
        self._settings_service.save_tray_settings(self._tray_settings)
        self._sync_tray_menu()

    def _sync_tray_menu(self) -> None:
        if not self._tray_enabled:
            return

        self._tray_service.update_menu_state(
            TrayMenuState(
                sidebar_visible=self._panel_controller.is_visible,
                always_on_top=self._panel_controller.always_on_top,
                auto_hide_enabled=self._panel_controller.auto_hide_enabled,
            )
        )
