"""Main panel showing habits with heatmaps."""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta
from typing import Optional

from PyQt6.QtCore import QByteArray, QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..db import (
    archive_habit,
    create_habit,
    delete_habit,
    get_completed_today,
    list_archived_habits,
    list_completions,
    list_habits,
    restore_habit,
    toggle_completion,
    update_habit,
    update_sort_orders,
)
from ..models import Habit
from ..utils import today
from .bar_chart_widget import BarChartWidget
from .dialogs import HabitDialog
from .heatmap_widget import HeatmapWidget

_MIME_HABIT = "application/x-habit-id"


def _is_scheduled_today(frequency: str) -> bool:
    """Return True if this habit is scheduled for today."""
    if frequency == "daily":
        return True
    try:
        return date.today().weekday() in [int(d) for d in frequency.split(",")]
    except ValueError:
        return True


class HabitCard(QFrame):
    """Widget representing a single habit with its heatmap."""

    deleted = pyqtSignal(int)
    changed = pyqtSignal()
    archived = pyqtSignal(int)
    restored = pyqtSignal(int)
    reorder_requested = pyqtSignal(int, int)  # (source_habit_id, target_habit_id)

    def __init__(
        self,
        habit: Habit,
        archived_mode: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._habit = habit
        self._archived_mode = archived_mode
        self._drag_start_pos = None
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setAcceptDrops(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(8)

        # ── Top row: drag handle + name + action buttons ─────────────────────
        top = QHBoxLayout()

        if not archived_mode:
            self._handle = QLabel("⠿")
            self._handle.setCursor(Qt.CursorShape.SizeVerCursor)
            self._handle.setObjectName("dragHandle")
            top.addWidget(self._handle)

        self._name_label = QLabel()
        self._name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        top.addWidget(self._name_label, 1)

        if not archived_mode:
            self._complete_btn = QPushButton()
            self._complete_btn.setCheckable(True)
            self._complete_btn.setMinimumWidth(160)
            self._complete_btn.clicked.connect(self._toggle_today)
            top.addWidget(self._complete_btn)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(self._edit)
            top.addWidget(edit_btn)

            archive_btn = QPushButton("Archive")
            archive_btn.setObjectName("archiveBtn")
            archive_btn.setMinimumWidth(70)
            archive_btn.clicked.connect(self._archive)
            top.addWidget(archive_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setMinimumWidth(60)
            delete_btn.clicked.connect(self._delete)
            top.addWidget(delete_btn)
        else:
            restore_btn = QPushButton("Restore")
            restore_btn.setObjectName("restoreBtn")
            restore_btn.setMinimumWidth(80)
            restore_btn.clicked.connect(self._restore)
            top.addWidget(restore_btn)

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
        stats_row = QHBoxLayout()
        self._count_label = QLabel()
        self._count_label.setStyleSheet("color: #888; font-size: 12px;")
        stats_row.addWidget(self._count_label, 1)

        if not archived_mode:
            self._chart_btn = QPushButton("📊")
            self._chart_btn.setObjectName("chartToggleBtn")
            self._chart_btn.setFixedSize(28, 22)
            self._chart_btn.setToolTip("Toggle bar chart / heatmap")
            self._chart_btn.clicked.connect(self._toggle_chart)
            stats_row.addWidget(self._chart_btn)

        outer.addLayout(stats_row)

        # ── Chart stack (heatmap / bar chart) ────────────────────────────────
        self._stack = QStackedWidget()
        self._heatmap = HeatmapWidget()
        self._bar_chart = BarChartWidget()
        self._stack.addWidget(self._heatmap)   # index 0
        self._stack.addWidget(self._bar_chart)  # index 1
        outer.addWidget(self._stack)

        self._refresh_data()

    # ── Public ───────────────────────────────────────────────────────────────

    def _refresh_data(self) -> None:
        """Reload completions from DB and update all display elements."""

        completions = list_completions(self._habit.id)
        dates = {c.completed_date for c in completions}
        self._heatmap.set_completions(dates)
        self._bar_chart.set_completions(dates)

        # Streak
        streak = 0
        d = today()
        while d in dates:
            streak += 1
            d -= timedelta(days=1)

        # This week (Mon → today)
        week_start = today() - timedelta(days=today().weekday())
        days_this_week = today().weekday() + 1
        done_week = sum(
            1 for i in range(days_this_week)
            if week_start + timedelta(days=i) in dates
        )

        # This month
        first_of_month = today().replace(day=1)
        days_this_month = today().day
        done_month = sum(
            1 for i in range(days_this_month)
            if first_of_month + timedelta(days=i) in dates
        )

        self._count_label.setText(
            f"Total: {len(dates)}  |  Streak: {streak}d  |  "
            f"Week: {done_week}/{days_this_week}  |  Month: {done_month}/{days_this_month}"
        )

        if not self._archived_mode:
            is_done_today = today() in dates
            self._complete_btn.setChecked(is_done_today)
            if is_done_today:
                self._complete_btn.setText("Completed Today ✓")
                self._complete_btn.setStyleSheet("background-color: #2ea043; color: white;")
            else:
                self._complete_btn.setText("Mark Complete Today")
                self._complete_btn.setStyleSheet("")

        self._name_label.setText(self._habit.name)

    # ── Private actions ──────────────────────────────────────────────────────

    def _toggle_today(self) -> None:
        toggle_completion(self._habit.id, today().isoformat())
        self._refresh_data()
        self.changed.emit()

    def _toggle_chart(self) -> None:
        new_idx = 1 if self._stack.currentIndex() == 0 else 0
        self._stack.setCurrentIndex(new_idx)

    def _edit(self) -> None:
        dlg = HabitDialog(self, self._habit)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc, cat_id, frequency = dlg.get_values()
            update_habit(self._habit.id, name, desc, cat_id, frequency)
            self._habit = dataclasses.replace(
                self._habit,
                name=name,
                description=desc,
                category_id=cat_id,
                frequency=frequency,
            )
            self._refresh_data()
            self.changed.emit()

    def _archive(self) -> None:
        reply = QMessageBox.question(
            self,
            "Archive Habit",
            f"Archive '{self._habit.name}'?\nIt will be hidden but all history is preserved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            archive_habit(self._habit.id)
            self.archived.emit(self._habit.id)

    def _restore(self) -> None:
        restore_habit(self._habit.id)
        self.restored.emit(self._habit.id)

    def _delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Habit",
            f"Delete '{self._habit.name}'? This will permanently remove all completion history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_habit(self._habit.id)
            self.deleted.emit(self._habit.id)

    # ── Drag and drop ────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            not self._archived_mode
            and event.button() == Qt.MouseButton.LeftButton
            and hasattr(self, "_handle")
            and self._handle.geometry().contains(event.pos())
        ):
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if (
            self._drag_start_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            dist = (event.pos() - self._drag_start_pos).manhattanLength()
            if dist >= QApplication.startDragDistance():
                self._drag_start_pos = None
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(_MIME_HABIT, QByteArray(str(self._habit.id).encode()))
                drag.setMimeData(mime)
                pixmap = self.grab()
                drag.setPixmap(pixmap.scaledToWidth(self.width()))
                drag.setHotSpot(event.pos())
                drag.exec(Qt.DropAction.MoveAction)
                return  # card may have been deleted by refresh() during the drop
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasFormat(_MIME_HABIT):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasFormat(_MIME_HABIT):
            source_id = int(bytes(event.mimeData().data(_MIME_HABIT)).decode())
            if source_id != self._habit.id:
                self.reorder_requested.emit(source_id, self._habit.id)
            event.acceptProposedAction()


class HabitView(QWidget):
    """Scrollable list of HabitCards filtered by category."""

    habit_changed = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._category_id: Optional[int] = None
        self._archived_mode = False
        self._incomplete_habits: list[Habit] = []

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

    # ── Public ───────────────────────────────────────────────────────────────

    def set_category_filter(self, category_id: Optional[int]) -> None:
        """Switch to a different category and refresh."""
        self._category_id = category_id
        self._archived_mode = False
        self._title.setText("Habits")
        self.refresh()

    def show_archived_view(self) -> None:
        """Show archived habits."""
        self._archived_mode = True
        self._title.setText("Archived Habits")
        self.refresh()

    def show_active_view(self) -> None:
        """Return to active habits view."""
        self._archived_mode = False
        self._title.setText("Habits")
        self.refresh()

    def refresh(self) -> None:
        """Clear and rebuild the habit card list."""

        # Remove all existing cards / headers / dividers
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._archived_mode:
            self._refresh_archived()
        else:
            self._refresh_active()

    def show_add_habit_dialog(self) -> None:
        dlg = HabitDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc, cat_id, frequency = dlg.get_values()
            create_habit(name, desc, cat_id, frequency)
            self.refresh()
            self.habit_changed.emit()

    # ── Private ──────────────────────────────────────────────────────────────

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionHeader")
        return lbl

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sectionDivider")
        return line

    def _insert(self, widget: QWidget) -> None:
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, widget)

    def _add_card(self, habit: Habit, archived_mode: bool = False) -> None:
        card = HabitCard(habit, archived_mode=archived_mode)
        card.deleted.connect(lambda _: self.refresh())
        card.changed.connect(self.refresh)
        card.changed.connect(self.habit_changed.emit)
        card.archived.connect(lambda _: self.refresh())
        card.restored.connect(lambda _: self.refresh())
        card.reorder_requested.connect(self._on_reorder)
        self._insert(card)

    def _refresh_active(self) -> None:
        habits = list_habits(self._category_id)

        if not habits:
            self._scroll.hide()
            self._placeholder.show()
            return

        self._placeholder.hide()
        self._scroll.show()

        completed_ids = get_completed_today()
        incomplete = [h for h in habits if h.id not in completed_ids and _is_scheduled_today(h.frequency)]
        completed = [h for h in habits if h.id in completed_ids]
        not_scheduled = [
            h for h in habits
            if h.id not in completed_ids and not _is_scheduled_today(h.frequency)
        ]

        self._incomplete_habits = incomplete

        sections_shown = 0

        if incomplete:
            self._insert(self._section_header("STILL NEED TO COMPLETE"))
            for habit in incomplete:
                self._add_card(habit)
            sections_shown += 1

        if completed:
            if sections_shown:
                self._insert(self._divider())
            self._insert(self._section_header("COMPLETED TODAY"))
            for habit in completed:
                self._add_card(habit)
            sections_shown += 1

        if not_scheduled:
            if sections_shown:
                self._insert(self._divider())
            self._insert(self._section_header("NOT SCHEDULED TODAY"))
            for habit in not_scheduled:
                self._add_card(habit)

    def _refresh_archived(self) -> None:
        habits = list_archived_habits(self._category_id)

        if not habits:
            self._scroll.hide()
            self._placeholder.setText("No archived habits.")
            self._placeholder.show()
            return

        self._placeholder.hide()
        self._scroll.show()

        for habit in habits:
            self._add_card(habit, archived_mode=True)

        # Reset placeholder text for when user returns to active view
        self._placeholder.setText("No habits yet. Click '+ Add Habit' to get started.")

    def _on_reorder(self, source_id: int, target_id: int) -> None:
        """Move source habit to target habit's position and persist new order."""
        ids = [h.id for h in self._incomplete_habits]
        if source_id not in ids or target_id not in ids:
            return
        src_idx = ids.index(source_id)
        tgt_idx = ids.index(target_id)
        ids.insert(tgt_idx, ids.pop(src_idx))
        update_sort_orders(ids)
        self.refresh()
