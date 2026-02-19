"""Weekly bar chart widget showing 52 weeks of completion counts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Set

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QToolTip, QWidget

# Match heatmap dimensions exactly so the two widgets are interchangeable
BAR_WIDTH = 11
BAR_GAP = 2
BAR_STEP = BAR_WIDTH + BAR_GAP
WEEKS = 52
MAX_BAR_HEIGHT = 77  # 7 rows * 13px (CELL_STEP) - 2px gap ≈ heatmap height

_COLOR_ZERO = QColor("#ebedf0")
_COLOR_LOW = QColor("#9be9a8")    # 1–2 completions
_COLOR_MID = QColor("#40c463")    # 3–5 completions
_COLOR_HIGH = QColor("#216e39")   # 6–7 completions


def _bar_color(count: int) -> QColor:
    if count == 0:
        return _COLOR_ZERO
    if count <= 2:
        return _COLOR_LOW
    if count <= 5:
        return _COLOR_MID
    return _COLOR_HIGH


class BarChartWidget(QWidget):
    """52-week bar chart drawn with QPainter. Each bar = completions in that week."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._completion_dates: Set[date] = set()
        self._today = date.today()
        self._week_data: list[tuple[date, int]] = []  # (week_start, count)
        self._bars: list[tuple[QRect, date, int]] = []  # (rect, week_start, count)
        self._compute_bars()
        self.setMouseTracking(True)
        self.setFixedSize(self.sizeHint())

    def set_completions(self, completion_dates: Set[date]) -> None:
        """Replace the completion set and trigger a repaint."""

        self._completion_dates = completion_dates
        self._compute_bars()
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(WEEKS * BAR_STEP - BAR_GAP + 2, MAX_BAR_HEIGHT + 2)

    def _compute_bars(self) -> None:
        """Pre-compute bar rects and per-week counts."""

        today = self._today
        # Start of week 0: 52 weeks ago, snapped to Monday
        week0_start = today - timedelta(weeks=WEEKS - 1)
        week0_start -= timedelta(days=week0_start.weekday())  # snap to Monday

        self._bars = []
        for w in range(WEEKS):
            ws = week0_start + timedelta(weeks=w)
            count = sum(
                1 for d in range(7)
                if ws + timedelta(days=d) in self._completion_dates
            )
            bar_h = int(count / 7 * MAX_BAR_HEIGHT) if count > 0 else 0
            x = w * BAR_STEP
            y = MAX_BAR_HEIGHT - bar_h
            rect = QRect(x, y, BAR_WIDTH, bar_h if bar_h > 0 else MAX_BAR_HEIGHT)
            self._bars.append((rect, ws, count))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)

        for rect, ws, count in self._bars:
            if count == 0:
                # Draw a thin empty bar at the bottom
                empty_rect = QRect(rect.x(), MAX_BAR_HEIGHT - 2, BAR_WIDTH, 2)
                painter.fillRect(empty_rect, _COLOR_ZERO)
            else:
                painter.fillRect(rect, _bar_color(count))

        painter.end()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.pos()
        for rect, ws, count in self._bars:
            # Check x range for this bar (full height column)
            if rect.x() <= pos.x() < rect.x() + BAR_WIDTH:
                week_end = ws + timedelta(days=6)
                tip = (
                    f"Week of {ws.strftime('%b %d')} – {week_end.strftime('%b %d %Y')}"
                    f"  —  {count}/7 completed"
                )
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()
