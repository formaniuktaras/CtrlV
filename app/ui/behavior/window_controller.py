from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from typing import TYPE_CHECKING

from app.core.sidebar_types import DockSide, PanelState, RuntimeState
from app.ui.behavior.animation import AnimationController
from app.ui.behavior.edge_dock import EdgeDockController


if TYPE_CHECKING:
    from app.services.settings_service import SettingsService


class WindowBehaviorController(QObject):
    """Configures sidebar window mode and delegates runtime behavior to controllers."""

    hover_expand_requested = Signal()
    hover_collapse_requested = Signal()

    def __init__(self, window: QWidget, drag_handle: QWidget, settings_service: SettingsService) -> None:
        super().__init__(window)
        self._window = window
        self._drag_handle = drag_handle
        self._settings_service = settings_service

        self._settings = self._settings_service.load_sidebar_settings()

        self._animation = AnimationController(window)
        self._dock = EdgeDockController(window=window, animation=self._animation)
        self._dock.apply_settings(self._settings)
        self._dock.settings_changed.connect(self._persist_sidebar_settings)
        self._dock.expand_requested.connect(self.hover_expand_requested.emit)
        self._dock.collapse_requested.connect(self.hover_collapse_requested.emit)

        self._dragging = False
        self._drag_offset = QPoint()

        self._resize_save_timer = QTimer(self)
        self._resize_save_timer.setSingleShot(True)
        self._resize_save_timer.setInterval(150)
        self._resize_save_timer.timeout.connect(self._persist_sidebar_settings)

        self._configure_window_flags()
        self._apply_initial_geometry()

        self._drag_handle.installEventFilter(self)
        self._window.installEventFilter(self)

    @property
    def always_on_top(self) -> bool:
        return self._settings.always_on_top

    @property
    def auto_hide_enabled(self) -> bool:
        return self._dock.auto_hide_enabled

    @property
    def runtime_state(self) -> RuntimeState:
        return self._dock.runtime_state

    @property
    def panel_state(self) -> PanelState:
        return self._dock.panel_state

    @property
    def dock_side(self) -> DockSide:
        return self._dock.dock_side

    @property
    def hide_delay_ms(self) -> int:
        return self._settings.hide_delay_ms

    @property
    def reveal_on_hover_enabled(self) -> bool:
        return self._settings.reveal_on_hover_enabled

    def set_always_on_top(self, enabled: bool) -> None:
        if self._settings.always_on_top == enabled:
            return

        self._settings.always_on_top = enabled
        self._window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)

        is_visible = self._window.isVisible()
        if is_visible:
            self._window.show()
            self._window.raise_()

        self._persist_sidebar_settings()

    def set_auto_hide_enabled(self, enabled: bool) -> None:
        self._dock.set_auto_hide_enabled(enabled)

    def set_hide_delay_ms(self, delay_ms: int) -> None:
        self._dock.set_hide_delay_ms(delay_ms)

    def set_reveal_on_hover_enabled(self, enabled: bool) -> None:
        self._dock.set_reveal_on_hover_enabled(enabled)

    def set_panel_width(self, width: int) -> None:
        normalized = max(self._window.minimumWidth(), width)
        if self._window.width() == normalized:
            return
        self._window.resize(normalized, self._window.height())
        self._dock.handle_resize()
        self._persist_sidebar_settings()

    def on_ready(self) -> None:
        self._dock.restore_position(prefer_collapsed=self._settings.panel_state == PanelState.COLLAPSED)
        self._dock.start()
        self._persist_sidebar_settings()

    def shutdown(self) -> None:
        self._dock.stop()
        self._resize_save_timer.stop()
        self._persist_sidebar_settings()

    def restore_position(self, prefer_collapsed: bool) -> None:
        self._dock.restore_position(prefer_collapsed=prefer_collapsed)
        self._persist_sidebar_settings()

    def reset_position_state(self) -> None:
        self._settings.width = 420
        self._settings.height = 0
        self._settings.expanded_y = 0
        self._settings.panel_state = PanelState.EXPANDED
        self._dock.apply_settings(self._settings)
        self._dock.apply_docked_geometry(prefer_collapsed=False)
        self._persist_sidebar_settings()

    def expand_panel(self) -> None:
        self._dock.expand()

    def collapse_panel(self) -> None:
        self._dock.collapse()

    def set_dock_side(self, side: DockSide) -> None:
        self._dock.set_dock_side(side)
        self._persist_sidebar_settings()

    def set_floating(self, floating: bool) -> None:
        self._dock.set_floating(floating)
        self._persist_sidebar_settings()

    def start_hover_tracking(self) -> None:
        self._dock.start()

    def stop_hover_tracking(self) -> None:
        self._dock.stop()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self._drag_handle:
            return self._handle_drag_events(event)

        if watched is self._window:
            return self._handle_window_events(event)

        return super().eventFilter(watched, event)

    def _handle_drag_events(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event = event if isinstance(event, QMouseEvent) else None
            if mouse_event and mouse_event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                self._drag_offset = mouse_event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
                self._dock.handle_manual_move()
                return True

        if event.type() == QEvent.Type.MouseMove and self._dragging:
            mouse_event = event if isinstance(event, QMouseEvent) else None
            if mouse_event:
                self._window.move(mouse_event.globalPosition().toPoint() - self._drag_offset)
                return True

        if event.type() == QEvent.Type.MouseButtonRelease and self._dragging:
            mouse_event = event if isinstance(event, QMouseEvent) else None
            if mouse_event and mouse_event.button() == Qt.MouseButton.LeftButton:
                self._dragging = False
                self._dock.finish_manual_move()
                return True

        return False

    def _handle_window_events(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self._dock.handle_resize()
            self._resize_save_timer.start()

        return False

    def _apply_initial_geometry(self) -> None:
        width = max(self._window.minimumWidth(), self._settings.width)
        self._window.resize(width, self._window.height())
        self._dock.apply_docked_geometry(prefer_collapsed=self._settings.panel_state == PanelState.COLLAPSED)

    def ensure_docked_geometry(self, prefer_collapsed: bool | None = None) -> None:
        if self._dock.runtime_state == RuntimeState.FLOATING:
            return
        self._dock.apply_docked_geometry(prefer_collapsed=prefer_collapsed)
        self._persist_sidebar_settings()

    def _configure_window_flags(self) -> None:
        self._window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._settings.always_on_top)
        self._window.setWindowFlag(Qt.WindowType.Tool, True)

    def _persist_sidebar_settings(self) -> None:
        snapshot = self._dock.current_settings_snapshot()
        snapshot.always_on_top = self._settings.always_on_top
        self._settings_service.save_sidebar_settings(snapshot)
        self._settings = snapshot
