from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from PySide6.QtCore import QMimeData, QSize, Qt, QUrl
from PySide6.QtGui import QImage, QPixmap

from app.core.models import ClipboardItem, ClipboardItemType
from app.utils.helpers import normalize_preview_text

LOGGER = logging.getLogger(__name__)


class ClipboardParser:
    def __init__(self, preview_limit: int = 90, thumbnail_size: int = 48) -> None:
        self._preview_limit = preview_limit
        self._thumbnail_size = thumbnail_size

    def parse(self, mime_data: QMimeData) -> ClipboardItem | None:
        if mime_data is None:
            return None

        if mime_data.hasUrls():
            file_paths = self._extract_local_paths(mime_data.urls())
            if file_paths:
                preview = self._files_preview(file_paths)
                fingerprint = self._sha1("files|" + "|".join(file_paths))
                return ClipboardItem(
                    item_type=ClipboardItemType.FILES,
                    file_paths=file_paths,
                    preview_text=preview,
                    fingerprint=fingerprint,
                )

        if mime_data.hasImage():
            image_data = mime_data.imageData()
            if isinstance(image_data, QImage):
                image = image_data
            else:
                image = QImage(image_data)
            if not image.isNull():
                preview = f"[Image] {image.width()}×{image.height()}"
                thumbnail = self._thumbnail_from_image(image)
                fingerprint = self._fingerprint_image(image)
                return ClipboardItem(
                    item_type=ClipboardItemType.IMAGE,
                    image=image,
                    image_thumbnail=thumbnail,
                    preview_text=preview,
                    fingerprint=fingerprint,
                )

        if mime_data.hasText():
            text = mime_data.text()
            normalized = normalize_preview_text(text, self._preview_limit)
            fingerprint = self._sha1("text|" + text)
            return ClipboardItem(
                item_type=ClipboardItemType.TEXT,
                text_content=text,
                preview_text=normalized,
                fingerprint=fingerprint,
            )

        formats = ", ".join(mime_data.formats())
        preview = "[Unknown] Clipboard format"
        fingerprint = self._sha1("unknown|" + formats)
        return ClipboardItem(
            item_type=ClipboardItemType.UNKNOWN,
            preview_text=preview,
            fingerprint=fingerprint,
        )

    def _extract_local_paths(self, urls: list[QUrl]) -> list[str]:
        paths: list[str] = []
        for url in urls:
            if not url.isLocalFile():
                continue
            local_path = Path(url.toLocalFile()).resolve()
            paths.append(str(local_path))
        return paths

    def _files_preview(self, file_paths: list[str]) -> str:
        if len(file_paths) == 1:
            return f"[File] {Path(file_paths[0]).name}"
        head = ", ".join(Path(p).name for p in file_paths[:2])
        if len(file_paths) > 2:
            return f"[Files] {head}, ... ({len(file_paths)} files)"
        return f"[Files] {head}"

    def _thumbnail_from_image(self, image: QImage) -> QPixmap:
        source = QPixmap.fromImage(image)
        return source.scaled(
            QSize(self._thumbnail_size, self._thumbnail_size),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _fingerprint_image(self, image: QImage) -> str:
        encoded_size = image.sizeInBytes()
        bits = image.bits()
        data = bytes(bits[:encoded_size])
        return self._sha1("image|" + hashlib.sha1(data).hexdigest())

    @staticmethod
    def _sha1(value: str) -> str:
        return hashlib.sha1(value.encode("utf-8")).hexdigest()
