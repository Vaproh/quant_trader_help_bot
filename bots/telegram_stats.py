import requests
from typing import Dict

from utils.logger import get_logger
from config.secrets import SECRETS


logger = get_logger(__name__)

# =========================
# 🎨 STRATEGY EMOJIS
# =========================
STRATEGY_EMOJI = {
    "breakout": "🚀",
    "pullback": "📉",
    "range": "📦",
    "momentum": "⚡",
    "volume_spike": "📊",
    "fake_breakout": "🪤",
    "pump": "🔥",
    "overnight": "🌙"
}


class TelegramStatsBot:

    def __init__(self):
        self.token = SECRETS["telegram_stats_token"]
        self.chat_id = SECRETS["telegram_stats_chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str):
        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
            )
        except Exception as e:
            logger.error(f"Stats send error: {e}")

    # =========================
    # 📊 STATS MESSAGE
    # =========================
    def format_stats(self, stats: Dict) -> str:

        return f"""
📊 *BOT PERFORMANCE*

📈 Trades: `{stats['total_trades']}`
✅ Win Rate: `{stats['win_rate']}%`

💰 PnL: `{stats['total_pnl']}`
⚖️ Profit Factor: `{stats['profit_factor']}`

📊 Avg Win: `{stats['avg_win']}`
📉 Avg Loss: `{stats['avg_loss']}`

🔥 Max DD: `{stats['max_drawdown']}%`
"""

    def send_stats(self, stats: Dict):
        self.send_message(self.format_stats(stats))

    # =========================
    # 📊 TRADE RESULT
    # =========================
    def send_trade_result(self, trade: Dict, symbol: str):

        result = trade.get("result")
        result_emoji = "🟢" if result == "WIN" else "🔴"

        strategy = trade.get("strategy", "N/A")

        msg = f"""
📊 *TRADE CLOSED*

{result_emoji} {trade.get('side')} — {symbol}
📊 Strategy: `{strategy}`

💰 PnL: `{round(trade.get('pnl', 0), 2)}`
📍 Entry: `{trade.get('entry')}`

━━━━━━━━━━━━━━━
"""

        self.send_message(msg)