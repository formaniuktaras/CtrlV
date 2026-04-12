from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.core.models import ClipboardItem


class ClipboardMonitorSignals(QObject):
    item_added = Signal(ClipboardItem)
    duplicate_skipped = Signal(str)
    parse_error = Signal(str)
