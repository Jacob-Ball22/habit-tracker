"""Data models for Habit Tracker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Category:
    """Represents a habit category."""

    id: int
    name: str
    color: str = "#4CAF50"


@dataclass(frozen=True)
class Habit:
    """Represents a habit."""

    id: int
    name: str
    description: Optional[str]
    category_id: int
    created_at: date
    is_active: bool = True


@dataclass(frozen=True)
class Completion:
    """Represents a habit completion on a date."""

    id: int
    habit_id: int
    completed_date: date
