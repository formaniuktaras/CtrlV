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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.clipboard_monitor import ClipboardMonitor
from app.core.history_store import HistoryStore
from app.core.models import ClipboardItem
from app.services.clipboard_service import ClipboardService
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
    ) -> None:
        super().__init__()
        self._store = store
        self._service = service
        self._monitor = monitor

        self._drag_handle = QWidget(self)
        self._tabs = QTabWidget(self)
        self._history_list = HistoryListWidget(self)
        self._pinned_list = HistoryListWidget(self)
        self._status_label = QLabel(self)
        self._status_label.setObjectName("metaLabel")
        self._restore_button = QPushButton("Copy selected again", self)
        self._clear_button = QPushButton("Clear", self)

        self._setup_ui()
        self._connect_signals()
        self._refresh_history()
        self._monitor.seed_with_current_clipboard()

    def clear_history(self) -> None:
        LOGGER.info("History cleared by user action")
        self._service.clear_history(preserve_pinned=True)
        self._refresh_history()

    def shutdown(self) -> None:
        pass

    @property
    def drag_handle(self) -> QWidget:
        return self._drag_handle

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
        self._tabs.addTab(self._history_list, "History")
        self._tabs.addTab(self._pinned_list, "Pinned")
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._status_label)

        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self._restore_button.clicked.connect(self._restore_selected)
        self._clear_button.clicked.connect(self.clear_history)
        self._history_list.itemDoubleClicked.connect(lambda _: self._restore_selected())
        self._history_list.restore_requested.connect(self._restore_selected)
        self._history_list.pin_toggled.connect(self._toggle_pin)
        self._history_list.delete_requested.connect(self._delete_item)

        self._pinned_list.itemDoubleClicked.connect(lambda _: self._restore_selected())
        self._pinned_list.restore_requested.connect(self._restore_selected)
        self._pinned_list.pin_toggled.connect(self._toggle_pin)
        self._pinned_list.delete_requested.connect(self._delete_item)

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
        all_items = self._service.get_all_items()
        pinned_items = self._service.get_pinned_items()
        self._history_list.set_items(all_items)
        self._pinned_list.set_items(pinned_items)
        self._status_label.setText(f"Items: {len(all_items)} • Pinned: {len(pinned_items)}")

    def _restore_selected(self) -> None:
        current_list = self._history_list if self._tabs.currentIndex() == 0 else self._pinned_list
        item = current_list.selected_item()
        if item is None:
            return
        self._monitor.mark_programmatic_fingerprint(item.fingerprint)
        restored = self._service.restore_item(item)
        if restored:
            self._status_label.setText(f"Restored item: {item.item_type.value}")
        else:
            self._status_label.setText("Failed to restore selected item")

    def _toggle_pin(self, item_id: str) -> None:
        if self._service.toggle_pin(item_id):
            self._refresh_history()

    def _delete_item(self, item_id: str) -> None:
        if self._service.delete_item(item_id):
            self._refresh_history()
