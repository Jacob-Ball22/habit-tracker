"""Main panel showing habits with heatmaps."""

from __future__ import annotations

import dataclasses
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..db import create_habit, delete_habit, list_completions, list_habits, toggle_completion, update_habit
from ..models import Habit
from ..utils import today
from .dialogs import HabitDialog
from .heatmap_widget import HeatmapWidget


class HabitCard(QFrame):
    """Widget representing a single habit with its heatmap."""

    deleted = pyqtSignal(int)
    changed = pyqtSignal()

    def __init__(self, habit: Habit, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._habit = habit
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(8)

        # ── Top row: name + action buttons ──────────────────────────────────
        top = QHBoxLayout()

        self._name_label = QLabel()
        self._name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        top.addWidget(self._name_label, 1)

        self._complete_btn = QPushButton()
        self._complete_btn.setCheckable(True)
        self._complete_btn.setMinimumWidth(160)
        self._complete_btn.clicked.connect(self._toggle_today)
        top.addWidget(self._complete_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(60)
        edit_btn.clicked.connect(self._edit)
        top.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setMinimumWidth(60)
        delete_btn.clicked.connect(self._delete)
        top.addWidget(delete_btn)

        outer.addLayout(top)

        # ── Description (optional) ───────────────────────────────────────────
        if habit.description:
            desc = QLabel(habit.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #666; font-size: 12px;")
            outer.addWidget(desc)

        # ── Stats row ────────────────────────────────────────────────────────
        self._count_label = QLabel()
        self._count_label.setStyleSheet("color: #888; font-size: 12px;")
        outer.addWidget(self._count_label)

        # ── Heatmap ──────────────────────────────────────────────────────────
        self._heatmap = HeatmapWidget()
        outer.addWidget(self._heatmap)

        self._refresh_data()

    def _refresh_data(self) -> None:
        """Reload completions from DB and update all display elements."""

        completions = list_completions(self._habit.id)
        dates = {c.completed_date for c in completions}
        self._heatmap.set_completions(dates)
        self._count_label.setText(f"Total completions: {len(dates)}")

        is_done_today = today() in dates
        self._complete_btn.setChecked(is_done_today)
        if is_done_today:
            self._complete_btn.setText("Completed Today ✓")
            self._complete_btn.setStyleSheet("background-color: #2ea043; color: white;")
        else:
            self._complete_btn.setText("Mark Complete Today")
            self._complete_btn.setStyleSheet("")
        self._name_label.setText(self._habit.name)

    def _toggle_today(self) -> None:
        toggle_completion(self._habit.id, today().isoformat())
        self._refresh_data()
        self.changed.emit()

    def _edit(self) -> None:
        dlg = HabitDialog(self, self._habit)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc, cat_id = dlg.get_values()
            update_habit(self._habit.id, name, desc, cat_id)
            self._habit = dataclasses.replace(
                self._habit, name=name, description=desc, category_id=cat_id
            )
            self._refresh_data()
            self.changed.emit()

    def _delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Habit",
            f"Delete '{self._habit.name}'? This will remove all completion history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_habit(self._habit.id)
            self.deleted.emit(self._habit.id)


class HabitView(QWidget):
    """Scrollable list of HabitCards filtered by category."""

    habit_changed = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._category_id: Optional[int] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 16, 16)
        root.setSpacing(8)

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        self._title = QLabel("Habits")
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(self._title, 1)

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.clicked.connect(self.settings_requested)
        header.addWidget(settings_btn)
        root.addLayout(header)

        # ── Scroll area containing habit cards ───────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 8, 0)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch(1)

        self._scroll.setWidget(self._cards_widget)
        root.addWidget(self._scroll, 1)

        # ── Empty state label ────────────────────────────────────────────────
        self._placeholder = QLabel("No habits yet. Click '+ Add Habit' to get started.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #999; font-size: 14px;")
        root.addWidget(self._placeholder)

        self.setLayout(root)
        self.refresh()

    def set_category_filter(self, category_id: Optional[int]) -> None:
        """Switch to a different category and refresh."""

        self._category_id = category_id
        self.refresh()

    def refresh(self) -> None:
        """Clear and rebuild the habit card list."""

        # Remove all cards (everything except the trailing stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        habits = list_habits(self._category_id)

        if habits:
            self._placeholder.hide()
            self._scroll.show()
            for habit in habits:
                card = HabitCard(habit)
                card.deleted.connect(lambda _: self.refresh())
                card.changed.connect(self.habit_changed.emit)
                self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
        else:
            self._scroll.hide()
            self._placeholder.show()

    def show_add_habit_dialog(self) -> None:
        dlg = HabitDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc, cat_id = dlg.get_values()
            create_habit(name, desc, cat_id)
            self.refresh()
            self.habit_changed.emit()
