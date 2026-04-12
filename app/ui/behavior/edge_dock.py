from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, QPoint, QRect, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QWidget

from app.ui.behavior.animation import AnimationController


class DockSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class PanelState(str, Enum):
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"


class EdgeDockController(QObject):
    """Handles edge snap, auto-hide and hover-reveal behavior."""

    def __init__(
        self,
        window: QWidget,
        animation: AnimationController,
        visible_edge_px: int = 8,
        hide_delay_ms: int = 450,
        reveal_delay_ms: int = 90,
        hover_check_ms: int = 60,
        edge_trigger_px: int = 3,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._animation = animation
        self._visible_edge_px = visible_edge_px
        self._edge_trigger_px = edge_trigger_px

        self._dock_side = DockSide.RIGHT
        self._state = PanelState.EXPANDED
        self._docked = False

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
    def state(self) -> PanelState:
        return self._state

    def start(self) -> None:
        self._hover_poll_timer.start()

    def stop(self) -> None:
        self._hover_poll_timer.stop()
        self._hide_timer.stop()
        self._reveal_timer.stop()

    def snap_to_nearest_edge(self) -> None:
        screen_geometry = self._active_screen_geometry()
        center_x = self._window.frameGeometry().center().x()

        distance_left = abs(center_x - screen_geometry.left())
        distance_right = abs(screen_geometry.right() - center_x)
        self._dock_side = DockSide.LEFT if distance_left <= distance_right else DockSide.RIGHT

        clamped_y = self._clamp_y(self._window.y(), screen_geometry)
        expanded_pos = self._expanded_position(screen_geometry, clamped_y)
        self._window.move(expanded_pos)

        self._docked = True

    def expand(self) -> None:
        if not self._docked:
            return
        self._hide_timer.stop()
        self._reveal_timer.stop()
        screen_geometry = self._active_screen_geometry()
        target = self._expanded_position(screen_geometry, self._window.y())
        self._animation.slide_to(target)
        self._state = PanelState.EXPANDED

    def collapse(self) -> None:
        if not self._docked:
            return
        self._hide_timer.stop()
        self._reveal_timer.stop()
        screen_geometry = self._active_screen_geometry()
        target = self._collapsed_position(screen_geometry, self._window.y())
        self._animation.slide_to(target)
        self._state = PanelState.COLLAPSED

    def handle_manual_move(self) -> None:
        self._docked = False
        self._state = PanelState.EXPANDED
        self._hide_timer.stop()
        self._reveal_timer.stop()

    def _update_hover_state(self) -> None:
        if not self._docked:
            return

        global_cursor = QCursor.pos()
        local_cursor = self._window.mapFromGlobal(global_cursor)
        panel_rect = QRect(QPoint(0, 0), self._window.size())
        hovered_panel = panel_rect.contains(local_cursor)

        if hovered_panel:
            self.expand()
            return

        if self._state == PanelState.EXPANDED:
            if not self._hide_timer.isActive():
                self._hide_timer.start()
            return

        if self._state == PanelState.COLLAPSED and self._cursor_hits_reveal_zone(global_cursor):
            if not self._reveal_timer.isActive():
                self._reveal_timer.start()
        else:
            self._reveal_timer.stop()

    def _cursor_hits_reveal_zone(self, cursor: QPoint) -> bool:
        screen_geometry = self._active_screen_geometry(cursor)
        if self._dock_side == DockSide.LEFT:
            return cursor.x() <= screen_geometry.left() + self._edge_trigger_px
        return cursor.x() >= screen_geometry.right() - self._edge_trigger_px

    def _expanded_position(self, screen: QRect, y: int) -> QPoint:
        clamped_y = self._clamp_y(y, screen)
        x = screen.left() if self._dock_side == DockSide.LEFT else screen.right() - self._window.width() + 1
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

    def _active_screen_geometry(self, reference: QPoint | None = None) -> QRect:
        point = reference if reference is not None else self._window.frameGeometry().center()
        screen = QGuiApplication.screenAt(point)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()
