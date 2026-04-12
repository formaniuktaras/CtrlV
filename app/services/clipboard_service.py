from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QClipboard

from app.core.models import ClipboardItem, ClipboardItemType

LOGGER = logging.getLogger(__name__)


class ClipboardService:
    def __init__(self, clipboard: QClipboard) -> None:
        self._clipboard = clipboard

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
