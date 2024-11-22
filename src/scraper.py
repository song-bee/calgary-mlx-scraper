"""Main scraper implementation for Calgary MLX"""

import requests
import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from .config import (
    BASE_URL, HEADERS, DEFAULT_SEARCH_PARAMS,
    DEFAULT_OUTPUT_FILE, LOG_FILE, COOKIES
)
from .utils import setup_logging, validate_price_range, format_property_data, repr_dict
from .cookie_manager import CookieManager

@dataclass
class Tile:
    lat: float
    lon: float
    count: int
    id: int
    pixel_size: int

class CalgaryMLXScraper:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.logger = setup_logging(LOG_FILE)
        self.cookie_manager = CookieManager()
        self.cookies = self._initialize_cookies()
        self.max_workers = 5  # For parallel processing

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

    def fetch_tiles(self, price_from: int, price_to: int) -> Dict[str, Any]:
        """First API call to get the tiles information"""
        try:
            payload = self.prepare_payload(price_from, price_to)
            self.logger.info(f"Fetching tiles for price range: ${price_from:,} - ${price_to:,}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching tiles: {str(e)}")
            raise

    def parse_tiles(self, tiles_data: Dict[str, Any]) -> List[Tile]:
        """Parse the tiles response into Tile objects"""
        tiles = []
        for tile in tiles_data.get('tiles', []):
            tiles.append(Tile(
                lat=tile['lat'],
                lon=tile['lon'],
                count=tile['count'],
                id=tile['id'],
                pixel_size=tile['pixelSize']
            ))
        return tiles

    def create_tile_boundary(self, tile: Tile, radius: float = 0.02) -> Dict[str, float]:
        """Create boundary coordinates for a single tile"""
        return {
            'sw_lat': tile.lat - radius,
            'sw_lng': tile.lon - radius,
            'ne_lat': tile.lat + radius,
            'ne_lng': tile.lon + radius,
            'center_lat': tile.lat,
            'center_lng': tile.lon
        }

    def fetch_tile_data(self, tile: Tile, price_from: int, price_to: int) -> pd.DataFrame:
        """Fetch data for a single tile"""
        try:
            boundary = self.create_tile_boundary(tile)
            payload = self.prepare_payload(price_from, price_to)
            payload.update(boundary)
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return self.parse_property_data(data)
            
        except Exception as e:
            self.logger.error(f"Error fetching data for tile at {tile.lat}, {tile.lon}: {str(e)}")
            return pd.DataFrame()

    def fetch_all_properties(self, price_from: int, price_to: int) -> pd.DataFrame:
        """Complete process to fetch all properties using tiles"""
        try:
            # Step 1: Get tiles
            tiles_response = self.fetch_tiles(price_from, price_to)
            self.logger.info(f"Found {tiles_response.get('totalFound', 0)} total properties")
            
            # Parse tiles
            tiles = self.parse_tiles(tiles_response)
            self.logger.info(f"Processing {len(tiles)} tiles")

            # Step 2: Fetch data for each tile in parallel
            all_data = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_tile = {
                    executor.submit(self.fetch_tile_data, tile, price_from, price_to): tile 
                    for tile in tiles
                }
                
                for future in as_completed(future_to_tile):
                    tile = future_to_tile[future]
                    try:
                        df = future.result()
                        if not df.empty:
                            all_data.append(df)
                            self.logger.info(f"Successfully processed tile at {tile.lat}, {tile.lon}")
                    except Exception as e:
                        self.logger.error(f"Tile processing failed: {str(e)}")

            # Combine all results
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                # Remove duplicates based on property ID
                final_df = final_df.drop_duplicates(subset=['id'])
                return final_df
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error in fetch_all_properties: {str(e)}")
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