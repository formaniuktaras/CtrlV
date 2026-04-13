APP_STYLE = """
QWidget {
    background: #1d1f24;
    color: #eceff4;
    font-family: Segoe UI;
    font-size: 10pt;
}
QListWidget {
    background: #23262d;
    border: 1px solid #313641;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #2c313b;
    padding: 6px;
}
QListWidget::item:selected {
    background: #3d5a80;
}
QTabWidget::pane {
    border: 1px solid #313641;
    border-radius: 6px;
    margin-top: 6px;
}
QTabBar::tab {
    background: #2a2f38;
    color: #a8b0bf;
    padding: 6px 10px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #3d5a80;
    color: #eceff4;
}
QPushButton {
    background: #2f3542;
    border: 1px solid #424b5a;
    border-radius: 6px;
    padding: 6px 10px;
}
QPushButton:hover {
    background: #3a4151;
}
QPushButton:pressed {
    background: #2a303c;
}
QLabel#metaLabel {
    color: #a8b0bf;
    font-size: 9pt;
}
QWidget#pinnedItem {
    background: rgba(61, 90, 128, 0.25);
    border-radius: 6px;
}
QPushButton#pinButton {
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
    padding: 0;
    background: transparent;
    border: none;
}
QPushButton#pinButton:hover {
    background: #3a4151;
    border: 1px solid #424b5a;
}
"""
