# backend/app/utils/logging.py
import logging
import sys
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    """Configure structured logging for the application."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Format: timestamp - name - level - message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

# Global logger instance
logger = setup_logger('veritas')
