import requests
from typing import Dict

from utils.logger import get_logger
from config.secrets import SECRETS
from utils.helpers import format_price, safe_round


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

        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        for attempt in range(3):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info("Telegram message sent")
                    return True
                else:
                    logger.warning(
                        f"Telegram failed [{response.status_code}]: {response.text}"
                    )

            except Exception as e:
                logger.error(f"Telegram send error (attempt {attempt + 1}): {e}")

        logger.error("Telegram message FAILED after retries")
        return False

    # =========================
    # 📤 SEND IMAGE
    # =========================
    def send_image(self, image_path: str, caption: str = ""):

        url = f"{self.base_url}/sendPhoto"

        for attempt in range(3):
            try:
                with open(image_path, "rb") as img:

                    files = {"photo": img}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown"
                    }

                    response = requests.post(
                        url,
                        files=files,
                        data=data,
                        timeout=15
                    )

                    if response.status_code == 200:
                        logger.info("Telegram image sent")
                        return True
                    else:
                        logger.warning(
                            f"Telegram image failed [{response.status_code}]: {response.text}"
                        )

            except Exception as e:
                logger.error(f"Telegram image error (attempt {attempt + 1}): {e}")

        logger.error("Telegram image FAILED after retries")
        return False

    # =========================
    # 📊 FORMAT TRADE MESSAGE
    # =========================
    def format_trade(self, trade: Dict, symbol: str) -> str:

        if trade.get("action") != "TRADE":
            return ""

        try:
            strategy = trade.get("strategy", "unknown")
            emoji = STRATEGY_EMOJI.get(strategy, "📊")

            side = trade.get("side", "N/A")
            side_emoji = "🟢" if side == "LONG" else "🔴"

            message = f"""
🚨 *TRADE SIGNAL* 🚨

{emoji} *{strategy.upper()}*
{side_emoji} *{side}* — {symbol}

📍 Entry: `{format_price(trade.get('entry'))}`
🛑 Stop Loss: `{format_price(trade.get('stop_loss'))}`
🎯 Take Profit: `{format_price(trade.get('take_profit'))}`

🧠 Confidence: `{safe_round(trade.get('confidence', 0), 2)}%`

💬 _{trade.get('reason', 'No reason provided')}_

━━━━━━━━━━━━━━━
"""

            return message

        except Exception as e:
            logger.error(f"Format trade error: {e}")
            return ""

    # =========================
    # 📤 SEND TRADE
    # =========================
    def send_trade(self, trade: Dict, symbol: str, chart_path: str = None):

        msg = self.format_trade(trade, symbol)

        if not msg:
            logger.warning("Empty trade message, skipping send")
            return

        logger.info(f"Sending trade to Telegram: {symbol} | {trade.get('side')}")

        if chart_path:
            self.send_image(chart_path, msg)
        else:
            self.send_message(msg)