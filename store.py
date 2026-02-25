"""
store.py — Database Storage Module
=====================================
Saves enriched headlines to a SQLite database and provides query functions.
This is the "L" in ETL (Load).

SQLite is a simple file-based database — no server setup needed.
The database file 'news.db' will be created automatically in your project folder.
"""

import os
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Database Setup ───────────────────────────────────────────────────────────

# SQLite database file will be created in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(__file__), "news.db")
engine = sa.create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db():
    """Create the database tables if they don't exist yet."""
    with engine.connect() as conn:
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS headlines (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                source      TEXT,
                published_at TEXT,
                url         TEXT,
                description TEXT,
                sentiment   TEXT,
                confidence  REAL,
                reason      TEXT,
                ai_mode     TEXT,
                fetched_at  TEXT,
                topic       TEXT
            )
        """))
        conn.commit()
    print(f"✅ Database ready at: {DB_PATH}")


# ─── Write ────────────────────────────────────────────────────────────────────

def save_results(results: list[dict], topic: str = None) -> int:
    """
    Save analyzed headlines to the database.

    Args:
        results: List of enriched headline dicts from analyze.py
        topic: The search topic used (stored for reference)

    Returns:
        Number of rows saved
    """
    if not results:
        print("⚠️  No results to save.")
        return 0

    init_db()

    df = pd.DataFrame(results)

    # Add metadata columns
    df["fetched_at"] = datetime.now().isoformat()
    df["topic"] = topic or os.getenv("NEWS_TOPIC", "unknown")

    # Ensure all expected columns exist (fill missing with None)
    expected_cols = ["title", "source", "published_at", "url", "description",
                     "sentiment", "confidence", "reason", "ai_mode", "fetched_at", "topic"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df = df[expected_cols]  # Keep only the columns we need

    # Append to the database (add rows, don't overwrite)
    df.to_sql("headlines", engine, if_exists="append", index=False)

    print(f"💾 Saved {len(df)} rows to database.")
    return len(df)


# ─── Read ─────────────────────────────────────────────────────────────────────

def load_all() -> pd.DataFrame:
    """Load all headlines from the database, newest first."""
    init_db()
    try:
        df = pd.read_sql(
            "SELECT * FROM headlines ORDER BY fetched_at DESC",
            engine
        )
        return df
    except Exception:
        return pd.DataFrame()


def load_by_topic(topic: str) -> pd.DataFrame:
    """Load headlines filtered by topic."""
    init_db()
    df = pd.read_sql(
        "SELECT * FROM headlines WHERE topic = :topic ORDER BY fetched_at DESC",
        engine,
        params={"topic": topic}
    )
    return df


def get_stats() -> dict:
    """Return summary statistics about the database."""
    init_db()
    df = load_all()
    if df.empty:
        return {"total": 0}

    return {
        "total": len(df),
        "positive": int((df["sentiment"] == "positive").sum()),
        "negative": int((df["sentiment"] == "negative").sum()),
        "neutral": int((df["sentiment"] == "neutral").sum()),
        "topics": df["topic"].nunique(),
        "sources": df["source"].nunique(),
        "last_run": df["fetched_at"].max(),
    }


def clear_db():
    """Delete all records from the database (use carefully!)."""
    with engine.connect() as conn:
        conn.execute(sa.text("DELETE FROM headlines"))
        conn.commit()
    print("🗑️  Database cleared.")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test this module directly: python store.py
    stats = get_stats()
    print("\n📊 Database Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
