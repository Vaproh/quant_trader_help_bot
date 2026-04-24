import time
from datetime import datetime, timezone, timedelta
from typing import Optional


# =========================
# ⏱️ CURRENT TIMESTAMP
# =========================
def now_ts() -> float:
    return time.time()


# =========================
# 🕒 CURRENT UTC DATETIME
# =========================
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =========================
# 📅 FORMAT TIMESTAMP
# =========================
def format_ts(ts: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    try:
        return datetime.fromtimestamp(ts).strftime(fmt)
    except Exception:
        return "N/A"


# =========================
# 🧠 SAFE TIMESTAMP
# =========================
def to_timestamp(dt: Optional[datetime]) -> float:
    try:
        if dt is None:
            return 0.0
        return dt.timestamp()
    except Exception:
        return 0.0


# =========================
# 📆 HUMAN READABLE AGO
# =========================
def time_ago(ts: float) -> str:
    try:
        diff = int(time.time() - ts)

        if diff < 0:
            return "future"

        if diff < 60:
            return f"{diff}s ago"
        elif diff < 3600:
            return f"{diff // 60}m ago"
        elif diff < 86400:
            return f"{diff // 3600}h ago"
        else:
            return f"{diff // 86400}d ago"

    except Exception:
        return "N/A"


# =========================
# ⏳ FORMAT DURATION
# =========================
def format_duration(seconds: int) -> str:
    try:
        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"

    except Exception:
        return "N/A"


# =========================
# ⏰ ADD TIME
# =========================
def add_seconds(ts: float, seconds: int) -> float:
    try:
        return ts + seconds
    except Exception:
        return ts


# =========================
# 🧠 IS EXPIRED (TTL CHECK)
# =========================
def is_expired(ts: float, ttl: int) -> bool:
    try:
        return (time.time() - ts) > ttl
    except Exception:
        return True