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
    """Seller view: every listing plus the admin's latest reason (if any)."""
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT l.*, "
            "(SELECT d.reason FROM decisions d WHERE d.listing_id = l.id "
            " ORDER BY d.id DESC LIMIT 1) AS last_reason "
            "FROM listings l ORDER BY l.id DESC"
        ).fetchall()


def get_status_counts(db_path):
    """Number of listings per status, e.g. {'Pending': 2, 'Approved': 1, ...}."""
    counts = {status: 0 for status in STATUSES}
    with get_connection(db_path) as conn:
        for row in conn.execute("SELECT status, COUNT(*) AS n FROM listings GROUP BY status"):
            counts[row["status"]] = row["n"]
    return counts


def get_latest_reason(db_path, listing_id):
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT reason FROM decisions WHERE listing_id = ? ORDER BY id DESC LIMIT 1",
            (listing_id,),
        ).fetchone()
        return row["reason"] if row else None


def resubmit_listing(db_path, listing_id, category, quantity, condition, description, price):
    """Seller corrects a listing the admin returned. Status goes back to Pending.

    Only works while status is 'Needs Correction'. Returns True if updated.
    """
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE listings SET category = ?, quantity = ?, condition = ?, "
            "description = ?, price = ?, status = 'Pending' "
            "WHERE id = ? AND status = 'Needs Correction'",
            (category, quantity, condition, description, price, listing_id),
        )
        return cur.rowcount == 1


# ---------------- Module 2: Admin Listing Verification ----------------

def get_listing(db_path, listing_id):
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()


def get_listings_for_admin(db_path, status=None):
    """Submitted listings, Pending first (DRM-5). Optional status filter."""
    query = "SELECT * FROM listings "
    params = ()
    if status:
        query += "WHERE status = ? "
        params = (status,)
    query += "ORDER BY CASE status WHEN 'Pending' THEN 0 ELSE 1 END, id DESC"
    with get_connection(db_path) as conn:
        return conn.execute(query, params).fetchall()


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
