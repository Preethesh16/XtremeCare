# database.py — SQLite helpers for XtremeCare
# Compatible with Python 3.14 (sqlite3 is stdlib, no version issues)

import sqlite3
from datetime import date
from config import DB_PATH


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS dose_logs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     TEXT    NOT NULL,
            session        TEXT    NOT NULL,
            status         TEXT    NOT NULL,
            dispensed_at   TEXT,
            verified_at    TEXT,
            delay_seconds  INTEGER,
            date           TEXT    NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS verification_events (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     TEXT    NOT NULL,
            face_confirmed INTEGER NOT NULL,
            hand_detected  INTEGER NOT NULL,
            verified       INTEGER NOT NULL,
            timestamp      TEXT    NOT NULL,
            session        TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables ready.")


def _fetchone_as_dict(conn: sqlite3.Connection, table: str,
                      row_id: int) -> dict:
    conn.row_factory = sqlite3.Row
    c   = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
    row = c.fetchone()
    return dict(row) if row else {}


def log_verification(patient_id: str, session: str, verified: bool,
                     face_confirmed: bool, hand_detected: bool) -> dict:
    """Insert a verification event and return it as a dict."""
    from utils import get_timestamp
    ts   = get_timestamp()
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        """INSERT INTO verification_events
           (patient_id, face_confirmed, hand_detected, verified, timestamp, session)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (patient_id, int(face_confirmed), int(hand_detected),
         int(verified), ts, session),
    )
    conn.commit()
    row_id = c.lastrowid
    result = _fetchone_as_dict(conn, "verification_events", row_id)
    conn.close()
    return result


def log_dose(patient_id: str, session: str, status: str,
             dispensed_at: str, verified_at: str,
             delay_seconds: int) -> dict:
    """Insert a dose log entry and return it as a dict."""
    today = date.today().isoformat()
    conn  = sqlite3.connect(DB_PATH)
    c     = conn.cursor()
    c.execute(
        """INSERT INTO dose_logs
           (patient_id, session, status, dispensed_at, verified_at,
            delay_seconds, date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, session, status, dispensed_at, verified_at,
         delay_seconds, today),
    )
    conn.commit()
    row_id = c.lastrowid
    result = _fetchone_as_dict(conn, "dose_logs", row_id)
    conn.close()
    return result


def get_today_logs() -> list[dict]:
    """Return all dose_logs rows for today as a list of dicts."""
    today = date.today().isoformat()
    conn  = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c     = conn.cursor()
    c.execute("SELECT * FROM dose_logs WHERE date = ?", (today,))
    rows  = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows
