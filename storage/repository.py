import os
import threading

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
        self._lock = threading.RLock()

        create_tables(self.conn)

    # =========================
    # 📥 INSERT TRADE
    # =========================
    def insert_trade(self, trade: Dict, symbol: str):

        try:
            with self._lock:
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
            with self._lock:
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
            with self._lock:
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
            with self._lock:
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
            with self._lock:
                cursor = self.conn.cursor()

                row = cursor.execute("""
                SELECT value FROM balance
                ORDER BY id DESC LIMIT 1
                """).fetchone()

                return row["value"] if row else None

        except Exception as e:
            logger.error(f"Get balance error: {e}")
            return None

    # =========================
    # 📈 GET BALANCE HISTORY
    # =========================
    def get_balance_history(self, limit: int = 50) -> List[float]:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                rows = cursor.execute("""
                SELECT value FROM balance
                ORDER BY id DESC LIMIT ?
                """, (limit,)).fetchall()

                return [row["value"] for row in rows[::-1]]  # Reverse to chronological

        except Exception as e:
            logger.error(f"Get balance history error: {e}")
            return []

    # =========================
    # 🏆 GET BEST PERFORMERS
    # =========================
    def get_best_performers(self, limit: int = 5) -> List[Dict]:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                rows = cursor.execute("""
                SELECT symbol, SUM(pnl) as total_pnl, COUNT(*) as trade_count
                FROM trades
                WHERE status = 'CLOSED'
                GROUP BY symbol
                ORDER BY total_pnl DESC
                LIMIT ?
                """, (limit,)).fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Get best performers error: {e}")
            return []

    # =========================
    # 👀 GET WATCHLIST
    # =========================
    def get_watchlist(self) -> List[str]:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                rows = cursor.execute("SELECT symbol FROM watchlist ORDER BY added_at").fetchall()

                return [row["symbol"] for row in rows]

        except Exception as e:
            logger.error(f"Get watchlist error: {e}")
            return []

    # =========================
    # ➕ ADD TO WATCHLIST
    # =========================
    def add_to_watchlist(self, symbol: str) -> bool:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                cursor.execute("INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)", (symbol.upper(),))

                self.conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Add to watchlist error: {e}")
            return False

    # =========================
    # ➖ REMOVE FROM WATCHLIST
    # =========================
    def remove_from_watchlist(self, symbol: str) -> bool:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))

                self.conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Remove from watchlist error: {e}")
            return False

    # =========================
    # 📊 GET ACTIVE TRADES
    # =========================
    def get_active_trades(self, symbol: str = None) -> List[Dict]:

        try:
            with self._lock:
                cursor = self.conn.cursor()

                query = "SELECT * FROM trades WHERE status = 'OPEN'"
                params = []

                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)

                rows = cursor.execute(query, params).fetchall()

                trades = []
                for row in rows:
                    d = dict(row)
                    # rename 'id' to 'db_id' for consistency
                    d['db_id'] = d.pop('id')
                    trades.append(d)
                return trades

        except Exception as e:
            logger.error(f"Get active trades error: {e}")
            return []