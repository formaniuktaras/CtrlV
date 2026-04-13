from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QClipboard

from app.core.history_store import HistoryStore
from app.core.models import ClipboardItem, ClipboardItemType

LOGGER = logging.getLogger(__name__)


class ClipboardService:
    def __init__(self, clipboard: QClipboard, store: HistoryStore) -> None:
        self._clipboard = clipboard
        self._store = store

    def restore_item(self, item: ClipboardItem) -> bool:
        try:
            if item.item_type is ClipboardItemType.TEXT and item.text_content is not None:
                self._clipboard.setText(item.text_content)
            elif item.item_type is ClipboardItemType.IMAGE and item.image is not None:
                self._clipboard.setImage(item.image)
            elif item.item_type is ClipboardItemType.FILES and item.file_paths:
                mime = QMimeData()
                urls = [QUrl.fromLocalFile(str(Path(path))) for path in item.file_paths]
                mime.setUrls(urls)
                self._clipboard.setMimeData(mime)
            else:
                LOGGER.warning("Skipped restoring unsupported item: %s", item.id)
                return False
        except Exception:
            LOGGER.exception("Failed to restore item to clipboard: %s", item.id)
            return False

        LOGGER.info("Item restored to clipboard: %s", item.id)
        return True

    def get_all_items(self) -> list[ClipboardItem]:
        return self._store.get_items()

    def get_pinned_items(self) -> list[ClipboardItem]:
        pinned_items = [item for item in self._store.get_items() if item.pinned]
        return sorted(pinned_items, key=lambda item: item.pinned_order or 0)

    def toggle_pin(self, item_id: str) -> bool:
        item = self._store.get_item_by_id(item_id)
        if item is None:
            return False

        item.pinned = not item.pinned
        if item.pinned:
            item.pinned_order = self._next_pinned_order()
        else:
            item.pinned_order = None
        return True

    def clear_history(self, preserve_pinned: bool = True) -> None:
        self._store.clear(preserve_pinned=preserve_pinned)

    def delete_item(self, item_id: str) -> bool:
        return self._store.remove_item_by_id(item_id)

    def _next_pinned_order(self) -> int:
        orders = [item.pinned_order for item in self._store.get_items() if item.pinned_order is not None]
        if not orders:
            return 1
        return max(orders) + 1
