from __future__ import annotations

import logging

from PySide6.QtGui import QClipboard

from app.core.clipboard_parser import ClipboardParser
from app.core.history_store import HistoryStore
from app.core.models import ClipboardItem
from app.core.signals import ClipboardMonitorSignals

LOGGER = logging.getLogger(__name__)


class ClipboardMonitor:
    def __init__(self, clipboard: QClipboard, parser: ClipboardParser, store: HistoryStore) -> None:
        self._clipboard = clipboard
        self._parser = parser
        self._store = store
        self.signals = ClipboardMonitorSignals()
        self._ignored_fingerprint: str | None = None

        self._clipboard.dataChanged.connect(self._on_clipboard_changed)

    def mark_programmatic_fingerprint(self, fingerprint: str) -> None:
        self._ignored_fingerprint = fingerprint

    def _on_clipboard_changed(self) -> None:
        LOGGER.info("Clipboard changed")
        mime_data = self._clipboard.mimeData()
        if mime_data is None:
            return

        try:
            item = self._parser.parse(mime_data)
        except Exception as exc:
            LOGGER.exception("Failed to parse clipboard content")
            self.signals.parse_error.emit(str(exc))
            return

        if item is None:
            return

        LOGGER.info("Item parsed: %s", item.item_type.value)
        if self._ignored_fingerprint and item.fingerprint == self._ignored_fingerprint:
            LOGGER.info("Self-trigger skipped: %s", item.fingerprint)
            self._ignored_fingerprint = None
            return

        self._ignored_fingerprint = None
        added = self._store.add_item(item)
        if not added:
            self.signals.duplicate_skipped.emit(item.fingerprint)
            return

        self.signals.item_added.emit(item)

    @property
    def store(self) -> HistoryStore:
        return self._store

    def shutdown(self) -> None:
        self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)

    def seed_with_current_clipboard(self) -> None:
        current = self._clipboard.mimeData()
        if current is None:
            return
        item = self._parser.parse(current)
        if item and self._store.add_item(item):
            self.signals.item_added.emit(item)
