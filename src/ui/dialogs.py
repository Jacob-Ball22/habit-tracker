"""Dialogs for adding and editing habits and categories."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..db import list_categories
from ..models import Habit


class HabitDialog(QDialog):
    """Dialog for adding or editing a habit."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        habit: Optional[Habit] = None,
    ) -> None:
        super().__init__(parent)
        self._habit = habit
        self.setWindowTitle("Edit Habit" if habit else "Add Habit")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        self._category_combo = QComboBox()

        self._categories = list_categories()
        for cat in self._categories:
            self._category_combo.addItem(cat.name, cat.id)

        if not self._categories:
            form.addRow(QLabel("No Focus Areas found. Add a Focus Area first."))

        form.addRow("Name *", self._name_edit)
        form.addRow("Description", self._desc_edit)
        form.addRow("Focus Area *", self._category_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if habit:
            self._name_edit.setText(habit.name)
            self._desc_edit.setPlainText(habit.description or "")
            idx = self._category_combo.findData(habit.category_id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)

    def _validate_and_accept(self) -> None:
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Habit name is required.")
            return
        if not self._categories:
            QMessageBox.warning(self, "Validation Error", "Please add a Focus Area first.")
            return
        self.accept()

    def get_values(self) -> tuple[str, Optional[str], int]:
        """Return (name, description, category_id)."""

        name = self._name_edit.text().strip()
        desc = self._desc_edit.toPlainText().strip() or None
        category_id: int = self._category_combo.currentData()
        return name, desc, category_id


class CategoryDialog(QDialog):
    """Dialog for adding a new Focus Area."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Focus Area")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        form.addRow("Name *", self._name_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Focus Area name is required.")
            return
        self.accept()

    def get_name(self) -> str:
        """Return the entered category name."""

        return self._name_edit.text().strip()
