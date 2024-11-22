"""Utility functions for the Calgary MLX scraper"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
import time
import random

def setup_logging(log_file: str) -> logging.Logger:
    """Configure and return a logger instance"""
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_price_range(price_from: int, price_to: int) -> None:
    """Validate price range parameters"""
    if price_from < 0 or price_to < 0:
        raise ValueError("Price values cannot be negative")
    if price_from > price_to:
        raise ValueError("Price-from cannot be greater than price-to")

def format_property_data(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """Format a single property item from raw data"""
    return {
        'id': raw_item.get('id'),
        'address': raw_item.get('address'),
        'price': raw_item.get('price'),
        'bedrooms': raw_item.get('bedrooms'),
        'bathrooms': raw_item.get('bathrooms'),
        'square_feet': raw_item.get('squareFeet'),
        'year_built': raw_item.get('yearBuilt'),
        'sold_date': raw_item.get('soldDate'),
        'fetch_date': datetime.now().strftime('%Y-%m-%d')
    } 

def repr_dict(data, indent=2):
    """Return a JSON representation of a dictionary with proper formatting"""
    return json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=True)

def random_sleep(base_ms: int = 500, variance_ms: int = 100) -> None:
    """Sleep for a random duration around base_ms ± variance_ms"""
    sleep_time = (base_ms + random.randint(-variance_ms, variance_ms)) / 1000.0
    time.sleep(sleep_time)
