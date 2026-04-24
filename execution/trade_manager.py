from typing import List, Dict
from utils.logger import get_logger


logger = get_logger(__name__)


class TradeManager:

    def __init__(self, max_trades: int = 5):
        self.active_trades: List[Dict] = []
        self.closed_trades: List[Dict] = []
        self.max_trades = max_trades

    # =========================
    # 📥 OPEN TRADE
    # =========================
    def open_trade(self, trade: Dict) -> bool:
        try:
            if len(self.active_trades) >= self.max_trades:
                logger.warning("Max open trades reached")
                return False

            # 🚫 DUPLICATE CHECK
            for t in self.active_trades:
                if (
                        t["side"] == trade["side"] and
                        abs(t["entry"] - trade["entry"]) / trade["entry"] < 0.002  # 0.2%
                ):
                    logger.info("Duplicate trade blocked")
                    return False

            trade["status"] = "OPEN"
            self.active_trades.append(trade)

            logger.info(f"Opened trade: {trade['side']} @ {trade['entry']}")
            return True

        except Exception as e:
            logger.error(f"Open trade error: {e}")
            return False

    # =========================
    # 📊 UPDATE TRADES
    # =========================
    def update_trades(self, current_price: float):

        to_close = []

        for trade in self.active_trades:
            try:
                side = trade["side"]
                entry = trade["entry"]
                sl = trade["stop_loss"]
                tp = trade["take_profit"]

                if side == "LONG":
                    if current_price <= sl:
                        trade["pnl"] = self._calc_pnl(entry, current_price, side)
                        trade["result"] = "LOSS"
                        to_close.append(trade)

                    elif current_price >= tp:
                        trade["pnl"] = self._calc_pnl(entry, current_price, side)
                        trade["result"] = "WIN"
                        to_close.append(trade)

                elif side == "SHORT":
                    if current_price >= sl:
                        trade["pnl"] = self._calc_pnl(entry, current_price, side)
                        trade["result"] = "LOSS"
                        to_close.append(trade)

                    elif current_price <= tp:
                        trade["pnl"] = self._calc_pnl(entry, current_price, side)
                        trade["result"] = "WIN"
                        to_close.append(trade)

            except Exception as e:
                logger.error(f"Trade update error: {e}")

        for trade in to_close:
            self.close_trade(trade)

    # =========================
    # 📤 CLOSE TRADE
    # =========================
    def close_trade(self, trade: Dict):
        try:
            trade["status"] = "CLOSED"

            if trade in self.active_trades:
                self.active_trades.remove(trade)

            self.closed_trades.append(trade)

            logger.info(
                f"Closed trade | {trade['side']} | PnL: {trade.get('pnl', 0):.2f}"
            )

        except Exception as e:
            logger.error(f"Close trade error: {e}")

    # =========================
    # 📊 PNL CALCULATION
    # =========================
    def _calc_pnl(self, entry: float, exit_price: float, side: str) -> float:
        try:
            return exit_price - entry if side == "LONG" else entry - exit_price
        except:
            return 0.0