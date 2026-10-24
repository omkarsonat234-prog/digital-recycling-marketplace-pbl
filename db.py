"""Database helpers (SQLite)."""
import sqlite3

STATUSES = ("Pending", "Approved", "Rejected", "Needs Correction")

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT    NOT NULL,
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    condition   TEXT    NOT NULL,
    description TEXT    NOT NULL,
    price       REAL    NOT NULL CHECK (price > 0),
    status      TEXT    NOT NULL DEFAULT 'Pending',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def add_listing(db_path, category, quantity, condition, description, price):
    """Insert a new listing with status Pending and return its id."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO listings (category, quantity, condition, description, price, status) "
            "VALUES (?, ?, ?, ?, ?, 'Pending')",
            (category, quantity, condition, description, price),
        )
        return cur.lastrowid


def get_all_listings(db_path):
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM listings ORDER BY id DESC").fetchall()
