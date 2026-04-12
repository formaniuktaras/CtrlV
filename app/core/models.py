from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from PySide6.QtGui import QImage, QPixmap


class ClipboardItemType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    FILES = "files"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ClipboardItem:
    item_type: ClipboardItemType
    fingerprint: str
    preview_text: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    text_content: str | None = None
    image: QImage | None = None
    image_thumbnail: QPixmap | None = None
    file_paths: list[str] | None = None

    def secondary_text(self) -> str:
        timestamp = self.created_at.astimezone().strftime("%H:%M:%S")
        return f"{self.item_type.value.upper()} • {timestamp}"
