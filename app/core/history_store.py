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
        if len(self._items) > self._max_items:
            self._items = self._items[: self._max_items]
        return True

    def get_items(self) -> list[ClipboardItem]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)
