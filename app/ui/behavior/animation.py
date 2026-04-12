from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation, Signal
from PySide6.QtWidgets import QWidget


class AnimationTarget(str, Enum):
    EXPAND = "expand"
    COLLAPSE = "collapse"


class AnimationController(QObject):
    """Controls sidebar slide animations with explicit targets."""

    finished = Signal(str)

    def __init__(self, window: QWidget, duration_ms: int = 180) -> None:
        super().__init__(window)
        self._window = window
        self._animation = QPropertyAnimation(window, b"pos", self)
        self._animation.setDuration(duration_ms)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.finished.connect(self._on_finished)

        self._active_target: AnimationTarget | None = None

    @property
    def is_running(self) -> bool:
        return self._animation.state() == QPropertyAnimation.State.Running

    @property
    def active_target(self) -> AnimationTarget | None:
        return self._active_target

    def animate_expand(self, target: QPoint) -> bool:
        return self._start(AnimationTarget.EXPAND, target)

    def animate_collapse(self, target: QPoint) -> bool:
        return self._start(AnimationTarget.COLLAPSE, target)

    def stop(self) -> None:
        if self.is_running:
            self._animation.stop()
        self._active_target = None

    def _start(self, target_state: AnimationTarget, target_pos: QPoint) -> bool:
        current = self._window.pos()
        if current == target_pos and not self.is_running:
            return False

        if self.is_running:
            same_target = self._active_target == target_state
            same_position = self._animation.endValue() == target_pos
            if same_target and same_position:
                return False
            self._animation.stop()
            current = self._window.pos()

        self._active_target = target_state
        self._animation.setStartValue(current)
        self._animation.setEndValue(target_pos)
        self._animation.start()
        return True

    def _on_finished(self) -> None:
        if self._active_target is None:
            return
        target = self._active_target
        self._active_target = None
        self.finished.emit(target.value)
