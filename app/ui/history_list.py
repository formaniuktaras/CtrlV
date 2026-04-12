from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStyle

from app.core.models import ClipboardItem, ClipboardItemType

ITEM_ROLE = Qt.ItemDataRole.UserRole + 1


class HistoryListWidget(QListWidget):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setIconSize(QSize(32, 32))

    def set_items(self, items: list[ClipboardItem]) -> None:
        self.clear()
        for item in items:
            self.add_history_item(item)

    def add_history_item(self, item: ClipboardItem) -> None:
        list_item = QListWidgetItem()
        list_item.setData(ITEM_ROLE, item)
        list_item.setIcon(self._icon_for_item(item))
        list_item.setText(f"{item.preview_text}\n{item.secondary_text()}")
        self.insertItem(0, list_item)

    def selected_item(self) -> ClipboardItem | None:
        selected = self.selectedItems()
        if not selected:
            return None
        return selected[0].data(ITEM_ROLE)

    def _icon_for_item(self, item: ClipboardItem) -> QIcon:
        if item.item_type is ClipboardItemType.IMAGE and item.image_thumbnail is not None:
            return QIcon(item.image_thumbnail)

        style = self.style()
        if item.item_type is ClipboardItemType.TEXT:
            return style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        if item.item_type is ClipboardItemType.FILES:
            return style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        if item.item_type is ClipboardItemType.IMAGE:
            return style.standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        return style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
