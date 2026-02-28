"""Settings dialog for appearance preferences."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Dialog for configuring app settings (theme, etc.)."""

    theme_changed = pyqtSignal(str)

    def __init__(
        self, parent: Optional[QWidget] = None, current_theme: str = "light"
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(280)
        self._current = current_theme

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Appearance")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        self._light_radio = QRadioButton("Default (Light)")
        self._dark_radio = QRadioButton("Dark Mode")

        if current_theme == "dark":
            self._dark_radio.setChecked(True)
        else:
            self._light_radio.setChecked(True)

        layout.addWidget(self._light_radio)
        layout.addWidget(self._dark_radio)
        layout.addSpacing(8)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply(self) -> None:
        theme = "dark" if self._dark_radio.isChecked() else "light"
        if theme != self._current:
            self.theme_changed.emit(theme)
        self.accept()
