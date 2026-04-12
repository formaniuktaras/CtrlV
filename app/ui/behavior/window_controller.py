from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QEvent, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from app.services.settings_service import SettingsService
from app.ui.behavior.animation import AnimationController
from app.ui.behavior.edge_dock import EdgeDockController
from app.ui.behavior.types import PanelState


class WindowBehaviorController(QObject):
    """Configures sidebar window mode and delegates runtime behavior to controllers."""

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

    def on_ready(self) -> None:
        self._dock.restore_position(prefer_collapsed=self._settings.panel_state == PanelState.COLLAPSED)
        self._dock.start()
        self._persist_sidebar_settings()

    def shutdown(self) -> None:
        self._dock.stop()
        self._resize_save_timer.stop()
        self._persist_sidebar_settings()

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

        if event.type() == QEvent.Type.Close:
            self.shutdown()

        return False

    def _apply_initial_geometry(self) -> None:
        self._window.resize(self._settings.width, self._settings.height)

    def _configure_window_flags(self) -> None:
        self._window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._settings.always_on_top)
        self._window.setWindowFlag(Qt.WindowType.Tool, True)

    def _persist_sidebar_settings(self) -> None:
        snapshot = self._dock.current_settings_snapshot()
        snapshot.always_on_top = self._settings.always_on_top
        self._settings_service.save_sidebar_settings(snapshot)
        self._settings = snapshot
