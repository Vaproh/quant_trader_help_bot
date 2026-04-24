import os
from typing import List, Dict

import matplotlib.pyplot as plt

from utils.logger import get_logger
from config.constants import CHART_OUTPUT_DIR


logger = get_logger(__name__)



class PerformanceCharts:

    def __init__(self):
        os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)

    # =========================
    # 📈 EQUITY CURVE (GREEN LINE)
    # =========================
    def equity_curve(self, balances: List[float], filename: str = "equity_curve.png"):

        try:
            if not balances:
                return

            plt.figure()

            plt.plot(balances, linewidth=2)

            # fill green/red based on profit
            start = balances[0]
            for i in range(1, len(balances)):
                if balances[i] >= start:
                    plt.fill_between(range(i+1), balances[:i+1], start, alpha=0.1)
                else:
                    plt.fill_between(range(i+1), balances[:i+1], start, alpha=0.1)

            plt.title("Equity Curve")
            plt.xlabel("Trades")
            plt.ylabel("Balance")
            plt.grid(True)

            path = os.path.join(CHART_OUTPUT_DIR, filename)
            plt.savefig(path)
            plt.close()

            logger.info(f"Saved equity curve: {path}")

        except Exception as e:
            logger.error(f"Equity chart error: {e}")

    # =========================
    # 📊 PNL DISTRIBUTION (GREEN/RED)
    # =========================
    def pnl_distribution(self, trades: List[Dict], filename: str = "pnl_distribution.png"):

        try:
            pnls = [t.get("pnl", 0) for t in trades if "pnl" in t]

            if not pnls:
                return

            colors = ["green" if p > 0 else "red" for p in pnls]

            plt.figure()
            plt.bar(range(len(pnls)), pnls)

            plt.title("PnL Distribution")
            plt.xlabel("Trades")
            plt.ylabel("PnL")
            plt.grid(True)

            path = os.path.join(CHART_OUTPUT_DIR, filename)
            plt.savefig(path)
            plt.close()

            logger.info(f"Saved PnL chart: {path}")

        except Exception as e:
            logger.error(f"PnL chart error: {e}")

    # =========================
    # 📊 WIN vs LOSS (COLOR)
    # =========================
    def win_loss_chart(self, trades: List[Dict], filename: str = "win_loss.png"):

        try:
            wins = sum(1 for t in trades if t.get("result") == "WIN")
            losses = sum(1 for t in trades if t.get("result") == "LOSS")

            if wins + losses == 0:
                return

            plt.figure()
            plt.bar(["Wins", "Losses"], [wins, losses])

            plt.title("Win vs Loss")

            path = os.path.join(CHART_OUTPUT_DIR, filename)
            plt.savefig(path)
            plt.close()

            logger.info(f"Saved win/loss chart: {path}")

        except Exception as e:
            logger.error(f"Win/Loss chart error: {e}")

    # =========================
    # 📉 DRAWDOWN (RED LINE)
    # =========================
    def drawdown(self, balances: List[float], filename: str = "drawdown.png"):

        try:
            if not balances:
                return

            peak = balances[0]
            drawdowns = []

            for b in balances:
                peak = max(peak, b)
                dd = (peak - b) / peak if peak != 0 else 0
                drawdowns.append(dd)

            plt.figure()
            plt.plot(drawdowns, linewidth=2)

            plt.title("Drawdown")
            plt.xlabel("Trades")
            plt.ylabel("Drawdown %")
            plt.grid(True)

            path = os.path.join(CHART_OUTPUT_DIR, filename)
            plt.savefig(path)
            plt.close()

            logger.info(f"Saved drawdown chart: {path}")

        except Exception as e:
            logger.error(f"Drawdown chart error: {e}")