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
    """UI-level mediator for reading/applying user settings."""

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

    def load_state(self) -> SettingsViewState:
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

    def apply_state(self, state: SettingsViewState) -> bool:
        try:
            self._set_autostart(state.launch_at_startup)
        except AutostartError as exc:
            LOGGER.exception("Failed to update autostart state")
            self.save_failed.emit(str(exc))
            return False

        self._settings_service.save_start_minimized_to_tray(state.start_minimized_to_tray)

        self._panel_controller.set_always_on_top(state.always_on_top)
        self._panel_controller.set_auto_hide_enabled(state.auto_hide_sidebar)
        self._panel_controller.set_reveal_on_hover_enabled(state.reveal_on_hover)
        self._panel_controller.set_hide_delay_ms(state.hide_delay_ms)
        self._panel_controller.set_dock(
            side=(DockState.LEFT if state.dock_side == DockSide.LEFT else DockState.RIGHT)
        )
        self._panel_controller.set_panel_width(state.panel_width)

        self.state_changed.emit(self.load_state())
        return True

    def reset_panel_state(self) -> SettingsViewState:
        self._panel_controller.reset_position_state()
        state = self.load_state()
        self.state_changed.emit(state)
        return state

    def _set_autostart(self, enabled: bool) -> None:
        if enabled:
            self._autostart_service.enable()
            return
        self._autostart_service.disable()
