"""SQLite database access layer for Habit Tracker."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from datetime import date

from .models import Category, Completion, Habit

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "habits.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys enabled."""

    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create database tables if they do not exist."""

    schema = """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#4CAF50'
    );

    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category_id INTEGER REFERENCES categories(id),
        created_at DATE DEFAULT CURRENT_DATE,
        is_active BOOLEAN DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER REFERENCES habits(id),
        completed_date DATE NOT NULL,
        UNIQUE(habit_id, completed_date)
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)


def list_categories() -> List[Category]:
    """Return all categories."""

    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, color FROM categories ORDER BY name;").fetchall()
    return [Category(id=row["id"], name=row["name"], color=row["color"]) for row in rows]


def create_category(name: str, color: str = "#4CAF50") -> Category:
    """Create and return a new category."""

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?);",
            (name, color),
        )
        category_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, name, color FROM categories WHERE id = ?;",
            (category_id,),
        ).fetchone()
    return Category(id=row["id"], name=row["name"], color=row["color"])


def list_habits(category_id: Optional[int] = None) -> List[Habit]:
    """Return habits, optionally filtered by category."""

    query = "SELECT id, name, description, category_id, created_at, is_active FROM habits"
    params: Iterable[object] = ()
    if category_id is not None:
        query += " WHERE category_id = ?"
        params = (category_id,)
    query += " ORDER BY created_at DESC, name;"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        Habit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            category_id=row["category_id"],
            created_at=date.fromisoformat(row["created_at"]),
            is_active=bool(row["is_active"]),
        )
        for row in rows
    ]


def create_habit(
    name: str,
    description: Optional[str],
    category_id: int,
) -> Habit:
    """Create and return a new habit."""

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO habits (name, description, category_id) VALUES (?, ?, ?);",
            (name, description, category_id),
        )
        habit_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, name, description, category_id, created_at, is_active FROM habits WHERE id = ?;",
            (habit_id,),
        ).fetchone()
    return Habit(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        category_id=row["category_id"],
        created_at=date.fromisoformat(row["created_at"]),
        is_active=bool(row["is_active"]),
    )


def list_completions(habit_id: int) -> List[Completion]:
    """Return completions for a habit."""

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, habit_id, completed_date FROM completions WHERE habit_id = ? ORDER BY completed_date;",
            (habit_id,),
        ).fetchall()
    return [
        Completion(
            id=row["id"],
            habit_id=row["habit_id"],
            completed_date=date.fromisoformat(row["completed_date"]),
        )
        for row in rows
    ]


def get_completed_today() -> set[int]:
    """Return the set of habit IDs that have a completion entry for today."""

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT habit_id FROM completions WHERE completed_date = ?;",
            (date.today().isoformat(),),
        ).fetchall()
    return {row["habit_id"] for row in rows}


def toggle_completion(habit_id: int, completed_date: str) -> bool:
    """Toggle completion for a habit on a date. Returns True if now completed."""

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM completions WHERE habit_id = ? AND completed_date = ?;",
            (habit_id, completed_date),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM completions WHERE id = ?;", (existing["id"],))
            return False
        conn.execute(
            "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?);",
            (habit_id, completed_date),
        )
        return True


def update_habit(
    habit_id: int,
    name: str,
    description: Optional[str],
    category_id: int,
) -> None:
    """Update name, description, and category for an existing habit."""

    with get_connection() as conn:
        conn.execute(
            "UPDATE habits SET name = ?, description = ?, category_id = ? WHERE id = ?;",
            (name, description, category_id, habit_id),
        )


def delete_habit(habit_id: int) -> None:
    """Delete a habit and all its completion records."""

    with get_connection() as conn:
        conn.execute("DELETE FROM completions WHERE habit_id = ?;", (habit_id,))
        conn.execute("DELETE FROM habits WHERE id = ?;", (habit_id,))
