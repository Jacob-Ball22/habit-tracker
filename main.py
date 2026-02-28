"""Habit Tracker application entry point."""

import os
from pathlib import Path

# Fix Qt platform plugin path for Anaconda/venv environments on macOS.
# Must run before any PyQt6 import.
try:
    import PyQt6 as _pyqt6
    _platforms = Path(_pyqt6.__file__).parent / "Qt6" / "plugins" / "platforms"
    if _platforms.exists():
        # Point directly at the platforms directory (not the parent plugins dir).
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(_platforms)
        # Also override QT_PLUGIN_PATH so Anaconda's Qt5 plugins don't intercept.
        _plugins = _platforms.parent
        os.environ["QT_PLUGIN_PATH"] = str(_plugins)
except ImportError:
    pass

from src.ui.main_window import launch_app  # noqa: E402

if __name__ == "__main__":
    launch_app()
