import random
from typing import Dict


class Formatter:

    def __init__(self):
        self.quotes = [
            "Patience pays more than speed.",
            "The trend is your ally.",
            "Protect capital first.",
            "Discipline beats emotion.",
            "Wait for the clean setup.",
            "Good trades are boring.",
            "Risk less, think more.",
            "Consistency > luck."
        ]

    # =========================
    # 🎯 TRADE SETUP MESSAGE
    # =========================
    def format_trade_setup(self, decision: Dict, bot_type: str) -> str:

        header = self._get_header(bot_type, decision["direction"])

        msg = f"""
{header}

📊 Symbol: {decision['symbol']}
📈 Direction: {decision['direction']}
⚙️ Type: {decision['trade_type']}
⚡ Leverage: {decision['leverage']}x

💰 Entry: {round(decision['entry'], 4)}
🛑 Stop Loss: {round(decision['stop_loss'], 4)}
🎯 Take Profit: {round(decision['take_profit'], 4)}

🧠 Strategy: {decision['strategy']}
📊 Confidence: {decision['confidence']}%

⏳ Expected Hold: {self._estimate_hold_time(decision)}

━━━━━━━━━━━━━━━
💡 {self._random_quote()}
"""

        return msg.strip()

    # =========================
    # ✅ TRADE CLOSED MESSAGE
    # =========================
    def format_trade_close(self, trade: Dict, bot_type: str) -> str:

        pnl = trade.get("pnl", 0)
        pnl_pct = trade.get("pnl_percent", 0)

        result_emoji = "🟢" if pnl > 0 else "🔴"

        msg = f"""
{result_emoji} Trade Closed ({bot_type.upper()})

📊 {trade['symbol']} | {trade['side']}
💰 Entry: {round(trade['entry_price'], 4)}
📉 Exit: {round(trade['exit_price'], 4)}

📊 PnL: {round(pnl, 2)}
📈 PnL %: {round(pnl_pct, 2)}%

🧠 Strategy: {trade['strategy']}
📌 Reason: {trade.get('exit_reason', 'N/A')}

━━━━━━━━━━━━━━━
💡 {self._random_quote()}
"""

        return msg.strip()

    # =========================
    # 📊 QUICK NOTIFICATION
    # =========================
    def format_quick_alert(self, message: str, bot_type: str) -> str:

        return f"""
⚡ [{bot_type.upper()} ALERT]

{message}
""".strip()

    # =========================
    # 🧠 HEADER BUILDER
    # =========================
    def _get_header(self, bot_type: str, direction: str) -> str:

        bot_map = {
            "main": "🟢 MAIN BOT",
            "extension": "🔴 EXTENSION BOT",
            "watchlist": "🟡 WATCHLIST BOT"
        }

        direction_emoji = "📈" if direction == "LONG" else "📉"

        return f"{bot_map.get(bot_type, 'BOT')} {direction_emoji}"

    # =========================
    # ⏳ HOLD TIME ESTIMATION
    # =========================
    def _estimate_hold_time(self, decision: Dict) -> str:

        strategy = decision.get("strategy")

        mapping = {
            "breakout": "30m - 2h",
            "pullback": "1h - 4h",
            "range": "30m - 1h",
            "momentum": "5m - 30m",
            "pump": "5m - 20m",
            "fake_breakout": "15m - 1h",
            "volume_spike": "10m - 45m",
            "overnight": "4h - 8h"
        }

        return mapping.get(strategy, "N/A")

    # =========================
    # 💡 RANDOM QUOTE
    # =========================
    def _random_quote(self) -> str:
        return random.choice(self.quotes)