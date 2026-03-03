"""Dialogs for adding and editing habits and categories."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..db import list_categories
from ..models import Habit

_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _frequency_to_checked(frequency: str) -> list[bool]:
    """Convert a frequency string to a list of 7 booleans (Mon–Sun)."""
    if frequency == "daily":
        return [True] * 7
    try:
        scheduled = {int(d) for d in frequency.split(",")}
        return [i in scheduled for i in range(7)]
    except ValueError:
        return [True] * 7


def _checked_to_frequency(checked: list[bool]) -> str:
    """Convert 7 booleans to a frequency string."""
    if all(checked):
        return "daily"
    return ",".join(str(i) for i, c in enumerate(checked) if c)


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

        self._category_combo.addItem("No Focus Area", None)
        self._categories = list_categories()
        for cat in self._categories:
            self._category_combo.addItem(cat.name, cat.id)

        form.addRow("Name *", self._name_edit)
        form.addRow("Description", self._desc_edit)
        form.addRow("Focus Area", self._category_combo)

        # ── Scheduled days checkboxes ─────────────────────────────────────
        days_row = QHBoxLayout()
        days_row.setSpacing(6)
        self._day_checks: list[QCheckBox] = []
        initial_checked = _frequency_to_checked(habit.frequency if habit else "daily")
        for i, day in enumerate(_DAYS):
            cb = QCheckBox(day)
            cb.setChecked(initial_checked[i])
            self._day_checks.append(cb)
            days_row.addWidget(cb)
        days_row.addStretch(1)

        days_widget = QWidget()
        days_widget.setLayout(days_row)
        form.addRow("Scheduled Days", days_widget)

        # ── Weekly / monthly goals ────────────────────────────────────────
        self._weekly_goal = QSpinBox()
        self._weekly_goal.setRange(0, 7)
        self._weekly_goal.setSpecialValueText("Off")
        self._weekly_goal.setToolTip("0 = hide weekly stat; 1–7 = show with this as the goal")

        self._monthly_goal = QSpinBox()
        self._monthly_goal.setRange(0, 31)
        self._monthly_goal.setSpecialValueText("Off")
        self._monthly_goal.setToolTip("0 = hide monthly stat; 1–31 = show with this as the goal")

        goals_row = QHBoxLayout()
        goals_row.setSpacing(16)
        goals_row.addWidget(QLabel("Weekly:"))
        goals_row.addWidget(self._weekly_goal)
        goals_row.addWidget(QLabel("Monthly:"))
        goals_row.addWidget(self._monthly_goal)
        goals_row.addStretch(1)
        goals_widget = QWidget()
        goals_widget.setLayout(goals_row)
        form.addRow("Goals (0=Auto)", goals_widget)

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
            self._weekly_goal.setValue(habit.weekly_goal)
            self._monthly_goal.setValue(habit.monthly_goal)

    def _validate_and_accept(self) -> None:
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Habit name is required.")
            return
        if not any(cb.isChecked() for cb in self._day_checks):
            QMessageBox.warning(self, "Validation Error", "Select at least one scheduled day.")
            return
        self.accept()

    def get_values(self) -> tuple[str, Optional[str], Optional[int], str, int, int]:
        """Return (name, description, category_id, frequency, weekly_goal, monthly_goal)."""

        name = self._name_edit.text().strip()
        desc = self._desc_edit.toPlainText().strip() or None
        category_id: Optional[int] = self._category_combo.currentData()
        frequency = _checked_to_frequency([cb.isChecked() for cb in self._day_checks])
        return name, desc, category_id, frequency, self._weekly_goal.value(), self._monthly_goal.value()


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
