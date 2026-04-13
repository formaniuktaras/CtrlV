from __future__ import annotations

import logging
import sys
import threading
from types import TracebackType

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

LOGGER = logging.getLogger(__name__)


class RuntimeDiagnostics:
    """Global exception hooks for unhandled runtime failures."""

    def __init__(self) -> None:
        self._dialog_visible = False
        self._original_sys_hook = sys.excepthook
        self._original_thread_hook = threading.excepthook

    def install(self) -> None:
        sys.excepthook = self._handle_unhandled_exception
        threading.excepthook = self._handle_thread_exception
        LOGGER.info("Runtime exception hooks installed")

    def _handle_unhandled_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_sys_hook(exc_type, exc_value, exc_traceback)
            return

        LOGGER.exception(
            "Unhandled exception in main thread",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        self._show_single_error_dialog("A critical error occurred. Check the logs folder for details.")

    def _handle_thread_exception(self, args: threading.ExceptHookArgs) -> None:
        LOGGER.exception(
            "Unhandled exception in background thread: %s",
            getattr(args.thread, "name", "unknown"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        self._show_single_error_dialog("A background error occurred. Check the logs folder for details.")

    def _show_single_error_dialog(self, message: str) -> None:
        app = QApplication.instance()
        if app is None or self._dialog_visible:
            return
        if QThread.currentThread() is not app.thread():
            return

        self._dialog_visible = True

        def show_dialog() -> None:
            try:
                QMessageBox.critical(None, "CtrlV error", message)
            finally:
                self._dialog_visible = False

        QTimer.singleShot(0, show_dialog)
