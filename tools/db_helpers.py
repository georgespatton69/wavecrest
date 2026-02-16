"""
Shared database utility functions used by all Wavecrest tools.

Functions:
    get_connection() -> sqlite3.Connection
    execute_query(sql, params) -> list[dict]
    insert_row(table, data_dict) -> int
    update_row(table, row_id, data_dict) -> bool
    delete_row(table, row_id) -> bool
"""

import sqlite3
import os

DB_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "wavecrest.db"),
)


def get_connection():
    """Get a connection to the Wavecrest SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_query(sql, params=None):
    """Execute a query and return results as a list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params or [])
        if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("WITH"):
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def insert_row(table, data):
    """Insert a row into a table. Returns the new row ID."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    conn = get_connection()
    try:
        cursor = conn.execute(sql, list(data.values()))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_row(table, row_id, data):
    """Update a row by ID. Returns True if a row was updated."""
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    sql = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    conn = get_connection()
    try:
        cursor = conn.execute(sql, list(data.values()) + [row_id])
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_row(table, row_id):
    """Delete a row by ID. Returns True if a row was deleted."""
    sql = f"DELETE FROM {table} WHERE id = ?"
    conn = get_connection()
    try:
        cursor = conn.execute(sql, [row_id])
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
