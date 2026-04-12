from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.sidebar_types import DockSide
from app.ui.settings.settings_controller import SettingsController, SettingsViewState


class SettingsWindow(QDialog):
    """User-facing settings editor for sidebar and startup behavior."""

    def __init__(self, controller: SettingsController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._loaded_state: SettingsViewState | None = None

        self.setWindowTitle("Settings")
        self.setModal(False)
        self.resize(460, 430)

        self._launch_at_startup = QCheckBox("Launch at startup")
        self._start_minimized = QCheckBox("Start minimized to tray")
        self._always_on_top = QCheckBox("Keep sidebar above other windows")

        self._auto_hide = QCheckBox("Auto-hide sidebar")
        self._reveal_on_hover = QCheckBox("Reveal when pointer touches screen edge")
        self._hide_delay = QSpinBox()
        self._hide_delay.setRange(0, 3000)
        self._hide_delay.setSingleStep(50)
        self._hide_delay.setSuffix(" ms")

        self._dock_side = QComboBox()
        self._dock_side.addItem("Left", DockSide.LEFT)
        self._dock_side.addItem("Right", DockSide.RIGHT)

        self._panel_width = QSpinBox()
        self._panel_width.setRange(300, 900)
        self._panel_width.setSingleStep(10)
        self._panel_width.setSuffix(" px")

        self._reset_panel_button = QPushButton("Reset window position/state")

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )

        self._build_layout()
        self._wire_signals()

    def open_and_sync(self) -> None:
        self._loaded_state = self._controller.load_state()
        self._set_controls_from_state(self._loaded_state)
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
        root.addWidget(self._buttons)

    def _build_general_tab(self) -> QWidget:
        group = QGroupBox("General")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self._launch_at_startup)
        layout.addWidget(self._start_minimized)
        layout.addWidget(self._always_on_top)

        note = QLabel("These options control how CtrlV starts and stays visible.")
        note.setWordWrap(True)
        note.setObjectName("metaLabel")
        layout.addWidget(note)

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.addWidget(group)
        root.addStretch(1)
        return wrapper

    def _build_behavior_tab(self) -> QWidget:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setSpacing(10)

        form.addRow(self._auto_hide)
        form.addRow(self._reveal_on_hover)
        form.addRow("Hide delay", self._hide_delay)

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(8, 8, 8, 8)
        root.addLayout(form)
        root.addStretch(1)
        return wrapper

    def _build_panel_tab(self) -> QWidget:
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Dock side", self._dock_side)
        form.addRow("Panel width", self._panel_width)

        hint = QLabel("Changes apply to the sidebar layout.")
        hint.setObjectName("metaLabel")

        wrapper = QWidget()
        root = QVBoxLayout(wrapper)
        root.setContentsMargins(8, 8, 8, 8)
        root.addLayout(form)
        root.addWidget(hint)
        root.addStretch(1)
        return wrapper

    def _build_advanced_tab(self) -> QWidget:
        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(8, 8, 8, 8)
        row.addWidget(self._reset_panel_button)
        row.addStretch(1)
        return wrapper

    def _wire_signals(self) -> None:
        self._buttons.accepted.connect(self._on_ok)
        self._buttons.rejected.connect(self.reject)
        apply_button = self._buttons.button(QDialogButtonBox.StandardButton.Apply)
        if apply_button is not None:
            apply_button.clicked.connect(self._apply)

        self._reset_panel_button.clicked.connect(self._on_reset_panel)

    def _on_ok(self) -> None:
        if self._apply():
            self.accept()

    def _apply(self) -> bool:
        success = self._controller.apply_state(self._read_state_from_controls())
        if success:
            self._loaded_state = self._controller.load_state()
            self._set_controls_from_state(self._loaded_state)
            return True
        return False

    def _on_reset_panel(self) -> None:
        new_state = self._controller.reset_panel_state()
        self._set_controls_from_state(new_state)

    def _set_controls_from_state(self, state: SettingsViewState) -> None:
        self._launch_at_startup.setChecked(state.launch_at_startup)
        self._start_minimized.setChecked(state.start_minimized_to_tray)
        self._always_on_top.setChecked(state.always_on_top)
        self._auto_hide.setChecked(state.auto_hide_sidebar)
        self._reveal_on_hover.setChecked(state.reveal_on_hover)
        self._hide_delay.setValue(state.hide_delay_ms)
        self._panel_width.setValue(state.panel_width)

        dock_idx = self._dock_side.findData(state.dock_side)
        self._dock_side.setCurrentIndex(max(0, dock_idx))

    def _read_state_from_controls(self) -> SettingsViewState:
        dock_side = self._dock_side.currentData()
        selected_side = dock_side if isinstance(dock_side, DockSide) else DockSide.RIGHT
        return SettingsViewState(
            launch_at_startup=self._launch_at_startup.isChecked(),
            start_minimized_to_tray=self._start_minimized.isChecked(),
            always_on_top=self._always_on_top.isChecked(),
            auto_hide_sidebar=self._auto_hide.isChecked(),
            reveal_on_hover=self._reveal_on_hover.isChecked(),
            hide_delay_ms=self._hide_delay.value(),
            dock_side=selected_side,
            panel_width=self._panel_width.value(),
        )
