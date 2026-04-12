from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QEvent, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from app.ui.behavior.animation import AnimationController
from app.ui.behavior.edge_dock import EdgeDockController


class WindowBehaviorController(QObject):
    """Configures sidebar window mode and delegates runtime behavior to controllers."""

    def __init__(self, window: QWidget, drag_handle: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self._drag_handle = drag_handle

        self._animation = AnimationController(window)
        self._dock = EdgeDockController(window=window, animation=self._animation)

        self._dragging = False
        self._drag_offset = QPoint()

        self._configure_window_flags()
        self._drag_handle.installEventFilter(self)

    def on_ready(self) -> None:
        self._dock.snap_to_nearest_edge()
        self._dock.start()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is not self._drag_handle:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event = event if isinstance(event, QMouseEvent) else None
            if mouse_event and mouse_event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                self._drag_offset = mouse_event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
                self._animation.stop()
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
                self._dock.snap_to_nearest_edge()
                return True

        return super().eventFilter(watched, event)

    def _configure_window_flags(self) -> None:
        self._window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._window.setWindowFlag(Qt.WindowType.Tool, True)
