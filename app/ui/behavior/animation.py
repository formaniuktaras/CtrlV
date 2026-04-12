from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation
from PySide6.QtWidgets import QWidget


class AnimationController(QObject):
    """Controls slide animations for sidebar movement."""

    def __init__(self, window: QWidget, duration_ms: int = 180) -> None:
        super().__init__(window)
        self._window = window
        self._animation = QPropertyAnimation(window, b"pos", self)
        self._animation.setDuration(duration_ms)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @property
    def is_running(self) -> bool:
        return self._animation.state() == QPropertyAnimation.State.Running

    def slide_to(self, target: QPoint) -> None:
        current = self._window.pos()
        if current == target and not self.is_running:
            return

        if self.is_running:
            running_target = self._animation.endValue()
            if running_target == target:
                return
            self._animation.stop()
            current = self._window.pos()

        self._animation.setStartValue(current)
        self._animation.setEndValue(target)
        self._animation.start()

    def stop(self) -> None:
        if self.is_running:
            self._animation.stop()
