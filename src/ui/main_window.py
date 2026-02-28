"""Main window for Habit Tracker."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from ..db import init_db
from .habit_view import HabitView
from .settings_dialog import SettingsDialog
from .sidebar import Sidebar

_LIGHT_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #1a1a1a;
    font-family: -apple-system, "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background-color: #c0c0c0;
}
QWidget#sidebar QLabel {
    background-color: transparent;
}

QFrame[frameShape="1"] {
    border: 1px solid #c8ccd0;
    border-radius: 6px;
    background-color: #ffffff;
}

/* ── All buttons: dark by default ── */
QPushButton {
    padding: 5px 12px;
    border: 1px solid #57606a;
    border-radius: 6px;
    background-color: #24292f;
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #32383f;
    border-color: #57606a;
}
QPushButton:checked {
    background-color: #0969da;
    color: #ffffff;
    border-color: #0969da;
}
QPushButton:pressed {
    background-color: #1c2128;
}

/* ── Focus Areas header ── */
QWidget#focusHeader {
    border-radius: 4px;
}
QWidget#focusHeader[hovered="true"] {
    background-color: #a8a8a8;
}
QPushButton#focusPlusBtn {
    background-color: transparent;
    border: none;
    color: #57606a;
    font-size: 16px;
    padding: 0px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    font-weight: bold;
}
QPushButton#focusPlusBtn:hover {
    color: #24292f;
}

/* ── Settings button ── */
QPushButton#settingsBtn {
    background-color: transparent;
    border: none;
    color: #57606a;
    font-size: 22px;
    padding: 2px 8px;
}
QPushButton#settingsBtn:hover {
    background-color: #e8eaed;
    border-radius: 6px;
}

/* ── Radio buttons ── */
QRadioButton {
    color: #1a1a1a;
    background: transparent;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #57606a;
    background-color: #ffffff;
}
QRadioButton::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}
QRadioButton::indicator:hover {
    border-color: #0969da;
}

/* ── Dialog inputs ── */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #57606a;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #ffffff;
    color: #1a1a1a;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #0969da;
}
QComboBox::drop-down {
    border: none;
}
QLabel {
    color: #1a1a1a;
}

/* ── Dialog button box ── */
QDialogButtonBox QPushButton {
    min-width: 72px;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #c8ccd0;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Message boxes ── */
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #1a1a1a;
    font-size: 13px;
}

"""

_DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background-color: #161b22;
}
QWidget#sidebar QLabel {
    background-color: transparent;
}

QFrame[frameShape="1"] {
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #161b22;
}

/* ── All buttons ── */
QPushButton {
    padding: 5px 12px;
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #21262d;
    color: #c9d1d9;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:checked {
    background-color: #1f6feb;
    color: #ffffff;
    border-color: #1f6feb;
}
QPushButton:pressed {
    background-color: #161b22;
}

/* ── Focus Areas header ── */
QWidget#focusHeader {
    border-radius: 4px;
}
QWidget#focusHeader[hovered="true"] {
    background-color: #21262d;
}
QPushButton#focusPlusBtn {
    background-color: transparent;
    border: none;
    color: #8b949e;
    font-size: 16px;
    padding: 0px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    font-weight: bold;
}
QPushButton#focusPlusBtn:hover {
    color: #e6edf3;
}

/* ── Settings button ── */
QPushButton#settingsBtn {
    background-color: transparent;
    border: none;
    color: #8b949e;
    font-size: 22px;
    padding: 2px 8px;
}
QPushButton#settingsBtn:hover {
    background-color: #21262d;
    border-radius: 6px;
}

/* ── Radio buttons ── */
QRadioButton {
    color: #e6edf3;
    background: transparent;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #8b949e;
    background-color: #161b22;
}
QRadioButton::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}
QRadioButton::indicator:hover {
    border-color: #1f6feb;
}

/* ── Dialog inputs ── */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #161b22;
    color: #e6edf3;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #1f6feb;
}
QComboBox::drop-down {
    border: none;
}
QLabel {
    color: #e6edf3;
}

/* ── Dialog button box ── */
QDialogButtonBox QPushButton {
    min-width: 72px;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Message boxes ── */
QMessageBox {
    background-color: #0d1117;
}
QMessageBox QLabel {
    color: #e6edf3;
    font-size: 13px;
}

"""


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self._theme = "light"
        self.setWindowTitle("Habit Tracker")
        self.setMinimumSize(1100, 700)

        root = QWidget(self)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.habit_view = HabitView()

        layout.addWidget(self.sidebar, 0)
        layout.addWidget(self.habit_view, 1)
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.sidebar.category_selected.connect(self.habit_view.set_category_filter)
        self.sidebar.add_habit_requested.connect(self.habit_view.show_add_habit_dialog)
        self.habit_view.settings_requested.connect(self._open_settings)

    def set_theme(self, theme: str) -> None:
        """Switch between 'light' and 'dark' themes."""
        self._theme = theme
        if theme == "dark":
            QApplication.instance().setStyleSheet(_DARK_STYLESHEET)
            self.sidebar.set_border_color("#30363d")
        else:
            QApplication.instance().setStyleSheet(_LIGHT_STYLESHEET)
            self.sidebar.set_border_color("#000000")

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self, current_theme=self._theme)
        dlg.theme_changed.connect(self.set_theme)
        dlg.exec()


def launch_app() -> None:
    """Initialize database and launch the Qt application."""

    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(_LIGHT_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
