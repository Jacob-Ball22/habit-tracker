"""Database smoke tests."""

from src.db import init_db


def test_init_db_creates_schema() -> None:
    init_db()
