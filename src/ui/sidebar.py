"""Sidebar with Focus Area filter tabs."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QStyleOptionButton,
    QVBoxLayout,
    QWidget,
)

from ..db import create_category, list_categories
from .dialogs import CategoryDialog


class _SidebarActionRow(QWidget):
    """A label + '+' button row with hover highlight, used for sidebar actions."""

    action_clicked = pyqtSignal()

    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("focusHeader")
        self.setProperty("hovered", False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 2, 4)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setObjectName("focusHeaderLabel")

        plus_btn = QPushButton("+")
        plus_btn.setObjectName("focusPlusBtn")
        plus_btn.setFixedSize(20, 20)
        plus_btn.clicked.connect(self.action_clicked)

        layout.addWidget(lbl, 1)
        layout.addWidget(plus_btn)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._set_hovered(False)
        super().leaveEvent(event)

    def _set_hovered(self, hovered: bool) -> None:
        self.setProperty("hovered", hovered)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class _WordWrapButton(QPushButton):
    """QPushButton that wraps long label text over multiple lines."""

    _H_PAD = 24
    _V_PAD = 10

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        w = self.width() if self.width() > 0 else 132
        rect = fm.boundingRect(
            QRect(0, 0, max(w - self._H_PAD, 1), 10000),
            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignHCenter,
            self.text(),
        )
        return QSize(w, rect.height() + self._V_PAD)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.updateGeometry()

    def paintEvent(self, event) -> None:  # noqa: N802
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter = QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_PushButtonBevel, opt, painter, self)
        text_rect = self.style().subElementRect(
            QStyle.SubElement.SE_PushButtonContents, opt, self
        )
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.text(),
        )
        painter.end()


class Sidebar(QWidget):
    """Left sidebar listing Focus Area filter buttons."""

    category_selected = pyqtSignal(object)  # int | None
    add_habit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(168)
        self.setObjectName("sidebar")
        self._active: int | None = None
        self._buttons: dict[int | None, _WordWrapButton] = {}
        self._border_color = "#000000"

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 12, 12, 12)
        self._layout.setSpacing(6)

        self._add_habit_row = _SidebarActionRow("Add Habit")
        self._add_habit_row.action_clicked.connect(self.add_habit_requested)

        self._focus_header = _SidebarActionRow("Focus Areas")
        self._focus_header.action_clicked.connect(self._add_focus_area)

        self._rebuild()

    def set_border_color(self, color: str) -> None:
        """Update the sidebar divider line color (call when theme changes)."""
        self._border_color = color
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw stylesheet background + dividing line on the right edge."""
        painter = QPainter(self)
        # Draw the stylesheet background (required for QWidget subclasses
        # that override paintEvent — without this, background-color is ignored).
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        # Draw the divider line
        pen = QPen(QColor(self._border_color))
        pen.setWidth(1)
        painter.setPen(pen)
        x = self.width() - 1
        painter.drawLine(x, 0, x, self.height())
        painter.end()

    # ── Public ──────────────────────────────────────────────────────────────

    def rebuild(self) -> None:
        """Rebuild the Focus Area list (call after external changes)."""
        self._rebuild()

    # ── Private ─────────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        """Clear all widgets and recreate buttons."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None and w not in (self._focus_header, self._add_habit_row):
                w.deleteLater()

        self._buttons.clear()

        all_btn = self._build_button("All", None)
        all_btn.setChecked(self._active is None)
        self._layout.addWidget(all_btn)

        self._layout.addWidget(self._add_habit_row)
        self._layout.addWidget(self._focus_header)

        for cat in list_categories():
            btn = self._build_button(cat.name, cat.id)
            btn.setChecked(self._active == cat.id)
            self._layout.addWidget(btn)

        self._layout.addStretch(1)

    def _build_button(self, label: str, category_id: int | None) -> _WordWrapButton:
        btn = _WordWrapButton(label)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._select(category_id))
        self._buttons[category_id] = btn
        return btn

    def _select(self, category_id: int | None) -> None:
        self._active = category_id
        for cid, btn in self._buttons.items():
            btn.setChecked(cid == category_id)
        self.category_selected.emit(category_id)

    def _add_focus_area(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec() == CategoryDialog.DialogCode.Accepted:
            create_category(dlg.get_name())
            self._rebuild()
