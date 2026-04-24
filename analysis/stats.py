from typing import List, Dict

from utils.logger import get_logger


logger = get_logger(__name__)


class Stats:

    def __init__(self, trades: List[Dict]):
        self.trades = trades

    # =========================
    # 📊 TOTAL TRADES
    # =========================
    def total_trades(self) -> int:
        return len(self.trades)

    # =========================
    # ✅ WIN RATE
    # =========================
    def win_rate(self) -> float:
        try:
            wins = sum(1 for t in self.trades if t.get("result") == "WIN")
            total = len(self.trades)

            if total == 0:
                return 0.0

            return (wins / total) * 100

        except Exception as e:
            logger.error(f"Win rate error: {e}")
            return 0.0

    # =========================
    # 📈 AVG WIN
    # =========================
    def avg_win(self) -> float:
        try:
            wins = [t["pnl"] for t in self.trades if t.get("result") == "WIN"]

            if not wins:
                return 0.0

            return sum(wins) / len(wins)

        except Exception as e:
            logger.error(f"Avg win error: {e}")
            return 0.0

    # =========================
    # 📉 AVG LOSS
    # =========================
    def avg_loss(self) -> float:
        try:
            losses = [t["pnl"] for t in self.trades if t.get("result") == "LOSS"]

            if not losses:
                return 0.0

            return sum(losses) / len(losses)

        except Exception as e:
            logger.error(f"Avg loss error: {e}")
            return 0.0

    # =========================
    # 💰 TOTAL PNL
    # =========================
    def total_pnl(self) -> float:
        try:
            return sum(t.get("pnl", 0) for t in self.trades)
        except Exception as e:
            logger.error(f"Total pnl error: {e}")
            return 0.0

    # =========================
    # ⚖️ PROFIT FACTOR
    # =========================
    def profit_factor(self) -> float:
        try:
            wins = sum(t["pnl"] for t in self.trades if t.get("result") == "WIN")
            losses = abs(sum(t["pnl"] for t in self.trades if t.get("result") == "LOSS"))

            if losses == 0:
                return wins

            return wins / losses

        except Exception as e:
            logger.error(f"Profit factor error: {e}")
            return 0.0

    # =========================
    # 📉 MAX DRAWDOWN
    # =========================
    def max_drawdown(self) -> float:
        try:
            balance = 0
            peak = 0
            max_dd = 0

            for t in self.trades:
                balance += t.get("pnl", 0)
                peak = max(peak, balance)

                if peak > 0:
                    dd = (peak - balance) / peak
                    max_dd = max(max_dd, dd)

            return max_dd * 100

        except Exception as e:
            logger.error(f"Drawdown error: {e}")
            return 0.0

    # =========================
    # 📊 SUMMARY
    # =========================
    def summary(self) -> Dict:

        return {
            "total_trades": self.total_trades(),
            "win_rate": round(self.win_rate(), 2),
            "avg_win": round(self.avg_win(), 2),
            "avg_loss": round(self.avg_loss(), 2),
            "total_pnl": round(self.total_pnl(), 2),
            "profit_factor": round(self.profit_factor(), 2),
            "max_drawdown": round(self.max_drawdown(), 2),
        }