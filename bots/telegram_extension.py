import requests
from typing import Dict

from utils.logger import get_logger
from config.secrets import SECRETS
from utils.helpers import format_price, safe_round


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
        self.chat_id = int(SECRETS["telegram_extension_chat_id"])
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
                    logger.info("Extension message sent")
                    return True
                else:
                    logger.warning(f"Extension failed [{res.status_code}]: {res.text}")

            except Exception as e:
                logger.error(f"Extension send error (attempt {attempt+1}): {e}")

        logger.error("Extension message FAILED after retries")
        return False

    # =========================
    # 📤 IMAGE SEND
    # =========================
    def send_image(self, image_path: str, caption: str = ""):

        url = f"{self.base_url}/sendPhoto"

        for attempt in range(3):
            try:
                with open(image_path, "rb") as img:
                    res = requests.post(
                        url,
                        files={"photo": img},
                        data={
                            "chat_id": self.chat_id,
                            "caption": caption,
                            "parse_mode": "Markdown"
                        },
                        timeout=15
                    )

                    if res.status_code == 200:
                        logger.info("Extension image sent")
                        return True
                    else:
                        logger.warning(f"Image failed [{res.status_code}]: {res.text}")

            except Exception as e:
                logger.error(f"Image error (attempt {attempt+1}): {e}")

        logger.error("Extension image FAILED")
        return False

    # =========================
    # ⚡ FORMAT TRADE
    # =========================
    def format_trade(self, trade: Dict, symbol: str) -> str:

        if trade.get("action") != "TRADE":
            return ""

        try:
            strategy = trade.get("strategy", "unknown")
            emoji = STRATEGY_EMOJI.get(strategy, "📊")

            side_emoji = "🟢" if trade.get("side") == "LONG" else "🔴"

            return f"""
⚡ *HIGH RISK TRADE*

{emoji} *{strategy.upper()}*
{side_emoji} *{trade.get('side')}* — {symbol}

📍 Entry: `{format_price(trade.get('entry'))}`
🛑 SL: `{format_price(trade.get('stop_loss'))}`
🎯 TP: `{format_price(trade.get('take_profit'))}`

🧠 Confidence: `{safe_round(trade.get('confidence', 0), 2)}%`

🚨 *Aggressive Setup*
"""

        except Exception as e:
            logger.error(f"Extension format error: {e}")
            return ""

    # =========================
    # 📤 SEND TRADE
    # =========================
    def send_trade(self, trade: Dict, symbol: str, chart_path: str = None):

        msg = self.format_trade(trade, symbol)

        if not msg:
            return

        logger.info(f"Sending extension trade: {symbol} | {trade.get('side')}")

        if chart_path:
            self.send_image(chart_path, msg)
        else:
            self.send_message(msg)