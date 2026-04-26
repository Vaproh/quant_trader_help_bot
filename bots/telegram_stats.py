import requests
from typing import Dict

from utils.logger import get_logger
from config.secrets import SECRETS
from utils.helpers import format_price, safe_round, safe_get


logger = get_logger(__name__)


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

    # =========================
    # 📤 SAFE SEND
    # =========================
    def send_message(self, text: str):

        url = f"{self.base_url}/sendMessage"

        for attempt in range(3):
            try:
                res = requests.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=10
                )

                if res.status_code == 200:
                    logger.info("Stats message sent")
                    return True
                else:
                    logger.warning(f"Stats failed [{res.status_code}]: {res.text}")

            except Exception as e:
                logger.error(f"Stats send error (attempt {attempt+1}): {e}")

        logger.error("Stats message FAILED after retries")
        return False

    # =========================
    # 📊 FORMAT STATS
    # =========================
    def format_stats(self, stats: Dict) -> str:

        return f"""
📊 *BOT PERFORMANCE*

📈 Trades: `{safe_get(stats, 'total_trades', 0)}`
✅ Win Rate: `{safe_get(stats, 'win_rate', 0)}%`

💰 PnL: `{safe_round(safe_get(stats, 'total_pnl', 0), 2)}`
⚖️ Profit Factor: `{safe_get(stats, 'profit_factor', 0)}`

📊 Avg Win: `{safe_round(safe_get(stats, 'avg_win', 0), 2)}`
📉 Avg Loss: `{safe_round(safe_get(stats, 'avg_loss', 0), 2)}`

🔥 Max DD: `{safe_get(stats, 'max_drawdown', 0)}%`
"""

    def send_stats(self, stats: Dict):
        self.send_message(self.format_stats(stats))

    # =========================
    # 📊 TRADE RESULT
    # =========================
    def send_trade_result(self, trade: Dict, symbol: str):

        try:
            result = trade.get("result", "UNKNOWN")
            result_emoji = "🟢" if result == "WIN" else "🔴"

            strategy = trade.get("strategy", "unknown")
            emoji = STRATEGY_EMOJI.get(strategy, "📊")

            msg = f"""
📊 *TRADE CLOSED*

{emoji} `{strategy.upper()}`
{result_emoji} {trade.get('side')} — {symbol}

💰 PnL: `{safe_round(trade.get('pnl', 0), 2)}`
📍 Entry: `{format_price(trade.get('entry'))}`

━━━━━━━━━━━━━━━
"""

            logger.info(f"Sending trade result: {symbol} | {result}")
            self.send_message(msg)

        except Exception as e:
            logger.error(f"Trade result formatting error: {e}")