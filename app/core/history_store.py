from __future__ import annotations

import logging

from app.core.models import ClipboardItem

LOGGER = logging.getLogger(__name__)


class HistoryStore:
    def __init__(self, max_items: int = 100) -> None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than zero")
        self._max_items = max_items
        self._items: list[ClipboardItem] = []

    @property
    def max_items(self) -> int:
        return self._max_items

    def add_item(self, item: ClipboardItem) -> bool:
        if self._items and self._items[0].fingerprint == item.fingerprint:
            LOGGER.info("Duplicate skipped: %s", item.fingerprint)
            return False

        self._items.insert(0, item)
        self._truncate_to_limit()
        return True

    def get_items(self) -> list[ClipboardItem]:
        return list(self._items)

    def get_item_by_id(self, item_id: str) -> ClipboardItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def remove_item_by_id(self, item_id: str) -> bool:
        for index, item in enumerate(self._items):
            if item.id != item_id:
                continue
            if item.pinned:
                return False
            del self._items[index]
            return True
        return False

    def clear(self, preserve_pinned: bool = False) -> None:
        if preserve_pinned:
            self._items = [item for item in self._items if item.pinned]
            return
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def _truncate_to_limit(self) -> None:
        while len(self._items) > self._max_items:
            drop_index: int | None = None
            for index in range(len(self._items) - 1, -1, -1):
                if not self._items[index].pinned:
                    drop_index = index
                    break

            if drop_index is None:
                drop_index = len(self._items) - 1

            del self._items[drop_index]
