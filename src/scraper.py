"""Main scraper implementation for Calgary MLX"""

import requests
import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass
import os
from datetime import datetime

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
        self.start_year = 1980
        self.end_year = datetime.now().year

    def _initialize_cookies(self) -> Dict[str, str]:
        """Initialize cookies from stored file or default configuration"""
        stored_cookies = self.cookie_manager.load_cookies()
        if stored_cookies:
            self.logger.info("Using stored cookies")
            return stored_cookies
        
        self.logger.info("Using default cookies")
        self.cookie_manager.save_cookies(COOKIES)
        return COOKIES

    def fetch_tiles(self, year: int) -> Dict[str, Any]:
        """First API call to get the tiles information for a specific year"""
        try:
            payload = DEFAULT_SEARCH_PARAMS.copy()
            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range
            self.logger.info(f"Fetching tiles for year: {year}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching tiles for year {year}: {str(e)}")
            raise

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

    def fetch_tile_data(self, tile: Tile, year: int) -> pd.DataFrame:
        """Fetch data for a single tile"""
        try:
            boundary = self.create_tile_boundary(tile)
            payload = DEFAULT_SEARCH_PARAMS.copy()
            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range
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
            self.logger.error(f"Error fetching data for tile at {tile.lat}, {tile.lon}, year {year}: {str(e)}")
            return pd.DataFrame()

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

    def fetch_properties_by_year(self, year: int) -> pd.DataFrame:
        """Fetch all properties for a specific year"""
        try:
            # Step 1: Get tiles for this year
            tiles_response = self.fetch_tiles(year)
            total_found = tiles_response.get('totalFound', 0)
            self.logger.info(f"Found {total_found} properties for year {year}")
            
            if total_found == 0:
                return pd.DataFrame()

            # Parse tiles
            tiles = self.parse_tiles(tiles_response)
            self.logger.info(f"Processing {len(tiles)} tiles for year {year}")

            # Step 2: Fetch data for each tile sequentially
            all_data = []
            for tile in tiles:
                self.logger.info(f"Processing tile at lat: {tile.lat}, lon: {tile.lon} for year {year}")
                df = self.fetch_tile_data(tile, year)
                if not df.empty:
                    all_data.append(df)
                    self.logger.info(f"Successfully processed tile with {len(df)} properties")

            # Combine all results for this year
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                final_df = final_df.drop_duplicates(subset=['id'])
                self.logger.info(f"Year {year}: Found {len(final_df)} unique properties")
                return final_df
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error processing year {year}: {str(e)}")
            return pd.DataFrame()

    def fetch_all_years(self) -> None:
        """Process all years from 1980 to current year"""
        for year in range(self.start_year, self.end_year + 1):
            self.logger.info(f"Starting processing for year {year}")
            df = self.fetch_properties_by_year(year)
            
            if not df.empty:
                # Save each year's data to a separate file
                filename = f"calgary_properties_{year}.csv"
                self.save_to_csv(df, filename)
                self.logger.info(f"Saved {len(df)} properties for year {year}")
            else:
                self.logger.info(f"No properties found for year {year}")

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