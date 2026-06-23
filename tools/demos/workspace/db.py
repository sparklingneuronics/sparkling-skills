"""Tiny DB helper used by the migration scripts."""
import sqlite3


def connect(path: str = "app.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
