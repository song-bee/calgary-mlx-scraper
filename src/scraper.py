"""Main scraper implementation for Calgary MLX"""

import requests
import pandas as pd
from typing import Dict, Any
import os

from .config import (
    BASE_URL, HEADERS, DEFAULT_SEARCH_PARAMS,
    DEFAULT_OUTPUT_FILE, LOG_FILE, COOKIES
)
from .utils import setup_logging, validate_price_range, format_property_data, repr_dict
from .cookie_manager import CookieManager

class CalgaryMLXScraper:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.logger = setup_logging(LOG_FILE)
        self.cookie_manager = CookieManager()
        self.cookies = self._initialize_cookies()

    def _initialize_cookies(self) -> Dict[str, str]:
        """Initialize cookies from stored file or default configuration"""
        stored_cookies = self.cookie_manager.load_cookies()
        if stored_cookies:
            self.logger.info("Using stored cookies")
            return stored_cookies
        
        self.logger.info("Using default cookies")
        self.cookie_manager.save_cookies(COOKIES)
        return COOKIES

    def prepare_payload(self, price_from: int, price_to: int) -> Dict[str, str]:
        """Prepare the POST request payload"""
        validate_price_range(price_from, price_to)
        
        payload = DEFAULT_SEARCH_PARAMS.copy()
        payload.update({
            "price-from": str(price_from),
            "price-to": str(price_to),
        })
        return payload

    def fetch_data(self, price_from: int, price_to: int) -> Dict[str, Any]:
        """Fetch data from the MLX website"""
        try:
            payload = self.prepare_payload(price_from, price_to)
            self.logger.info(f"Fetching data for price range: ${price_from:,} - ${price_to:,}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()

            # Print the request headers and body
            print('Request Headers:')
            print(repr_dict(dict(response.request.headers)))
            print('\nRequest Body:')
            print(response.request.body)

            # Print the response for verification
            print('\nResponse:')
            print(repr_dict(response.json()))

            # Update cookies if any new ones were set
            if response.cookies:
                new_cookies = self.cookies.copy()
                new_cookies.update(response.cookies.get_dict())
                self.cookie_manager.save_cookies(new_cookies)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            raise

    def parse_property_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Parse the raw JSON data into a structured format"""
        try:
            properties = [
                format_property_data(item)
                for item in raw_data.get('properties', [])
            ]
            
            df = pd.DataFrame(properties)
            self.logger.info(f"Successfully parsed {len(df)} properties")
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing data: {str(e)}")
            raise

    def save_to_csv(self, df: pd.DataFrame, filename: str = DEFAULT_OUTPUT_FILE):
        """Save the processed data to a CSV file"""
        try:
            # Ensure the data directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            df.to_csv(filename, index=False)
            self.logger.info(f"Data saved successfully to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise 