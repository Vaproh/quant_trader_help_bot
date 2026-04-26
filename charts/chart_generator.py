import os
import matplotlib
matplotlib.use('Agg')  # Headless mode
import matplotlib.pyplot as plt
from typing import List, Optional


class ChartGenerator:

    def __init__(self, config=None):
        self.config = config or {}

        self.output_dir = self.config.get("chart_output_dir", "charts/output")
        os.makedirs(self.output_dir, exist_ok=True)

    # =========================
    # 📊 TRADE CHART (COLORED)
    # =========================
    def generate_trade_chart(
        self,
        symbol: str,
        candles: List[List[float]],
        entry: float,
        stop_loss: float,
        take_profit: float,
        filename: Optional[str] = None
    ) -> str:

        if not candles:
            return ""

        closes = [c[4] for c in candles]

        plt.figure(figsize=(10, 5))

        # 📈 Price (WHITE/BLACK)
        plt.plot(closes, linewidth=2, label="Price")

        # 🎯 ENTRY (BLUE)
        plt.axhline(
            entry,
            linestyle="--",
            linewidth=2,
            label="Entry"
        )

        # 🛑 STOP LOSS (RED)
        plt.axhline(
            stop_loss,
            linestyle="--",
            linewidth=2,
            label="Stop Loss"
        )

        # 🎯 TAKE PROFIT (GREEN)
        plt.axhline(
            take_profit,
            linestyle="--",
            linewidth=2,
            label="Take Profit"
        )

        # =========================
        # 🎨 COLOR STYLING
        # =========================
        lines = plt.gca().get_lines()

        if len(lines) >= 4:
            lines[0].set_color("black")   # price
            lines[1].set_color("blue")    # entry
            lines[2].set_color("red")     # SL
            lines[3].set_color("green")   # TP

        # Background grid
        plt.grid(True, alpha=0.3)

        # Labels
        plt.title(f"{symbol} Trade Setup", fontsize=14)
        plt.xlabel("Candles")
        plt.ylabel("Price")

        plt.legend()

        filename = filename or f"{symbol.replace('/', '_')}_trade.png"
        path = os.path.join(self.output_dir, filename)

        plt.savefig(path, dpi=120, bbox_inches="tight")
        plt.close()

        return path

    # =========================
    # 📈 PERFORMANCE CHART
    # =========================
    def generate_performance_chart(
        self,
        pnl_history: List[float],
        filename: Optional[str] = None
    ) -> str:

        if not pnl_history:
            return ""

        plt.figure(figsize=(10, 5))

        # Balance line (GREEN)
        plt.plot(pnl_history, linewidth=2)

        # Fill profit/loss
        start = pnl_history[0]

        for i in range(1, len(pnl_history)):
            if pnl_history[i] >= start:
                plt.fill_between(range(i + 1), pnl_history[:i + 1], start, alpha=0.1)
            else:
                plt.fill_between(range(i + 1), pnl_history[:i + 1], start, alpha=0.1)

        plt.title("Equity Curve")
        plt.xlabel("Trades")
        plt.ylabel("Balance")

        plt.grid(True, alpha=0.3)

        filename = filename or "performance.png"
        path = os.path.join(self.output_dir, filename)

        plt.savefig(path, dpi=120, bbox_inches="tight")
        plt.close()

        return path