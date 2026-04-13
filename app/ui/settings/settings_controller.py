from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices

from app.core.sidebar_types import DockSide
from app.services.autostart_service import AutostartError, AutostartService
from app.services.settings_service import SettingsService
from app.ui.panel import DockState, PanelController, PanelMode, VisibilityState
from app.utils.log_paths import get_logs_dir

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SettingsViewState:
    launch_at_startup: bool
    start_minimized_to_tray: bool
    always_on_top: bool
    auto_hide_sidebar: bool
    reveal_on_hover: bool
    hide_delay_ms: int
    dock_side: DockSide
    panel_width: int
    panel_visible: bool
    panel_collapsed: bool


class SettingsController(QObject):
    """Single settings integration point between UI and runtime services."""

    state_changed = Signal(object)
    save_failed = Signal(str)

    def __init__(
        self,
        settings_service: SettingsService,
        panel_controller: PanelController,
        autostart_service: AutostartService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._panel_controller = panel_controller
        self._autostart_service = autostart_service

    def get_current_settings(self) -> SettingsViewState:
        sidebar = self._settings_service.load_sidebar_settings()
        snapshot = self._panel_controller.snapshot
        return SettingsViewState(
            launch_at_startup=self._autostart_service.is_enabled(),
            start_minimized_to_tray=self._settings_service.load_start_minimized_to_tray(),
            always_on_top=sidebar.always_on_top,
            auto_hide_sidebar=sidebar.auto_hide_enabled,
            reveal_on_hover=sidebar.reveal_on_hover_enabled,
            hide_delay_ms=sidebar.hide_delay_ms,
            dock_side=sidebar.dock_side,
            panel_width=sidebar.width,
            panel_visible=snapshot.visibility == VisibilityState.VISIBLE,
            panel_collapsed=snapshot.panel_mode == PanelMode.COLLAPSED,
        )

    def set_autostart(self, enabled: bool) -> bool:
        try:
            if enabled:
                self._autostart_service.enable()
            else:
                self._autostart_service.disable()
        except AutostartError as exc:
            LOGGER.exception("Failed to update autostart state")
            self.save_failed.emit(str(exc))
            self._emit_state()
            return False

        LOGGER.info("Launch at startup changed: %s", enabled)
        self._emit_state()
        return True

    def set_start_minimized_to_tray(self, enabled: bool) -> None:
        LOGGER.info("Start minimized to tray changed: %s", enabled)
        self._settings_service.save_start_minimized_to_tray(enabled)
        self._emit_state()

    def set_always_on_top(self, enabled: bool) -> None:
        LOGGER.info("Always-on-top changed: %s", enabled)
        self._panel_controller.set_always_on_top(enabled)
        self._emit_state()

    def set_auto_hide(self, enabled: bool) -> None:
        LOGGER.info("Auto-hide changed: %s", enabled)
        self._panel_controller.set_auto_hide_enabled(enabled)
        self._emit_state()

    def set_reveal_on_hover(self, enabled: bool) -> None:
        LOGGER.info("Reveal on hover changed: %s", enabled)
        self._panel_controller.set_reveal_on_hover_enabled(enabled)
        self._emit_state()

    def set_hide_delay_ms(self, delay_ms: int) -> None:
        self._panel_controller.set_hide_delay_ms(delay_ms)
        self._emit_state()

    def set_dock_side(self, side: DockSide) -> None:
        mapped = DockState.LEFT if side == DockSide.LEFT else DockState.RIGHT
        self._panel_controller.set_dock(side=mapped)
        self._emit_state()

    def set_panel_width(self, width: int) -> None:
        self._panel_controller.set_panel_width(width)
        self._emit_state()

    def reset_panel_position_state(self) -> SettingsViewState:
        LOGGER.info("Recovery action: reset panel position/state")
        self._panel_controller.reset_position_state()
        self._panel_controller.ensure_visible_and_expanded()
        return self._emit_state()

    def open_logs_folder(self) -> bool:
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_dir)))
        if opened:
            LOGGER.info("Recovery action: open logs folder (%s)", logs_dir)
        else:
            LOGGER.warning("Failed to open logs folder: %s", logs_dir)
            self.save_failed.emit("Failed to open logs folder.")
        return opened

    def _emit_state(self) -> SettingsViewState:
        state = self.get_current_settings()
        self.state_changed.emit(state)
        return state
