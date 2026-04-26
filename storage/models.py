import sqlite3


def create_tables(conn: sqlite3.Connection):

    cursor = conn.cursor()

    # =========================
    # 📊 TRADES TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT,
        side TEXT,
        type TEXT,

        entry REAL,
        stop_loss REAL,
        take_profit REAL,

        rr REAL,
        leverage INTEGER,
        confidence INTEGER,

        size REAL,

        status TEXT,
        result TEXT,
        pnl REAL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # 💰 BALANCE TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS balance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # 👀 WATCHLIST TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()