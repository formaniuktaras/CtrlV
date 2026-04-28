from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.core.models import ClipboardItem, ClipboardItemType

ITEM_ROLE = Qt.ItemDataRole.UserRole + 1


class HistoryListWidget(QListWidget):
    pin_toggled = Signal(str)
    restore_requested = Signal()
    delete_requested = Signal(str)

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
        list_item.setSizeHint(QSize(250, 54))
        self.addItem(list_item)
        self.setItemWidget(list_item, HistoryItemWidget(item=item, icon=self._icon_for_item(item), parent=self))

    def selected_item(self) -> ClipboardItem | None:
        selected = self.selectedItems()
        if not selected:
            return None
        return selected[0].data(ITEM_ROLE)

    def selected_item_id(self) -> str | None:
        item = self.selected_item()
        return item.id if item is not None else None

    def select_item_by_id(self, item_id: str | None) -> None:
        if item_id is None:
            return
        for row in range(self.count()):
            candidate = self.item(row)
            data = candidate.data(ITEM_ROLE)
            if data is not None and data.id == item_id:
                self.setCurrentItem(candidate)
                return

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.restore_requested.emit()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Delete:
            item = self.selected_item()
            if item is not None:
                self.delete_requested.emit(item.id)
            event.accept()
            return

        super().keyPressEvent(event)

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


class HistoryItemWidget(QWidget):
    def __init__(self, item: ClipboardItem, icon: QIcon, parent: HistoryListWidget) -> None:
        super().__init__(parent)
        self._item = item
        self._list_parent = parent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        icon_label = QLabel(self)
        icon_label.setPixmap(icon.pixmap(24, 24))
        icon_label.setObjectName("historyItemIcon")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._title = QLabel(item.preview_text, self)
        self._title.setWordWrap(True)
        self._meta = QLabel(item.secondary_text(), self)
        self._meta.setObjectName("metaLabel")
        text_layout.addWidget(self._title)
        text_layout.addWidget(self._meta)
        layout.addLayout(text_layout, stretch=1)

        self._pin_button = QPushButton("📌" if item.pinned else "📍", self)
        self._pin_button.setObjectName("pinButton")
        self._pin_button.setToolTip("Unpin item" if item.pinned else "Pin item")
        self._pin_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pin_button.clicked.connect(self._on_pin_clicked)
        layout.addWidget(self._pin_button, alignment=Qt.AlignmentFlag.AlignTop)

        if item.pinned:
            self.setObjectName("pinnedItem")

    def _on_pin_clicked(self) -> None:
        self._list_parent.pin_toggled.emit(self._item.id)
