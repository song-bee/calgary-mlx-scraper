"""Utility functions for the Calgary MLX scraper"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
import time
import random
import select
import sys


def setup_logging(log_file: str) -> logging.Logger:
    """Configure and return a logger instance"""
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create formatters
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")

    # File handler (all levels)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler (only WARNING and INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add filters to console handler to only show WARNING and INFO
    class WarningInfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno in [logging.WARNING, logging.INFO]

    console_handler.addFilter(WarningInfoFilter())

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def validate_price_range(price_from: int, price_to: int) -> None:
    """Validate price range parameters"""
    if price_from < 0 or price_to < 0:
        raise ValueError("Price values cannot be negative")
    if price_from > price_to:
        raise ValueError("Price-from cannot be greater than price-to")


def format_property_data(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """Format a single property item from raw data"""
    return {
        "id": raw_item.get("id"),
        "address": raw_item.get("address"),
        "price": raw_item.get("price"),
        "bedrooms": raw_item.get("bedrooms"),
        "bathrooms": raw_item.get("bathrooms"),
        "square_feet": raw_item.get("squareFeet"),
        "year_built": raw_item.get("yearBuilt"),
        "sold_date": raw_item.get("soldDate"),
        "fetch_date": datetime.now().strftime("%Y-%m-%d"),
    }


def repr_dict(data: Dict[str, Any], indent: int = 2) -> str:
    """Return a JSON representation of a dictionary with proper formatting"""
    return json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=True)


def random_sleep(base_ms: int = 300, variance_ms: int = 100) -> None:
    """Sleep for a random duration around base_ms ± variance_ms"""
    sleep_time = (base_ms + random.randint(-variance_ms, variance_ms)) / 1000.0
    time.sleep(sleep_time)


def getch(timeout: int = -1, isPrompt: bool = True) -> None:
    if isPrompt:
        print("Please press return key to continue")

    INTERVAL = 1

    if timeout > 0:
        while timeout > 0:

            if isPrompt:
                mins, secs = divmod(timeout, 60)
                timer = "{:02d}:{:02d}".format(mins, secs)
                print("\033[91m{}\033[00m".format(timer), end="\r")

            inputFlag, _, _ = select.select([sys.stdin], [], [], INTERVAL)
            if inputFlag:
                return sys.stdin.read(1), False

            timeout -= INTERVAL
        else:
            return None, True

    return sys.stdin.read(1), True
