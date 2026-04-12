from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.clipboard_monitor import ClipboardMonitor
from app.core.history_store import HistoryStore
from app.core.models import ClipboardItem
from app.services.clipboard_service import ClipboardService
from app.services.settings_service import SettingsService
from app.ui.behavior import WindowBehaviorController
from app.ui.history_list import HistoryListWidget

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    close_requested = Signal(object)
    visibility_changed = Signal(bool)

    def __init__(
        self,
        store: HistoryStore,
        service: ClipboardService,
        monitor: ClipboardMonitor,
        settings_service: SettingsService,
    ) -> None:
        super().__init__()
        self._store = store
        self._service = service
        self._monitor = monitor

        self._drag_handle = QWidget(self)
        self._history_list = HistoryListWidget(self)
        self._status_label = QLabel(self)
        self._status_label.setObjectName("metaLabel")
        self._restore_button = QPushButton("Copy selected again", self)
        self._clear_button = QPushButton("Clear", self)

        self._window_behavior = WindowBehaviorController(
            window=self,
            drag_handle=self._drag_handle,
            settings_service=settings_service,
        )

        self._setup_ui()
        self._connect_signals()
        self._refresh_history()
        self._monitor.seed_with_current_clipboard()
        self._window_behavior.on_ready()

    @property
    def always_on_top(self) -> bool:
        return self._window_behavior.always_on_top

    @property
    def auto_hide_enabled(self) -> bool:
        return self._window_behavior.auto_hide_enabled

    def set_always_on_top(self, enabled: bool) -> None:
        self._window_behavior.set_always_on_top(enabled)

    def set_auto_hide_enabled(self, enabled: bool) -> None:
        self._window_behavior.set_auto_hide_enabled(enabled)

    def clear_history(self) -> None:
        self._store.clear()
        self._refresh_history()

    def shutdown(self) -> None:
        self._window_behavior.shutdown()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.close_requested.emit(event)
        if event.isAccepted():
            super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event: QHideEvent) -> None:  # noqa: N802
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(340)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        handle_layout = QHBoxLayout(self._drag_handle)
        handle_layout.setContentsMargins(0, 0, 0, 0)
        handle_layout.setSpacing(8)
        title = QLabel("CtrlV Clipboard", self._drag_handle)
        title.setObjectName("metaLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        handle_layout.addWidget(title)
        self._drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self._drag_handle.setFixedHeight(20)

        button_row = QHBoxLayout()
        button_row.addWidget(self._restore_button)
        button_row.addWidget(self._clear_button)

        layout.addWidget(self._drag_handle)
        layout.addLayout(button_row)
        layout.addWidget(self._history_list, stretch=1)
        layout.addWidget(self._status_label)

        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self._restore_button.clicked.connect(self._restore_selected)
        self._clear_button.clicked.connect(self.clear_history)
        self._history_list.itemDoubleClicked.connect(lambda _: self._restore_selected())

        self._monitor.signals.item_added.connect(self._on_item_added)
        self._monitor.signals.duplicate_skipped.connect(self._on_duplicate_skipped)
        self._monitor.signals.parse_error.connect(self._on_parse_error)

    def _on_item_added(self, _: ClipboardItem) -> None:
        self._refresh_history()

    def _on_duplicate_skipped(self, fingerprint: str) -> None:
        LOGGER.debug("Duplicate skipped by monitor: %s", fingerprint)

    def _on_parse_error(self, error_message: str) -> None:
        QMessageBox.warning(self, "Clipboard parse error", error_message)

    def _refresh_history(self) -> None:
        self._history_list.set_items(self._store.get_items())
        self._status_label.setText(f"Items in history: {len(self._store)}")

    def _restore_selected(self) -> None:
        item = self._history_list.selected_item()
        if item is None:
            return
        self._monitor.mark_programmatic_fingerprint(item.fingerprint)
        restored = self._service.restore_item(item)
        if restored:
            self._status_label.setText(f"Restored item: {item.item_type.value}")
        else:
            self._status_label.setText("Failed to restore selected item")
