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
    pinned: bool = False
    pinned_order: int | None = None
    text_content: str | None = None
    image: QImage | None = None
    image_thumbnail: QPixmap | None = None
    file_paths: list[str] | None = None

    def secondary_text(self) -> str:
        timestamp = self.created_at.astimezone().strftime("%H:%M:%S")
        return f"{self.item_type.value.upper()} • {timestamp}"

    @property
    def content(self) -> str:
        if self.item_type is ClipboardItemType.TEXT and self.text_content is not None:
            return self.text_content
        if self.item_type is ClipboardItemType.FILES and self.file_paths:
            return "\n".join(self.file_paths)
        if self.item_type is ClipboardItemType.IMAGE and self.image is not None:
            return f"image:{self.image.width()}x{self.image.height()}"
        return self.preview_text

    @property
    def type(self) -> ClipboardItemType:
        return self.item_type

    @property
    def timestamp(self) -> datetime:
        return self.created_at
