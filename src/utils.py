"""Utility helpers for dates and formatting."""

from __future__ import annotations

from datetime import date


def today() -> date:
    """Return today's local date."""

    return date.today()
