import os
import sqlite3
from contextlib import contextmanager
from datetime import date

from plan import METRIC_KEYS, get_week_number

# On Amvera the persistent volume is mounted at /data
DB_PATH = os.environ.get("DB_PATH", "/data/coaching.db" if os.path.isdir("/data") else "coaching.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_log (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                date                    TEXT UNIQUE,
                week_number             INTEGER,
                new_contacts            INTEGER DEFAULT 0,
                invitations             INTEGER DEFAULT 0,
                signed_up               INTEGER DEFAULT 0,
                diagnostics_done        INTEGER DEFAULT 0,
                new_clients             INTEGER DEFAULT 0,
                active_clients_coaching INTEGER DEFAULT 0,
                active_clients_mentoring INTEGER DEFAULT 0,
                sessions_done           INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)


# ── Settings ──────────────────────────────────────────────────────────────────

def save_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_setting(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None


# ── Daily log ─────────────────────────────────────────────────────────────────

def upsert_metric(d: date, metric: str, value: int) -> None:
    """Insert or update a single metric for a given date."""
    week = get_week_number(d)
    date_str = d.isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO daily_log (date, week_number) VALUES (?, ?)",
            (date_str, week),
        )
        conn.execute(
            f"UPDATE daily_log SET {metric} = ? WHERE date = ?",
            (value, date_str),
        )


def get_day(d: date) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM daily_log WHERE date = ?", (d.isoformat(),)
        ).fetchone()


def get_week_totals(week_number: int) -> dict[str, int]:
    """Return summed metrics for all days in a given week."""
    select_cols = ", ".join(f"COALESCE(SUM({m}), 0) AS {m}" for m in METRIC_KEYS)
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {select_cols} FROM daily_log WHERE week_number = ?",
            (week_number,),
        ).fetchone()
        if row:
            return dict(row)
        return {m: 0 for m in METRIC_KEYS}
