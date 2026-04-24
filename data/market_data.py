import requests
from typing import List, Optional

from utils.logger import get_logger
from config.constants import API_TIMEOUT, API_RETRIES, CACHE_MARKET_TTL
from storage.cache import Cache


logger = get_logger(__name__)


class MarketData:

    def __init__(self, base_url: str = "https://api.binance.com", cache: Optional[Cache] = None):
        self.base_url = base_url
        self.cache = cache or Cache()

    # =========================
    # 📊 FETCH KLINES (MAIN)
    # =========================
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 100
    ) -> List[List[float]]:

        cache_key = f"klines:{symbol}:{interval}:{limit}"

        # =========================
        # CACHE CHECK
        # =========================
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"[CACHE HIT] {cache_key}")
            return cached

        logger.info(f"[FETCH] Fetching klines for {symbol} ({interval})")

        clean_symbol = symbol.replace("/", "").upper()

        url = (
            f"{self.base_url}/api/v3/klines"
            f"?symbol={clean_symbol}"
            f"&interval={interval}"
            f"&limit={limit}"
        )

        # =========================
        # RETRY LOGIC
        # =========================
        for attempt in range(1, API_RETRIES + 1):
            try:
                response = requests.get(url, timeout=API_TIMEOUT)

                logger.info(f"[HTTP] {response.status_code} | Attempt {attempt}")

                if response.status_code != 200:
                    logger.warning(f"[ERROR] Bad status: {response.status_code}")
                    continue

                data = response.json()

                # =========================
                # VALIDATION
                # =========================
                if not isinstance(data, list) or len(data) == 0:
                    raise ValueError("Invalid kline data format")

                candles = self._parse_klines(data)

                if not candles:
                    raise ValueError("Parsed candles empty")

                # =========================
                # CACHE STORE
                # =========================
                self.cache.set(cache_key, candles, CACHE_MARKET_TTL)

                logger.info(f"[SUCCESS] Retrieved {len(candles)} candles")

                return candles

            except requests.exceptions.Timeout:
                logger.warning(f"[TIMEOUT] Attempt {attempt}")

            except requests.exceptions.ConnectionError:
                logger.warning(f"[CONNECTION ERROR] Attempt {attempt}")

            except Exception as e:
                logger.error(f"[UNEXPECTED ERROR] {e}")

        # =========================
        # HARD FAIL (NO SILENT FAIL)
        # =========================
        raise Exception(f"Failed to fetch market data for {symbol}")

    # =========================
    # 🔄 PARSE DATA
    # =========================
    def _parse_klines(self, raw_data: List) -> List[List[float]]:
        parsed = []

        try:
            for k in raw_data:
                parsed.append([
                    float(k[0]),  # timestamp
                    float(k[1]),  # open
                    float(k[2]),  # high
                    float(k[3]),  # low
                    float(k[4]),  # close
                    float(k[5])   # volume
                ])

            return parsed

        except Exception as e:
            logger.error(f"[PARSE ERROR] {e}")
            return []

    # =========================
    # 📈 CLOSE PRICES
    # =========================
    def get_closes(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[4] for c in candles]

    # =========================
    # 📊 HIGHS
    # =========================
    def get_highs(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[2] for c in candles]

    # =========================
    # 📉 LOWS
    # =========================
    def get_lows(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[float]:
        candles = self.get_klines(symbol, interval, limit)
        return [c[3] for c in candles]