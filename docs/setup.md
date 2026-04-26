# ⚙️ Setup Guide

## Create Virtual ENV
```bash
python -m venv .venv
```

## Install Libraries
```bash
pip install -r requirements.txt
```

## Setup Environment variables (.env)

- telegram tokens
- api keys

### format:
```env
# TELEGRAM
telegram_main_token=
telegram_main_chat_id=

telegram_extension_token=
telegram_extension_chat_id=

telegram_watchlist_token=
telegram_watchlist_chat_id=

telegram_stats_token=
telegram_stats_chat_id=

# APIs
news_api_key=
ai_api_key=

# (optional)
binance_api_key=
binance_secret_key=
```

## Run bot

```bash
python main.py
```

## Notes

- Default = paper trading
- No real trading enabled