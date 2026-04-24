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


class TelegramMainBot:

    def __init__(self):
        self.token = SECRETS["telegram_main_token"]
        self.chat_id = SECRETS["telegram_main_chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    # =========================
    # 📤 SEND MESSAGE
    # =========================
    def send_message(self, text: str):

        try:
            url = f"{self.base_url}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }

            requests.post(url, json=payload)

        except Exception as e:
            logger.error(f"Telegram send error: {e}")

    # =========================
    # 📤 SEND IMAGE
    # =========================
    def send_image(self, image_path: str, caption: str = ""):

        try:
            url = f"{self.base_url}/sendPhoto"

            with open(image_path, "rb") as img:
                files = {"photo": img}

                data = {
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown"
                }

                requests.post(url, files=files, data=data)

        except Exception as e:
            logger.error(f"Telegram image send error: {e}")

    # =========================
    # 📊 FORMAT TRADE MESSAGE
    # =========================
    def format_trade(self, trade: Dict, symbol: str) -> str:

        if trade["action"] != "TRADE":
            return ""

        strategy = trade.get("strategy", "unknown")
        emoji = STRATEGY_EMOJI.get(strategy, "📊")

        side_emoji = "🟢" if trade["side"] == "LONG" else "🔴"

        message = f"""
🚨 *TRADE SIGNAL* 🚨

{emoji} *{strategy.upper()}*
{side_emoji} *{trade['side']}* — {symbol}

📍 Entry: `{trade['entry']:.4f}`
🛑 Stop Loss: `{trade['stop_loss']:.4f}`
🎯 Take Profit: `{trade['take_profit']:.4f}`

🧠 Confidence: `{trade['confidence']}%`

💬 _{trade['reason']}_

━━━━━━━━━━━━━━━
"""

        return message

    # =========================
    # 📤 SEND TRADE
    # =========================
    def send_trade(self, trade: Dict, symbol: str, chart_path: str = None):

        msg = self.format_trade(trade, symbol)

        if not msg:
            return

        if chart_path:
            self.send_image(chart_path, msg)
        else:
            self.send_message(msg)