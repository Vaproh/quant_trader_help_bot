import os

import sqlite3
from typing import List, Dict, Optional

from utils.logger import get_logger
from storage.models import create_tables


logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "trades.db")


class Repository:

    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        create_tables(self.conn)

    # =========================
    # 📥 INSERT TRADE
    # =========================
    def insert_trade(self, trade: Dict, symbol: str):

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
            INSERT INTO trades (
                symbol, side, type,
                entry, stop_loss, take_profit,
                rr, leverage, confidence,
                size, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                trade.get("side"),
                trade.get("type"),

                trade.get("entry"),
                trade.get("stop_loss"),
                trade.get("take_profit"),

                trade.get("rr"),
                trade.get("leverage"),
                trade.get("confidence"),

                trade.get("size"),
                trade.get("status", "OPEN")
            ))

            self.conn.commit()

            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Insert trade error: {e}")
            return None

    # =========================
    # 📤 CLOSE TRADE
    # =========================
    def close_trade(self, trade_id: int, pnl: float, result: str):

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
            UPDATE trades
            SET status = ?, pnl = ?, result = ?
            WHERE id = ?
            """, ("CLOSED", pnl, result, trade_id))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Close trade error: {e}")

    # =========================
    # 📊 GET TRADES
    # =========================
    def get_trades(self) -> List[Dict]:

        try:
            cursor = self.conn.cursor()

            rows = cursor.execute("SELECT * FROM trades").fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Get trades error: {e}")
            return []

    # =========================
    # 💰 SAVE BALANCE
    # =========================
    def save_balance(self, value: float):

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
            INSERT INTO balance (value)
            VALUES (?)
            """, (value,))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Save balance error: {e}")

    # =========================
    # 💰 GET LAST BALANCE
    # =========================
    def get_last_balance(self) -> Optional[float]:

        try:
            cursor = self.conn.cursor()

            row = cursor.execute("""
            SELECT value FROM balance
            ORDER BY id DESC LIMIT 1
            """).fetchone()

            return row["value"] if row else None

        except Exception as e:
            logger.error(f"Get balance error: {e}")
            return None