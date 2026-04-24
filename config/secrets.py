from dotenv import load_dotenv
import os

load_dotenv()

SECRETS = {

    # =========================
    # 🤖 TELEGRAM
    # =========================
    "telegram_main_token": os.getenv("telegram_main_token"),
    "telegram_main_chat_id": os.getenv("telegram_main_chat_id"),

    "telegram_extension_token": os.getenv("telegram_extension_token"),
    "telegram_extension_chat_id": os.getenv("telegram_extension_chat_id"),

    "telegram_watchlist_token": os.getenv("telegram_watchlist_token"),
    "telegram_watchlist_chat_id": os.getenv("telegram_watchlist_chat_id"),

    "telegram_stats_token": os.getenv("telegram_stats_token"),
    "telegram_stats_chat_id": os.getenv("telegram_stats_chat_id"),

    # =========================
    # 🪙 BINANCE (optional later)
    # =========================
    "binance_api_key": os.getenv("binance_api_key"),
    "binance_secret_key": os.getenv("binance_secret_key"),

    # =========================
    # 📰 NEWS API
    # =========================
    "news_api_key": os.getenv("news_api_key"),

    # =========================
    # 🤖 AI API (OpenAI or compatible)
    # =========================
    "ai_api_key": os.getenv("ai_api_key"),
}