SETTINGS = {

    # =========================
    # 🪙 SYMBOLS
    # =========================
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],

    "preference_coins": ["BTC/USDT", "ETH/USDT"],

    # =========================
    # ⏱️ LOOP
    # =========================
    "loop_delay": 10,

    # =========================
    # 🚀 ENGINE
    # =========================
    "engine": {
        "cycle_delay": 5
    },

    # =========================
    # ⚠️ RISK
    # =========================
    "risk_per_trade": 0.02,

    # =========================
    # 🧠 DECISION
    # =========================
    "decision": {
        "min_confidence": 70,  # Main bot only takes high-confidence trades
        "max_leverage": 3
    },

    # =========================
    # 📊 STRATEGY DECIDER
    # =========================
    "strategy_decider": {
        "min_confidence": 50,  # Base pre-filter (overridden per engine)
        "max_signals_per_cycle": 3
    },

    # =========================
    # ⚡ EXTENSION (Aggressive)
    # =========================
    "extension": {
        "loop_interval": 5,
        "risk_per_trade": 0.05,
        "max_leverage": 10,
        "max_signals_per_cycle": 5,
        "min_confidence": 30,  # Very low — catches high-risk opportunities
        "loop_delay": 5
    },

    # =========================
    # 👀 WATCHLIST (High Quality)
    # =========================
    "watchlist": {
        "symbols": [],
        "min_confidence": 65,  # Higher than main
        "min_rr": 1.5,
        "max_signals_per_cycle": 2,
        "loop_delay": 15
    },

    # =========================
    # 📈 STRATEGIES CONFIG
    # =========================
    "strategies": {
        "enabled": [
            "breakout",
            "pullback",
            "range",
            "overnight"
        ]
    },

    # =========================
    # 🧠 ENGINE STRATEGY ASSIGNMENTS
    # =========================
    "engines": {
        "main": [
            "breakout",
            "pullback",
            "range",
            "momentum"
        ],
        "extension": [
            "breakout",
            "momentum",
            "volume_spike",
            "fake_breakout",
            "pump"
        ],
        "watchlist": [
            "breakout",
            "pullback",
            "fake_breakout",
            "volume_spike",
            "overnight"
        ]
    },

    # =========================
    # ⚙️ EXECUTION
    # =========================
    "paper_trader": {
        "initial_balance": 100.0,
        "max_open_trades": 5,
        "loop_delay": 10,
        "symbol_cooldown": 1200,  # 20 minutes
        "direction_cooldown": 600,  # 10 minutes
        "stats_interval": 3600  # 1 hour
    },

    # =========================
    # 📊 CHARTS
    # =========================
    "charts": {
        "output_dir": "charts/output"
    },

    # =========================
    # 🤖 TELEGRAM
    # =========================
    "telegram": {
        "watchdog_interval": 300,  # 5 minutes
        "silence_threshold": 600   # 10 minutes
    }
}