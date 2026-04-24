import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


LOG_DIR = "logs"
LOG_FILE = "first run logs.log"


def setup_logger(
    level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Setup global logger (idempotent).
    """

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # =========================
    # 📄 FILE HANDLER
    # =========================
    if log_to_file:
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, LOG_FILE),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # =========================
    # 🖥️ CONSOLE HANDLER
    # =========================
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(levelname)s | %(name)s | %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    logger.debug("Logger initialized")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a named logger instance.
    """
    return logging.getLogger(name if name else __name__)