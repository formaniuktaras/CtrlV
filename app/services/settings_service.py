from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from app.ui.behavior.types import DockSide, PanelState


@dataclass(slots=True)
class SidebarSettings:
    width: int = 420
    height: int = 640
    expanded_x: int = 0
    expanded_y: int = 120
    dock_side: DockSide = DockSide.RIGHT
    panel_state: PanelState = PanelState.EXPANDED
    visible_edge_px: int = 8
    auto_hide_enabled: bool = True
    always_on_top: bool = True
    reveal_trigger_px: int = 3
    reveal_vertical_tolerance_px: int = 80


@dataclass(slots=True)
class TraySettings:
    close_to_tray_enabled: bool = True
    tray_click_action: str = "toggle_sidebar"
    always_on_top: bool = True
    auto_hide_enabled: bool = True


class SettingsService:
    """Application settings wrapper used by runtime controllers."""

    def __init__(self) -> None:
        self._settings = QSettings()

    def load_sidebar_settings(self) -> SidebarSettings:
        raw_dock = str(self._settings.value("sidebar/dock_side", DockSide.RIGHT.value))
        raw_panel = str(self._settings.value("sidebar/panel_state", PanelState.EXPANDED.value))

        dock_side = DockSide.LEFT if raw_dock == DockSide.LEFT.value else DockSide.RIGHT
        panel_state = PanelState.COLLAPSED if raw_panel == PanelState.COLLAPSED.value else PanelState.EXPANDED

        return SidebarSettings(
            width=self._int("sidebar/width", 420),
            height=self._int("sidebar/height", 640),
            expanded_x=self._int("sidebar/expanded_x", 0),
            expanded_y=self._int("sidebar/expanded_y", 120),
            dock_side=dock_side,
            panel_state=panel_state,
            visible_edge_px=max(1, self._int("sidebar/visible_edge_px", 8)),
            auto_hide_enabled=self._bool("sidebar/auto_hide_enabled", True),
            always_on_top=self._bool("sidebar/always_on_top", True),
            reveal_trigger_px=max(1, self._int("sidebar/reveal_trigger_px", 3)),
            reveal_vertical_tolerance_px=max(0, self._int("sidebar/reveal_vertical_tolerance_px", 80)),
        )

    def save_sidebar_settings(self, state: SidebarSettings) -> None:
        self._settings.setValue("sidebar/width", state.width)
        self._settings.setValue("sidebar/height", state.height)
        self._settings.setValue("sidebar/expanded_x", state.expanded_x)
        self._settings.setValue("sidebar/expanded_y", state.expanded_y)
        self._settings.setValue("sidebar/dock_side", state.dock_side.value)
        self._settings.setValue("sidebar/panel_state", state.panel_state.value)
        self._settings.setValue("sidebar/visible_edge_px", state.visible_edge_px)
        self._settings.setValue("sidebar/auto_hide_enabled", state.auto_hide_enabled)
        self._settings.setValue("sidebar/always_on_top", state.always_on_top)
        self._settings.setValue("sidebar/reveal_trigger_px", state.reveal_trigger_px)
        self._settings.setValue("sidebar/reveal_vertical_tolerance_px", state.reveal_vertical_tolerance_px)
        self._settings.sync()

    def load_tray_settings(self) -> TraySettings:
        return TraySettings(
            close_to_tray_enabled=self._bool("tray/close_to_tray_enabled", True),
            tray_click_action=str(self._settings.value("tray/tray_click_action", "toggle_sidebar")),
            always_on_top=self._bool("sidebar/always_on_top", True),
            auto_hide_enabled=self._bool("sidebar/auto_hide_enabled", True),
        )

    def save_tray_settings(self, state: TraySettings) -> None:
        self._settings.setValue("tray/close_to_tray_enabled", state.close_to_tray_enabled)
        self._settings.setValue("tray/tray_click_action", state.tray_click_action)
        self._settings.setValue("sidebar/always_on_top", state.always_on_top)
        self._settings.setValue("sidebar/auto_hide_enabled", state.auto_hide_enabled)
        self._settings.sync()

    def is_first_run(self) -> bool:
        return not self._bool("app/first_run_completed", False)

    def mark_first_run_completed(self) -> None:
        self._settings.setValue("app/first_run_completed", True)
        self._settings.sync()

    def flush(self) -> None:
        self._settings.sync()

    def _int(self, key: str, default: int) -> int:
        value = self._settings.value(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _bool(self, key: str, default: bool) -> bool:
        value = self._settings.value(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)
