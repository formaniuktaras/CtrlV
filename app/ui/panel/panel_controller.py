from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging

from PySide6.QtCore import QObject, Signal

from app.services.settings_service import SettingsService
from app.core.sidebar_types import DockSide, PanelState, RuntimeState
from app.ui.behavior.window_controller import WindowBehaviorController
from app.ui.main_window import MainWindow


class VisibilityState(str, Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"


class PanelMode(str, Enum):
    COLLAPSED = "collapsed"
    EXPANDED = "expanded"


class DockState(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    FLOATING = "floating"


class RuntimeMode(str, Enum):
    IDLE = "idle"
    ANIMATING = "animating"


@dataclass(slots=True)
class PanelSnapshot:
    visibility: VisibilityState
    panel_mode: PanelMode
    dock_state: DockState
    runtime: RuntimeMode


LOGGER = logging.getLogger(__name__)


class PanelController(QObject):
    """Single control layer for panel visibility, docking and expansion state."""

    state_changed = Signal(object)
    visibility_changed = Signal(bool)
    before_hover_expand = Signal()

    def __init__(self, window: MainWindow, settings_service: SettingsService) -> None:
        super().__init__(window)
        self._window = window
        self._behavior = WindowBehaviorController(
            window=window,
            drag_handle=window.drag_handle,
            settings_service=settings_service,
        )

        self._behavior.hover_expand_requested.connect(self._expand_panel_from_hover)
        self._behavior.hover_collapse_requested.connect(self.collapse_panel)

        self._window.visibility_changed.connect(self._on_visibility_changed)

        self._behavior.on_ready()
        self._sync_state()

    @property
    def always_on_top(self) -> bool:
        return self._behavior.always_on_top

    @property
    def auto_hide_enabled(self) -> bool:
        return self._behavior.auto_hide_enabled

    @property
    def dock_side(self) -> DockSide:
        return self._behavior.dock_side

    @property
    def panel_width(self) -> int:
        return self._window.width()

    @property
    def hide_delay_ms(self) -> int:
        return self._behavior.hide_delay_ms

    @property
    def reveal_on_hover_enabled(self) -> bool:
        return self._behavior.reveal_on_hover_enabled

    @property
    def is_visible(self) -> bool:
        return self._window.isVisible()

    @property
    def snapshot(self) -> PanelSnapshot:
        visibility = VisibilityState.VISIBLE if self._window.isVisible() else VisibilityState.HIDDEN

        panel_mode = (
            PanelMode.COLLAPSED if self._behavior.panel_state == PanelState.COLLAPSED else PanelMode.EXPANDED
        )

        if self._behavior.runtime_state == RuntimeState.FLOATING:
            dock_state = DockState.FLOATING
        elif self._behavior.dock_side == DockSide.LEFT:
            dock_state = DockState.LEFT
        else:
            dock_state = DockState.RIGHT

        runtime = (
            RuntimeMode.ANIMATING
            if self._behavior.runtime_state in {RuntimeState.ANIMATING_COLLAPSE, RuntimeState.ANIMATING_EXPAND}
            else RuntimeMode.IDLE
        )

        return PanelSnapshot(
            visibility=visibility,
            panel_mode=panel_mode,
            dock_state=dock_state,
            runtime=runtime,
        )

    def show_panel(self) -> None:
        LOGGER.info("Panel show requested")
        if self.snapshot.dock_state != DockState.FLOATING:
            self._behavior.ensure_docked_geometry(prefer_collapsed=False)

        if not self._window.isVisible():
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()

        if self.snapshot.dock_state == DockState.FLOATING:
            self._sync_state()
            return

        self.restore_docked_position(prefer_collapsed=False)
        self.expand_panel()

    def hide_panel(self) -> None:
        LOGGER.info("Panel hide requested")
        if not self._window.isVisible():
            self._sync_state()
            return
        self._window.hide()
        self._sync_state()

    def toggle_panel(self) -> None:
        LOGGER.info("Panel toggle requested")
        state = self.snapshot

        if state.visibility == VisibilityState.HIDDEN:
            self.show_panel()
            self.expand_panel()
            return

        if state.panel_mode == PanelMode.COLLAPSED:
            self.expand_panel()
            return

        self.hide_panel()

    def expand_panel(self) -> None:
        if not self._window.isVisible():
            self.show_panel()
            return

        if self.snapshot.dock_state != DockState.FLOATING:
            self._behavior.expand_panel()
        self._sync_state()

    def _expand_panel_from_hover(self) -> None:
        self.before_hover_expand.emit()
        self.expand_panel()

    def collapse_panel(self) -> None:
        state = self.snapshot
        if state.visibility == VisibilityState.HIDDEN:
            return
        if state.dock_state == DockState.FLOATING:
            return

        self._behavior.collapse_panel()
        self._sync_state()

    def ensure_visible_and_expanded(self) -> None:
        if self.snapshot.visibility == VisibilityState.HIDDEN:
            self.show_panel()
        self.expand_panel()

    def set_dock(self, side: DockState) -> None:
        if side == DockState.FLOATING:
            self._behavior.set_floating(True)
            self._sync_state()
            return

        self._behavior.set_floating(False)
        self._behavior.set_dock_side(DockSide.LEFT if side == DockState.LEFT else DockSide.RIGHT)
        self.restore_docked_position(prefer_collapsed=False)
        self.expand_panel()

    def set_always_on_top(self, enabled: bool) -> None:
        self._behavior.set_always_on_top(enabled)
        self._sync_state()

    def set_auto_hide_enabled(self, enabled: bool) -> None:
        self._behavior.set_auto_hide_enabled(enabled)
        if not enabled:
            self.expand_panel()
        self._sync_state()

    def set_hide_delay_ms(self, delay_ms: int) -> None:
        self._behavior.set_hide_delay_ms(delay_ms)
        self._sync_state()

    def set_reveal_on_hover_enabled(self, enabled: bool) -> None:
        self._behavior.set_reveal_on_hover_enabled(enabled)
        self._sync_state()

    def set_panel_width(self, width: int) -> None:
        self._behavior.set_panel_width(width)
        self._sync_state()

    def reset_position_state(self) -> None:
        LOGGER.info("Panel reset position/state requested")
        self._behavior.reset_position_state()
        self.expand_panel()
        self._sync_state()

    def shutdown(self) -> None:
        self._behavior.shutdown()

    def restore_docked_position(self, prefer_collapsed: bool) -> None:
        self._behavior.restore_position(prefer_collapsed=prefer_collapsed)
        self._sync_state()

    def _on_visibility_changed(self, visible: bool) -> None:
        if visible:
            if self.snapshot.dock_state != DockState.FLOATING:
                prefer_collapsed = self.snapshot.panel_mode == PanelMode.COLLAPSED
                self._behavior.ensure_docked_geometry(prefer_collapsed=prefer_collapsed)
            self._behavior.start_hover_tracking()
        else:
            self._behavior.stop_hover_tracking()
        self.visibility_changed.emit(visible)
        self._sync_state()

    def _sync_state(self) -> None:
        self.state_changed.emit(self.snapshot)
