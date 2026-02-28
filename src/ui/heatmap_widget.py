"""GitHub-style heatmap widget showing 52 weeks of daily completions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Set

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QToolTip, QWidget

CELL_SIZE = 11
CELL_GAP = 2
CELL_STEP = CELL_SIZE + CELL_GAP
WEEKS = 52

_COLOR_EMPTY = QColor("#ebedf0")
_COLOR_DONE = QColor("#9be9a8")
_COLOR_STREAK = QColor("#216e39")
_COLOR_TODAY_BORDER = QColor("#0969da")


class HeatmapWidget(QWidget):
    """52-week heatmap drawn with QPainter. Rows = Sun–Sat, columns = weeks."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._completion_dates: Set[date] = set()
        self._today = date.today()
        self._cells: list[tuple[QRect, date]] = []
        self._compute_cells()
        self.setMouseTracking(True)
        self.setFixedSize(self.sizeHint())

    def set_completions(self, completion_dates: Set[date]) -> None:
        """Replace the completion set and trigger a repaint."""

        self._completion_dates = completion_dates
        self.update()

    def _compute_cells(self) -> None:
        """Pre-compute (rect, date) pairs for every day in the grid."""

        today = self._today
        # Go back 52 weeks from today, then snap to the nearest previous Sunday.
        rough_start = today - timedelta(days=WEEKS * 7 - 1)
        # weekday(): Mon=0 … Sun=6 → convert so Sun=0, Mon=1, …, Sat=6
        start_offset = (rough_start.weekday() + 1) % 7
        start = rough_start - timedelta(days=start_offset)

        self._cells = []
        d = start
        while d <= today:
            col = (d - start).days // 7
            row = (d.weekday() + 1) % 7  # Sun=0, Sat=6
            rect = QRect(col * CELL_STEP, row * CELL_STEP, CELL_SIZE, CELL_SIZE)
            self._cells.append((rect, d))
            d += timedelta(days=1)

    def sizeHint(self) -> QSize:
        if not self._cells:
            return QSize(WEEKS * CELL_STEP, 7 * CELL_STEP)
        max_x = max(r.x() + r.width() for r, _ in self._cells)
        return QSize(max_x + 2, 7 * CELL_STEP - CELL_GAP + 2)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)

        for rect, d in self._cells:
            is_done = d in self._completion_dates
            is_today = d == self._today

            if is_done:
                prev = d - timedelta(days=1)
                color = _COLOR_STREAK if prev in self._completion_dates else _COLOR_DONE
            else:
                color = _COLOR_EMPTY

            painter.fillRect(rect, color)

            if is_today:
                painter.setPen(QPen(_COLOR_TODAY_BORDER, 1.5))
                painter.drawRect(rect)
            else:
                painter.setPen(Qt.PenStyle.NoPen)

        painter.end()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.pos()
        for rect, d in self._cells:
            if rect.contains(pos):
                status = "Completed" if d in self._completion_dates else "Not completed"
                tip = f"{d.strftime('%A, %b %d %Y')} — {status}"
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()
