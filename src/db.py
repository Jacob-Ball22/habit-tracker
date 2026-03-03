"""SQLite database access layer for Habit Tracker."""

from __future__ import annotations

import csv
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
        # Migrate existing databases: add new columns if missing
        for col, defn in [
            ("sort_order", "INTEGER DEFAULT 0"),
            ("frequency", "TEXT DEFAULT 'daily'"),
            ("weekly_goal", "INTEGER DEFAULT 0"),
            ("monthly_goal", "INTEGER DEFAULT 0"),
        ]:
            try:
                conn.execute(f"ALTER TABLE habits ADD COLUMN {col} {defn};")
            except sqlite3.OperationalError:
                pass  # Column already exists


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


def _row_to_habit(row: sqlite3.Row) -> Habit:
    return Habit(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        category_id=row["category_id"],
        created_at=date.fromisoformat(row["created_at"]),
        is_active=bool(row["is_active"]),
        sort_order=row["sort_order"] if row["sort_order"] is not None else 0,
        frequency=row["frequency"] or "daily",
        weekly_goal=row["weekly_goal"] if row["weekly_goal"] is not None else 0,
        monthly_goal=row["monthly_goal"] if row["monthly_goal"] is not None else 0,
    )


def list_habits(category_id: Optional[int] = None) -> List[Habit]:
    """Return active habits, optionally filtered by category."""

    conditions = ["is_active = 1"]
    params: list[object] = []
    if category_id is not None:
        conditions.append("category_id = ?")
        params.append(category_id)

    where = " AND ".join(conditions)
    query = (
        f"SELECT id, name, description, category_id, created_at, is_active, sort_order, frequency, weekly_goal, monthly_goal "
        f"FROM habits WHERE {where} ORDER BY sort_order ASC, created_at DESC, name;"
    )
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_habit(row) for row in rows]


def list_archived_habits(category_id: Optional[int] = None) -> List[Habit]:
    """Return archived (inactive) habits, optionally filtered by category."""

    conditions = ["is_active = 0"]
    params: list[object] = []
    if category_id is not None:
        conditions.append("category_id = ?")
        params.append(category_id)

    where = " AND ".join(conditions)
    query = (
        f"SELECT id, name, description, category_id, created_at, is_active, sort_order, frequency, weekly_goal, monthly_goal "
        f"FROM habits WHERE {where} ORDER BY name;"
    )
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_habit(row) for row in rows]


def create_habit(
    name: str,
    description: Optional[str],
    category_id: Optional[int],
    frequency: str = "daily",
    weekly_goal: int = 0,
    monthly_goal: int = 0,
) -> Habit:
    """Create and return a new habit."""

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO habits (name, description, category_id, frequency, weekly_goal, monthly_goal) VALUES (?, ?, ?, ?, ?, ?);",
            (name, description, category_id, frequency, weekly_goal, monthly_goal),
        )
        habit_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, name, description, category_id, created_at, is_active, sort_order, frequency, weekly_goal, monthly_goal "
            "FROM habits WHERE id = ?;",
            (habit_id,),
        ).fetchone()
    return _row_to_habit(row)


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
    category_id: Optional[int],
    frequency: str = "daily",
    weekly_goal: int = 0,
    monthly_goal: int = 0,
) -> None:
    """Update name, description, category, and frequency for an existing habit."""

    with get_connection() as conn:
        conn.execute(
            "UPDATE habits SET name = ?, description = ?, category_id = ?, frequency = ?, weekly_goal = ?, monthly_goal = ? WHERE id = ?;",
            (name, description, category_id, frequency, weekly_goal, monthly_goal, habit_id),
        )


def archive_habit(habit_id: int) -> None:
    """Soft-delete a habit by marking it inactive (preserves history)."""

    with get_connection() as conn:
        conn.execute("UPDATE habits SET is_active = 0 WHERE id = ?;", (habit_id,))


def restore_habit(habit_id: int) -> None:
    """Restore an archived habit back to active."""

    with get_connection() as conn:
        conn.execute("UPDATE habits SET is_active = 1 WHERE id = ?;", (habit_id,))


def delete_habit(habit_id: int) -> None:
    """Permanently delete a habit and all its completion records."""

    with get_connection() as conn:
        conn.execute("DELETE FROM completions WHERE habit_id = ?;", (habit_id,))
        conn.execute("DELETE FROM habits WHERE id = ?;", (habit_id,))


def update_sort_orders(ordered_ids: list[int]) -> None:
    """Persist a new display order for habits given as an ordered list of IDs."""

    with get_connection() as conn:
        for i, habit_id in enumerate(ordered_ids):
            conn.execute("UPDATE habits SET sort_order = ? WHERE id = ?;", (i, habit_id))


def export_to_csv(filepath: str) -> None:
    """Export all habit completion history to a CSV file."""

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                h.name        AS habit_name,
                c.name        AS focus_area,
                co.completed_date
            FROM habits h
            LEFT JOIN categories c ON c.id = h.category_id
            LEFT JOIN completions co ON co.habit_id = h.id
            ORDER BY h.name, co.completed_date;
            """
        ).fetchall()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Habit Name", "Focus Area", "Completed Date"])
        for row in rows:
            if row["completed_date"]:
                writer.writerow([row["habit_name"], row["focus_area"], row["completed_date"]])
