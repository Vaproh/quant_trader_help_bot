import requests
from typing import Dict

from utils.logger import get_logger
from config.secrets import SECRETS


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


class TelegramExtensionBot:

    def __init__(self):
        self.token = SECRETS["telegram_extension_token"]
        self.chat_id = SECRETS["telegram_extension_chat_id"]
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
            logger.error(f"Extension send error: {e}")

    def send_image(self, image_path: str, caption: str = ""):
        try:
            with open(image_path, "rb") as img:
                requests.post(
                    f"{self.base_url}/sendPhoto",
                    files={"photo": img},
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown"
                    }
                )
        except Exception as e:
            logger.error(f"Extension image error: {e}")

    # =========================
    # ⚡ FORMAT TRADE
    # =========================
    def format_trade(self, trade: Dict, symbol: str) -> str:

        if trade["action"] != "TRADE":
            return ""

        strategy = trade.get("strategy", "unknown")
        emoji = STRATEGY_EMOJI.get(strategy, "📊")

        side_emoji = "🟢" if trade["side"] == "LONG" else "🔴"

        return f"""
⚡ *HIGH RISK TRADE*

{emoji} *{strategy.upper()}*
{side_emoji} *{trade['side']}* — {symbol}

📍 Entry: `{trade['entry']:.4f}`
🛑 SL: `{trade['stop_loss']:.4f}`
🎯 TP: `{trade['take_profit']:.4f}`

🧠 Confidence: `{trade['confidence']}%`

🚨 *Aggressive Setup*
"""

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