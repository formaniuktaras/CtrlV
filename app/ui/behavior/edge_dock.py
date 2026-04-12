from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QRect, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QWidget

from app.services.settings_service import SidebarSettings
from app.ui.behavior.animation import AnimationController, AnimationTarget
from app.ui.behavior.types import DockSide, PanelState, RuntimeState


class EdgeDockController(QObject):
    """Handles edge snap, auto-hide and hover-reveal behavior."""

    state_changed = Signal(str)
    dock_side_changed = Signal(str)
    settings_changed = Signal()

    def __init__(
        self,
        window: QWidget,
        animation: AnimationController,
        hide_delay_ms: int = 450,
        reveal_delay_ms: int = 90,
        hover_check_ms: int = 60,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._animation = animation
        self._animation.finished.connect(self._on_animation_finished)

        self._visible_edge_px = 8
        self._edge_trigger_px = 3
        self._reveal_vertical_tolerance_px = 80
        self._auto_hide_enabled = True

        self._dock_side = DockSide.RIGHT
        self._runtime_state = RuntimeState.FLOATING
        self._last_expanded_pos = QPoint(0, 120)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(hide_delay_ms)
        self._hide_timer.timeout.connect(self.collapse)

        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.setInterval(reveal_delay_ms)
        self._reveal_timer.timeout.connect(self.expand)

        self._hover_poll_timer = QTimer(self)
        self._hover_poll_timer.setInterval(hover_check_ms)
        self._hover_poll_timer.timeout.connect(self._update_hover_state)

    @property
    def runtime_state(self) -> RuntimeState:
        return self._runtime_state

    @property
    def panel_state(self) -> PanelState:
        if self._runtime_state == RuntimeState.DOCKED_COLLAPSED:
            return PanelState.COLLAPSED
        return PanelState.EXPANDED

    def apply_settings(self, settings: SidebarSettings) -> None:
        self._dock_side = settings.dock_side
        self._visible_edge_px = max(1, settings.visible_edge_px)
        self._edge_trigger_px = max(1, settings.reveal_trigger_px)
        self._reveal_vertical_tolerance_px = max(0, settings.reveal_vertical_tolerance_px)
        self._auto_hide_enabled = settings.auto_hide_enabled
        self._last_expanded_pos = QPoint(settings.expanded_x, settings.expanded_y)

    def start(self) -> None:
        self._hover_poll_timer.start()

    def stop(self) -> None:
        self._hover_poll_timer.stop()
        self._hide_timer.stop()
        self._reveal_timer.stop()

    def restore_position(self, prefer_collapsed: bool) -> None:
        screen = self._active_screen_geometry(self._last_expanded_pos)
        self._clamp_window_size(screen)
        expanded = self._expanded_position(screen, self._last_expanded_pos.y())
        self._last_expanded_pos = expanded

        if prefer_collapsed:
            self._window.move(self._collapsed_position(screen, expanded.y()))
            self._set_runtime_state(RuntimeState.DOCKED_COLLAPSED)
        else:
            self._window.move(expanded)
            self._set_runtime_state(RuntimeState.DOCKED_EXPANDED)

    def snap_to_nearest_edge(self) -> None:
        screen = self._active_screen_geometry()
        self._clamp_window_size(screen)
        center_x = self._window.frameGeometry().center().x()

        old_side = self._dock_side
        left_dist = abs(center_x - screen.left())
        right_dist = abs(screen.right() - center_x)
        self._dock_side = DockSide.LEFT if left_dist <= right_dist else DockSide.RIGHT
        if old_side != self._dock_side:
            self.dock_side_changed.emit(self._dock_side.value)

        expanded = self._expanded_position(screen, self._window.y())
        self._window.move(expanded)
        self._last_expanded_pos = expanded
        self._set_runtime_state(RuntimeState.DOCKED_EXPANDED)
        self.settings_changed.emit()

    def expand(self) -> None:
        if self._runtime_state not in {RuntimeState.DOCKED_COLLAPSED, RuntimeState.ANIMATING_COLLAPSE}:
            return
        self._hide_timer.stop()
        self._reveal_timer.stop()

        screen = self._active_screen_geometry()
        target = self._expanded_position(screen, self._window.y())
        started = self._animation.animate_expand(target)
        if started:
            self._set_runtime_state(RuntimeState.ANIMATING_EXPAND)
        else:
            self._window.move(target)
            self._last_expanded_pos = target
            self._set_runtime_state(RuntimeState.DOCKED_EXPANDED)
            self.settings_changed.emit()

    def collapse(self) -> None:
        if not self._auto_hide_enabled:
            return
        if self._runtime_state not in {RuntimeState.DOCKED_EXPANDED, RuntimeState.ANIMATING_EXPAND}:
            return
        self._hide_timer.stop()
        self._reveal_timer.stop()

        screen = self._active_screen_geometry()
        target = self._collapsed_position(screen, self._window.y())
        started = self._animation.animate_collapse(target)
        if started:
            self._set_runtime_state(RuntimeState.ANIMATING_COLLAPSE)
        else:
            self._window.move(target)
            self._set_runtime_state(RuntimeState.DOCKED_COLLAPSED)
            self.settings_changed.emit()

    def handle_manual_move(self) -> None:
        self._hide_timer.stop()
        self._reveal_timer.stop()
        self._animation.stop()

        if self._runtime_state in {RuntimeState.DOCKED_EXPANDED, RuntimeState.ANIMATING_EXPAND}:
            self._last_expanded_pos = self._window.pos()
        self._set_runtime_state(RuntimeState.DRAGGING)

    def finish_manual_move(self) -> None:
        self.snap_to_nearest_edge()

    def handle_resize(self) -> None:
        screen = self._active_screen_geometry()
        self._clamp_window_size(screen)

        if self._runtime_state in {RuntimeState.DOCKED_EXPANDED, RuntimeState.ANIMATING_EXPAND}:
            expanded = self._expanded_position(screen, self._window.y())
            self._window.move(expanded)
            self._last_expanded_pos = expanded
        elif self._runtime_state in {RuntimeState.DOCKED_COLLAPSED, RuntimeState.ANIMATING_COLLAPSE}:
            expanded = self._expanded_position(screen, self._window.y())
            self._last_expanded_pos = expanded
            self._window.move(self._collapsed_position(screen, expanded.y()))

        self.settings_changed.emit()

    def current_settings_snapshot(self) -> SidebarSettings:
        return SidebarSettings(
            width=self._window.width(),
            height=self._window.height(),
            expanded_x=self._last_expanded_pos.x(),
            expanded_y=self._last_expanded_pos.y(),
            dock_side=self._dock_side,
            panel_state=self.panel_state,
            visible_edge_px=self._visible_edge_px,
            auto_hide_enabled=self._auto_hide_enabled,
            always_on_top=True,
            reveal_trigger_px=self._edge_trigger_px,
            reveal_vertical_tolerance_px=self._reveal_vertical_tolerance_px,
        )

    def _update_hover_state(self) -> None:
        if self._runtime_state in {RuntimeState.FLOATING, RuntimeState.DRAGGING}:
            return

        cursor = QCursor.pos()
        local = self._window.mapFromGlobal(cursor)
        hovered_panel = QRect(QPoint(0, 0), self._window.size()).contains(local)

        if hovered_panel:
            self._hide_timer.stop()
            if self._runtime_state == RuntimeState.DOCKED_COLLAPSED:
                self._request_reveal()
            return

        if self._runtime_state == RuntimeState.ANIMATING_EXPAND:
            return

        if self._runtime_state == RuntimeState.ANIMATING_COLLAPSE:
            self._reveal_timer.stop()
            return

        if self._runtime_state == RuntimeState.DOCKED_EXPANDED:
            self._request_collapse()
            return

        if self._runtime_state == RuntimeState.DOCKED_COLLAPSED:
            self._request_reveal() if self._cursor_hits_reveal_zone(cursor) else self._reveal_timer.stop()

    def _request_collapse(self) -> None:
        if not self._auto_hide_enabled:
            return
        self._reveal_timer.stop()
        if not self._hide_timer.isActive():
            self._hide_timer.start()

    def _request_reveal(self) -> None:
        self._hide_timer.stop()
        if not self._reveal_timer.isActive():
            self._reveal_timer.start()

    def _on_animation_finished(self, target: str) -> None:
        if target == AnimationTarget.EXPAND.value:
            screen = self._active_screen_geometry()
            expanded = self._expanded_position(screen, self._window.y())
            self._window.move(expanded)
            self._last_expanded_pos = expanded
            self._set_runtime_state(RuntimeState.DOCKED_EXPANDED)
            self.settings_changed.emit()
            return

        if target == AnimationTarget.COLLAPSE.value:
            self._set_runtime_state(RuntimeState.DOCKED_COLLAPSED)
            self.settings_changed.emit()

    def _cursor_hits_reveal_zone(self, cursor: QPoint) -> bool:
        screen = self._active_screen_geometry(cursor)

        if self._dock_side == DockSide.LEFT:
            edge_hit = cursor.x() <= screen.left() + self._edge_trigger_px
        else:
            edge_hit = cursor.x() >= screen.right() - self._edge_trigger_px

        if not edge_hit:
            return False

        top = self._window.y() - self._reveal_vertical_tolerance_px
        bottom = self._window.y() + self._window.height() + self._reveal_vertical_tolerance_px
        return top <= cursor.y() <= bottom

    def _expanded_position(self, screen: QRect, y: int) -> QPoint:
        clamped_y = self._clamp_y(y, screen)
        if self._dock_side == DockSide.LEFT:
            x = screen.left()
        else:
            x = screen.right() - self._window.width() + 1
        return QPoint(x, clamped_y)

    def _collapsed_position(self, screen: QRect, y: int) -> QPoint:
        clamped_y = self._clamp_y(y, screen)
        if self._dock_side == DockSide.LEFT:
            x = screen.left() - self._window.width() + self._visible_edge_px
        else:
            x = screen.right() - self._visible_edge_px + 1
        return QPoint(x, clamped_y)

    def _clamp_y(self, y: int, screen: QRect) -> int:
        top = screen.top()
        bottom = screen.bottom() - self._window.height() + 1
        if bottom < top:
            return top
        return max(top, min(y, bottom))

    def _clamp_window_size(self, screen: QRect) -> None:
        clamped_height = max(1, min(self._window.height(), screen.height()))
        clamped_width = max(1, min(self._window.width(), screen.width()))

        if clamped_width != self._window.width() or clamped_height != self._window.height():
            self._window.resize(clamped_width, clamped_height)

    def _active_screen_geometry(self, reference: QPoint | None = None) -> QRect:
        point = reference if reference is not None else self._window.frameGeometry().center()
        screen = QGuiApplication.screenAt(point)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()

    def _set_runtime_state(self, state: RuntimeState) -> None:
        if self._runtime_state == state:
            return
        self._runtime_state = state
        self.state_changed.emit(state.value)
