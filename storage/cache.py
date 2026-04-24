import threading
from typing import Any, Optional, Dict

from utils.time_utils import now_ts, is_expired
from utils.logger import get_logger


logger = get_logger(__name__)


class CacheItem:
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.timestamp = now_ts()
        self.ttl = ttl

    def is_expired(self) -> bool:
        return is_expired(self.timestamp, self.ttl)


class Cache:

    def __init__(self):
        self._store: Dict[str, CacheItem] = {}
        self._lock = threading.Lock()

    # =========================
    # 🧠 SET VALUE
    # =========================
    def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            with self._lock:
                self._store[key] = CacheItem(value, ttl)
                logger.debug(f"Cache SET: {key} (ttl={ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    # =========================
    # 🔍 GET VALUE
    # =========================
    def get(self, key: str) -> Optional[Any]:
        try:
            with self._lock:
                item = self._store.get(key)

                if not item:
                    return None

                if item.is_expired():
                    logger.debug(f"Cache EXPIRED: {key}")
                    del self._store[key]
                    return None

                return item.value

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    # =========================
    # ❌ DELETE
    # =========================
    def delete(self, key: str) -> None:
        try:
            with self._lock:
                if key in self._store:
                    del self._store[key]
                    logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    # =========================
    # 🧹 CLEAR ALL
    # =========================
    def clear(self) -> None:
        try:
            with self._lock:
                self._store.clear()
                logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    # =========================
    # 🧼 CLEAN EXPIRED (OPTIONAL)
    # =========================
    def cleanup(self) -> None:
        try:
            with self._lock:
                keys_to_delete = [
                    key for key, item in self._store.items()
                    if item.is_expired()
                ]

                for key in keys_to_delete:
                    del self._store[key]

                if keys_to_delete:
                    logger.debug(f"Cache cleanup removed {len(keys_to_delete)} items")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")