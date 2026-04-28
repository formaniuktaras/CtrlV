from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.clipboard_monitor import ClipboardMonitor
from app.core.history_store import HistoryStore
from app.core.models import ClipboardItem, ClipboardItemType
from app.services.clipboard_service import ClipboardService
from app.services.paste_service import PasteService
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
        paste_service: PasteService,
        hide_panel_callback: Callable[[], None] | None = None,
        paste_delay_ms: int = 120,
    ) -> None:
        super().__init__()
        self._store = store
        self._service = service
        self._monitor = monitor
        self._paste_service = paste_service
        self._hide_panel_callback = hide_panel_callback
        self._paste_delay_ms = paste_delay_ms

        self._drag_handle = QWidget(self)
        self._tabs = QTabWidget(self)
        self._history_list = HistoryListWidget(self)
        self._pinned_list = HistoryListWidget(self)
        self._status_label = QLabel(self)
        self._status_label.setObjectName("metaLabel")
        self._restore_button = QPushButton("Copy to clipboard", self)
        self._clear_button = QPushButton("Clear", self)

        self._setup_ui()
        self._connect_signals()
        self._refresh_history()
        self._monitor.seed_with_current_clipboard()

    def set_hide_panel_callback(self, callback: Callable[[], None]) -> None:
        self._hide_panel_callback = callback

    def clear_history(self) -> None:
        LOGGER.info("Action=clear_history")
        self._service.clear_history(preserve_pinned=True)
        self._refresh_history()
        self._status_label.setText("History cleared. Pinned items preserved.")

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
        self._restore_button.clicked.connect(self._copy_selected_to_clipboard)
        self._clear_button.clicked.connect(self.clear_history)
        self._history_list.itemDoubleClicked.connect(lambda _: self._paste_selected())
        self._history_list.restore_requested.connect(self._paste_selected)
        self._history_list.pin_toggled.connect(self._toggle_pin)
        self._history_list.delete_requested.connect(self._delete_item)
        self._history_list.itemSelectionChanged.connect(lambda: self._on_selection_changed(self._history_list))

        self._pinned_list.itemDoubleClicked.connect(lambda _: self._paste_selected())
        self._pinned_list.restore_requested.connect(self._paste_selected)
        self._pinned_list.pin_toggled.connect(self._toggle_pin)
        self._pinned_list.delete_requested.connect(self._delete_item)
        self._pinned_list.itemSelectionChanged.connect(lambda: self._on_selection_changed(self._pinned_list))

        self._monitor.signals.item_added.connect(self._on_item_added)
        self._monitor.signals.duplicate_skipped.connect(self._on_duplicate_skipped)
        self._monitor.signals.parse_error.connect(self._on_parse_error)

    def _on_item_added(self, _: ClipboardItem) -> None:
        self._refresh_history()

    def _on_duplicate_skipped(self, fingerprint: str) -> None:
        LOGGER.debug("Action=clipboard_duplicate_skipped fingerprint=%s", fingerprint)

    def _on_parse_error(self, error_message: str) -> None:
        LOGGER.warning("Action=clipboard_parse_error message=%s", error_message)
        self._status_label.setText("Could not process clipboard item")

    def _refresh_history(self, selected_item_id: str | None = None) -> None:
        history_selected_id = self._history_list.selected_item_id()
        pinned_selected_id = self._pinned_list.selected_item_id()

        all_items = self._service.get_all_items()
        pinned_items = self._service.get_pinned_items()
        self._history_list.set_items(all_items)
        self._pinned_list.set_items(pinned_items)

        if selected_item_id is not None:
            self._history_list.select_item_by_id(selected_item_id)
            self._pinned_list.select_item_by_id(selected_item_id)
        else:
            self._history_list.select_item_by_id(history_selected_id)
            self._pinned_list.select_item_by_id(pinned_selected_id)

        if self._history_list.selected_item() is None and self._pinned_list.selected_item() is None:
            self._status_label.setText(f"Items: {len(all_items)} • Pinned: {len(pinned_items)}")

    def _active_list(self) -> HistoryListWidget:
        return self._history_list if self._tabs.currentIndex() == 0 else self._pinned_list

    def _copy_selected_to_clipboard(self) -> None:
        item = self._active_list().selected_item()
        if item is None:
            self._status_label.setText("Select an item first")
            return

        LOGGER.info("Action=copy_to_clipboard item_id=%s item_type=%s", item.id, item.item_type.value)
        self._monitor.mark_programmatic_fingerprint(item.fingerprint)
        restored = self._service.restore_item(item)
        if restored:
            self._status_label.setText("Copied to clipboard")
        else:
            self._status_label.setText("Could not copy selected item")

    def _paste_selected(self) -> None:
        item = self._active_list().selected_item()
        if item is None:
            self._status_label.setText("Select an item first")
            return

        LOGGER.info("Action=double_click_paste item_id=%s item_type=%s", item.id, item.item_type.value)
        self._monitor.mark_programmatic_fingerprint(item.fingerprint)

        if item.item_type is not ClipboardItemType.TEXT:
            restored = self._service.restore_item(item)
            if restored:
                self._status_label.setText("Copied. Paste manually")
            else:
                self._status_label.setText("Could not copy selected item")
            return

        restored = self._service.restore_item(item)
        if not restored:
            self._status_label.setText("Could not copy selected item")
            return

        if self._hide_panel_callback is not None:
            self._hide_panel_callback()

        QTimer.singleShot(self._paste_delay_ms, self._finalize_paste)

    def _finalize_paste(self) -> None:
        pasted = self._paste_service.paste_clipboard_to_previous_window()
        if pasted:
            self._status_label.setText("Pasted into previous window")
        else:
            self._status_label.setText("Could not paste automatically. Press Ctrl+V manually")

    def _toggle_pin(self, item_id: str) -> None:
        LOGGER.info("Action=pin_toggle item_id=%s", item_id)
        current_selection = self._active_list().selected_item_id() or item_id
        if self._service.toggle_pin(item_id):
            self._refresh_history(selected_item_id=current_selection)

    def _delete_item(self, item_id: str) -> None:
        selected_item = self._active_list().selected_item()
        if selected_item is None:
            self._status_label.setText("Select an item first")
            return

        target_id = selected_item.id
        if target_id != item_id:
            LOGGER.debug("Action=delete_item normalized_selected_id=%s requested_id=%s", target_id, item_id)

        LOGGER.info("Action=delete_item item_id=%s item_type=%s", selected_item.id, selected_item.item_type.value)
        if selected_item.pinned:
            self._status_label.setText("Pinned item cannot be deleted. Unpin it first.")
            return

        if self._service.delete_item(target_id):
            self._refresh_history()
            self._status_label.setText("Item deleted")
        else:
            self._status_label.setText("Could not delete selected item")

    def _on_selection_changed(self, source: HistoryListWidget) -> None:
        if source is not self._active_list():
            return

        item = source.selected_item()
        if item is None:
            return

        self._status_label.setText(f"Selected: {self._status_type(item)}")
        LOGGER.info("Action=select_item item_id=%s item_type=%s", item.id, item.item_type.value)

    @staticmethod
    def _status_type(item: ClipboardItem) -> str:
        if item.item_type is ClipboardItemType.FILES:
            return "file"
        if item.item_type is ClipboardItemType.IMAGE:
            return "image"
        if item.item_type is ClipboardItemType.TEXT:
            return "text"
        return item.item_type.value
