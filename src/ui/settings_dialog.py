"""Settings dialog for appearance preferences."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ..db import export_to_csv


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

        # ── Appearance ───────────────────────────────────────────────────────
        appearance_lbl = QLabel("Appearance")
        appearance_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(appearance_lbl)

        self._light_radio = QRadioButton("Default (Light)")
        self._dark_radio = QRadioButton("Dark Mode")

        if current_theme == "dark":
            self._dark_radio.setChecked(True)
        else:
            self._light_radio.setChecked(True)

        layout.addWidget(self._light_radio)
        layout.addWidget(self._dark_radio)
        layout.addSpacing(12)

        # ── Data export ──────────────────────────────────────────────────────
        data_lbl = QLabel("Data")
        data_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(data_lbl)

        export_btn = QPushButton("Export Data to CSV…")
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn)

        layout.addSpacing(8)

        # ── Buttons ──────────────────────────────────────────────────────────
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

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Habit Data", "habit_data.csv", "CSV Files (*.csv)"
        )
        if path:
            export_to_csv(path)
            QMessageBox.information(
                self, "Export Complete", f"Data exported to:\n{path}"
            )
