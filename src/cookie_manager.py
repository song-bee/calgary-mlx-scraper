"""Cookie management utilities for the scraper"""

import json
import os
from typing import Dict
from datetime import datetime
from .config import COOKIE_FILE, DATA_DIR

class CookieManager:
    def __init__(self):
        self.cookie_file = COOKIE_FILE
        os.makedirs(DATA_DIR, exist_ok=True)

    def save_cookies(self, cookies: Dict[str, str]) -> None:
        """Save cookies to file with timestamp"""
        cookie_data = {
            'timestamp': datetime.now().isoformat(),
            'cookies': cookies
        }
        with open(self.cookie_file, 'w') as f:
            json.dump(cookie_data, f, indent=4)

    def load_cookies(self) -> Dict[str, str]:
        """Load cookies from file if they exist and are recent"""
        try:
            with open(self.cookie_file, 'r') as f:
                data = json.load(f)
                stored_time = datetime.fromisoformat(data['timestamp'])
                
                # Check if cookies are less than 24 hours old
                if (datetime.now() - stored_time).total_seconds() < 86400:
                    return data['cookies']
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        
        return {}

    def is_cookies_valid(self) -> bool:
        """Check if stored cookies are valid and recent"""
        try:
            with open(self.cookie_file, 'r') as f:
                data = json.load(f)
                stored_time = datetime.fromisoformat(data['timestamp'])
                return (datetime.now() - stored_time).total_seconds() < 86400
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False 