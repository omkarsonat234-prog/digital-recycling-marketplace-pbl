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

CREATE TABLE IF NOT EXISTS decisions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    decision   TEXT    NOT NULL,
    reason     TEXT,
    decided_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
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


# ---------------- Module 2: Admin Listing Verification ----------------

def get_listing(db_path, listing_id):
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()


def get_listings_for_admin(db_path):
    """All submitted listings, Pending first (DRM-5)."""
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM listings "
            "ORDER BY CASE status WHEN 'Pending' THEN 0 ELSE 1 END, id DESC"
        ).fetchall()


def get_approved_listings(db_path):
    """Only approved listings for the public marketplace (DRM-7)."""
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM listings WHERE status = 'Approved' ORDER BY id DESC"
        ).fetchall()


def get_decisions(db_path, listing_id):
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM decisions WHERE listing_id = ? ORDER BY id DESC", (listing_id,)
        ).fetchall()


def record_decision(db_path, listing_id, new_status, reason):
    """Save the decision + reason and update the listing status (DRM-16).

    Only a Pending listing can be decided. Returns True if saved,
    False if the listing was not Pending (or does not exist).
    """
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE listings SET status = ? WHERE id = ? AND status = 'Pending'",
            (new_status, listing_id),
        )
        if cur.rowcount == 0:
            return False
        conn.execute(
            "INSERT INTO decisions (listing_id, decision, reason) VALUES (?, ?, ?)",
            (listing_id, new_status, reason),
        )
        return True
