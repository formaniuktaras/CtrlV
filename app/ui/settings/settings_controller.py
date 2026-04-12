from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from app.core.sidebar_types import DockSide
from app.services.autostart_service import AutostartError, AutostartService
from app.services.settings_service import SettingsService
from app.ui.panel import DockState, PanelController

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
        return SettingsViewState(
            launch_at_startup=self._autostart_service.is_enabled(),
            start_minimized_to_tray=self._settings_service.load_start_minimized_to_tray(),
            always_on_top=sidebar.always_on_top,
            auto_hide_sidebar=sidebar.auto_hide_enabled,
            reveal_on_hover=sidebar.reveal_on_hover_enabled,
            hide_delay_ms=sidebar.hide_delay_ms,
            dock_side=sidebar.dock_side,
            panel_width=sidebar.width,
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

        self._emit_state()
        return True

    def set_start_minimized_to_tray(self, enabled: bool) -> None:
        self._settings_service.save_start_minimized_to_tray(enabled)
        self._emit_state()

    def set_always_on_top(self, enabled: bool) -> None:
        self._panel_controller.set_always_on_top(enabled)
        self._emit_state()

    def set_auto_hide(self, enabled: bool) -> None:
        self._panel_controller.set_auto_hide_enabled(enabled)
        self._emit_state()

    def set_reveal_on_hover(self, enabled: bool) -> None:
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

    def reset_window_state(self) -> SettingsViewState:
        self._panel_controller.reset_position_state()
        return self._emit_state()

    def _emit_state(self) -> SettingsViewState:
        state = self.get_current_settings()
        self.state_changed.emit(state)
        return state
