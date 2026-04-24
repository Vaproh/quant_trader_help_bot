from typing import Any, Optional


# =========================
# 🔢 SAFE FLOAT CONVERSION
# =========================
def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================
# 🔢 SAFE ROUND
# =========================
def safe_round(value: Any, digits: int = 4) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


# =========================
# 💰 FORMAT PRICE
# =========================
def format_price(price: float) -> str:
    """
    Smart formatting based on price size.
    """
    try:
        price = float(price)

        if price >= 1000:
            return f"{price:,.2f}"
        elif price >= 1:
            return f"{price:.4f}"
        else:
            return f"{price:.6f}"

    except Exception:
        return "0"


# =========================
# 📊 PERCENTAGE CHANGE
# =========================
def percentage_change(start: float, end: float) -> float:
    try:
        start = float(start)
        end = float(end)

        if start == 0:
            return 0.0

        return ((end - start) / start) * 100

    except Exception:
        return 0.0


# =========================
# 📉 RISK / REWARD
# =========================
def calculate_rr(entry: float, stop_loss: float, take_profit: float) -> float:
    try:
        entry = float(entry)
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)

        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)

        if risk == 0:
            return 0.0

        return reward / risk

    except Exception:
        return 0.0


# =========================
# 🔒 CLAMP VALUE
# =========================
def clamp(value: float, min_value: float, max_value: float) -> float:
    try:
        return max(min_value, min(value, max_value))
    except Exception:
        return min_value


# =========================
# 📈 CONFIDENCE BOOST
# =========================
def boost_confidence(
    current: float,
    boost: float,
    max_value: float = 100
) -> float:
    return clamp(current + boost, 0, max_value)


# =========================
# ✅ VALID NUMBER CHECK
# =========================
def is_valid_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


# =========================
# 🧠 SAFE GET FROM DICT
# =========================
def safe_get(data: dict, key: str, default: Optional[Any] = None):
    try:
        return data.get(key, default)
    except Exception:
        return default