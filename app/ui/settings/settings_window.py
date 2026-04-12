from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.sidebar_types import DockSide
from app.ui.settings.settings_controller import SettingsController, SettingsViewState


class SettingsWindow(QDialog):
    """Settings UI with live-apply behavior delegated to SettingsController."""

    def __init__(self, controller: SettingsController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller

        self.setWindowTitle("Settings")
        self.setModal(False)
        self.setMinimumWidth(420)
        self.resize(460, 470)

        self._launch_at_startup = QCheckBox("Launch at startup")
        self._start_minimized = QCheckBox("Start minimized to tray")
        self._always_on_top = QCheckBox("Always on top")

        self._auto_hide = QCheckBox("Auto-hide sidebar")
        self._reveal_on_hover = QCheckBox("Reveal on hover")

        self._hide_delay = QSpinBox()
        self._hide_delay.setRange(0, 3000)
        self._hide_delay.setSingleStep(50)
        self._hide_delay.setSuffix(" ms")

        self._dock_side = QComboBox()
        self._dock_side.addItem("Left", DockSide.LEFT)
        self._dock_side.addItem("Right", DockSide.RIGHT)

        self._panel_width_slider = QSlider(Qt.Orientation.Horizontal)
        self._panel_width_slider.setRange(300, 900)
        self._panel_width_slider.setSingleStep(10)
        self._panel_width_value = QLabel("420 px")

        self._reset_panel_button = QPushButton("Reset window position/state")

        self._build_layout()
        self._wire_signals()

    def open_and_sync(self) -> None:
        self._sync_from_state(self._controller.get_current_settings())
        self.show()
        self.raise_()
        self.activateWindow()

    def _build_layout(self) -> None:
        tabs = QTabWidget(self)
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_behavior_tab(), "Behavior")
        tabs.addTab(self._build_panel_tab(), "Panel")
        tabs.addTab(self._build_advanced_tab(), "Advanced")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)
        root.addWidget(tabs)

    def _build_general_tab(self) -> QWidget:
        group = QGroupBox("General")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self._launch_at_startup)
        layout.addWidget(self._start_minimized)
        layout.addWidget(self._always_on_top)

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.addWidget(group)
        root.addStretch(1)
        return wrapper

    def _build_behavior_tab(self) -> QWidget:
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow(self._auto_hide)
        form.addRow(self._reveal_on_hover)
        form.addRow("Hide delay", self._hide_delay)

        note = QLabel("All changes are applied immediately.")
        note.setWordWrap(True)
        note.setObjectName("metaLabel")

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(8, 8, 8, 8)
        root.addLayout(form)
        root.addWidget(note)
        root.addStretch(1)
        return wrapper

    def _build_panel_tab(self) -> QWidget:
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Dock side", self._dock_side)
        form.addRow("Panel width", self._panel_width_slider)
        form.addRow("Width value", self._panel_width_value)

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(8, 8, 8, 8)
        root.addLayout(form)
        root.addStretch(1)
        return wrapper

    def _build_advanced_tab(self) -> QWidget:
        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self._reset_panel_button)
        root.addStretch(1)
        return wrapper

    def _wire_signals(self) -> None:
        self._launch_at_startup.toggled.connect(self._controller.set_autostart)
        self._start_minimized.toggled.connect(self._controller.set_start_minimized_to_tray)
        self._always_on_top.toggled.connect(self._controller.set_always_on_top)

        self._auto_hide.toggled.connect(self._controller.set_auto_hide)
        self._reveal_on_hover.toggled.connect(self._controller.set_reveal_on_hover)
        self._hide_delay.valueChanged.connect(self._controller.set_hide_delay_ms)

        self._dock_side.currentIndexChanged.connect(self._on_dock_side_changed)
        self._panel_width_slider.valueChanged.connect(self._on_panel_width_changed)

        self._reset_panel_button.clicked.connect(self._on_reset_panel)
        self._controller.state_changed.connect(self._sync_from_state)

    def _on_dock_side_changed(self) -> None:
        selected = self._dock_side.currentData()
        if isinstance(selected, DockSide):
            self._controller.set_dock_side(selected)

    def _on_panel_width_changed(self, width: int) -> None:
        self._panel_width_value.setText(f"{width} px")
        self._controller.set_panel_width(width)

    def _on_reset_panel(self) -> None:
        self._sync_from_state(self._controller.reset_window_state())

    def _sync_from_state(self, state: SettingsViewState) -> None:
        blockers = [
            QSignalBlocker(self._launch_at_startup),
            QSignalBlocker(self._start_minimized),
            QSignalBlocker(self._always_on_top),
            QSignalBlocker(self._auto_hide),
            QSignalBlocker(self._reveal_on_hover),
            QSignalBlocker(self._hide_delay),
            QSignalBlocker(self._dock_side),
            QSignalBlocker(self._panel_width_slider),
        ]

        self._launch_at_startup.setChecked(state.launch_at_startup)
        self._start_minimized.setChecked(state.start_minimized_to_tray)
        self._always_on_top.setChecked(state.always_on_top)
        self._auto_hide.setChecked(state.auto_hide_sidebar)
        self._reveal_on_hover.setChecked(state.reveal_on_hover)
        self._hide_delay.setValue(state.hide_delay_ms)

        dock_idx = self._dock_side.findData(state.dock_side)
        self._dock_side.setCurrentIndex(max(0, dock_idx))

        self._panel_width_slider.setValue(state.panel_width)
        self._panel_width_value.setText(f"{state.panel_width} px")

        del blockers
