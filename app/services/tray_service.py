from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon, QWidget

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TrayMenuState:
    sidebar_visible: bool
    sidebar_collapsed: bool
    always_on_top: bool
    auto_hide_enabled: bool
    launch_at_startup: bool


class TrayService(QObject):
    """System tray integration and context-menu state synchronization."""

    toggle_sidebar_requested = Signal()
    clear_history_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    always_on_top_toggled = Signal(bool)
    auto_hide_toggled = Signal(bool)
    autostart_toggled = Signal(bool)
    reset_panel_requested = Signal()
    open_logs_folder_requested = Signal()
    menu_opening = Signal()

    def __init__(self, parent_widget: QWidget, tooltip: str = "CtrlV") -> None:
        super().__init__(parent_widget)
        self._parent_widget = parent_widget
        self._tooltip = tooltip

        self._tray_icon: QSystemTrayIcon | None = None
        self._menu: QMenu | None = None

        self._toggle_sidebar_action: QAction | None = None
        self._always_on_top_action: QAction | None = None
        self._auto_hide_action: QAction | None = None
        self._clear_history_action: QAction | None = None
        self._settings_action: QAction | None = None
        self._autostart_action: QAction | None = None
        self._reset_panel_action: QAction | None = None
        self._open_logs_action: QAction | None = None
        self._quit_action: QAction | None = None

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def initialize(self) -> bool:
        if not self.is_available():
            return False

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(self._build_icon())
        tray_icon.setToolTip(self._tooltip)
        tray_icon.activated.connect(self._on_tray_activated)

        menu = QMenu(self._parent_widget)
        menu.aboutToShow.connect(self.menu_opening.emit)

        self._toggle_sidebar_action = menu.addAction("Show sidebar")
        self._toggle_sidebar_action.triggered.connect(self.toggle_sidebar_requested.emit)

        self._settings_action = menu.addAction("Settings...")
        self._settings_action.triggered.connect(self.settings_requested.emit)

        menu.addSeparator()

        self._always_on_top_action = menu.addAction("Always on top")
        self._always_on_top_action.setCheckable(True)
        self._always_on_top_action.toggled.connect(self.always_on_top_toggled.emit)

        self._auto_hide_action = menu.addAction("Auto-hide")
        self._auto_hide_action.setCheckable(True)
        self._auto_hide_action.toggled.connect(self.auto_hide_toggled.emit)

        self._autostart_action = menu.addAction("Launch at startup")
        self._autostart_action.setCheckable(True)
        self._autostart_action.toggled.connect(self.autostart_toggled.emit)

        menu.addSeparator()

        self._reset_panel_action = menu.addAction("Reset panel position/state")
        self._reset_panel_action.triggered.connect(self.reset_panel_requested.emit)

        self._open_logs_action = menu.addAction("Open logs folder")
        self._open_logs_action.triggered.connect(self.open_logs_folder_requested.emit)

        self._clear_history_action = menu.addAction("Clear history")
        self._clear_history_action.triggered.connect(self.clear_history_requested.emit)

        menu.addSeparator()

        self._quit_action = menu.addAction("Quit")
        self._quit_action.triggered.connect(self.quit_requested.emit)

        tray_icon.setContextMenu(menu)
        tray_icon.show()

        self._tray_icon = tray_icon
        self._menu = menu
        LOGGER.info("Tray service initialized")
        return True

    def update_menu_state(self, state: TrayMenuState) -> None:
        if self._toggle_sidebar_action is not None:
            should_show = not state.sidebar_visible
            self._toggle_sidebar_action.setText("Show sidebar" if should_show else "Hide sidebar")

        if self._always_on_top_action is not None:
            self._always_on_top_action.blockSignals(True)
            self._always_on_top_action.setChecked(state.always_on_top)
            self._always_on_top_action.blockSignals(False)

        if self._auto_hide_action is not None:
            self._auto_hide_action.blockSignals(True)
            self._auto_hide_action.setChecked(state.auto_hide_enabled)
            self._auto_hide_action.blockSignals(False)

        if self._autostart_action is not None:
            self._autostart_action.blockSignals(True)
            self._autostart_action.setChecked(state.launch_at_startup)
            self._autostart_action.blockSignals(False)

    def show_message(self, title: str, message: str, timeout_ms: int = 2500) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, timeout_ms)

    def shutdown(self) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.hide()
        self._tray_icon.deleteLater()
        self._tray_icon = None
        self._menu = None

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.toggle_sidebar_requested.emit()

    def _build_icon(self) -> QIcon:
        app_style = self._parent_widget.style()
        if app_style is not None:
            standard_icon = app_style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            if not standard_icon.isNull():
                return standard_icon

        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        return QIcon(pixmap)
