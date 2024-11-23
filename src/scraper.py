"""Main scraper implementation for Calgary MLX"""

import requests
import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass
import os
from datetime import datetime
import sys
import traceback

from .config import (
    BASE_URL, HEADERS, DEFAULT_SEARCH_PARAMS,
    DATA_DIR, DEFAULT_OUTPUT_FILE, LOG_FILE, COOKIES,
    START_YEAR, DEBUG_MODE,
    OMNI_TEMPLATE,
    LISTING_URL_PREFIX, LISTING_URL_TEMPLATE, LISTING_URL_CITY,
    PROPERTY_URL_FIELDS,
    SUBAREAS,
)
from .utils import setup_logging, validate_price_range, format_property_data, repr_dict, random_sleep
from .cookie_manager import CookieManager
from .debug_utils import DebugHelper

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
        self.start_year = START_YEAR
        self.end_year = datetime.now().year
        self.debug = DebugHelper(DEBUG_MODE)

    def _initialize_cookies(self) -> Dict[str, str]:
        """Initialize cookies from stored file or default configuration"""
        stored_cookies = self.cookie_manager.load_cookies()
        if stored_cookies:
            self.logger.info("Using stored cookies")
            return stored_cookies
        
        self.logger.info("Using default cookies")
        self.cookie_manager.save_cookies(COOKIES)
        return COOKIES

    def fetch_tiles(self, subarea_code: str, year: int) -> Dict[str, Any]:
        """First API call to get the tiles information for a specific year"""
        try:
            payload = DEFAULT_SEARCH_PARAMS.copy()
            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range

            subarea_name = SUBAREAS[subarea_code]
            omni = OMNI_TEMPLATE.format(subarea_code=subarea_code, subarea_name=subarea_name)
            payload["omni"] = omni
            
            # Debug request information
            self.debug.print_request_info(
                method="POST",
                url=self.base_url,
                headers=self.headers,
                payload=payload
            )

            self.logger.info(f"Fetching tiles for year: {year}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()
            
            # Debug response information
            self.debug.print_response_info(response)
            
            # Debug pause
            if not self.debug.debug_pause(f"Fetching tiles for year {year}"):
                raise SystemExit("Debug quit requested")
            else:
                # Sleep after the request
                random_sleep()
            
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

    def fetch_tile_data(self, tile: Tile, subarea_code: str, year: int) -> pd.DataFrame:
        """Fetch data for a single tile"""
        try:
            boundary = self.create_tile_boundary(tile)
            payload = DEFAULT_SEARCH_PARAMS.copy()

            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range
            payload.update(boundary)
            
            subarea_name = SUBAREAS[subarea_code]
            omni = OMNI_TEMPLATE.format(subarea_code=subarea_code, subarea_name=subarea_name)
            payload["omni"] = omni
 
            # Debug request information
            self.debug.print_request_info(
                method="POST",
                url=self.base_url,
                headers=self.headers,
                payload=payload
            )
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload
            )
            response.raise_for_status()
            
            # Debug response information
            self.debug.print_response_info(response)
            
            data = response.json()
            
            # Check if we got any results
            if data.get('totalFound', 0) == 0 and not data.get('listings'):
                self.logger.info(f"No properties found for tile at {tile.lat}, {tile.lon}")
                return pd.DataFrame()
            
            # Debug pause
            if not self.debug.debug_pause(f"Fetching tile data for year {year}, lat: {tile.lat}, lon: {tile.lon}"):
                raise SystemExit("Debug quit requested")
            else:
                # Sleep after the request
                random_sleep()

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

    def fetch_properties_by_subarea_year(self, subarea_code: str, year: int) -> pd.DataFrame:
        """Fetch all properties for a specific year"""
        try:
            # Step 1: Get tiles for this year
            tiles_response = self.fetch_tiles(subarea_code, year)
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
                df = self.fetch_tile_data(tile, subarea_code, year)
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
            traceback.print_exc(file=sys.stdout)
            return pd.DataFrame()

    def fetch_all_years(self):
        """Fetch data for all years and subareas"""
        for subarea_code, subarea_name in SUBAREAS.items():
            self.logger.info(f"Processing subarea: {subarea_name} ({subarea_code})")

            """Process all years from START_YEAR to current year"""
            for year in range(self.start_year, self.end_year + 1):
                self.logger.info(f"Starting processing for year {year}")
                df = self.fetch_properties_by_subarea_year(subarea_code, year)
                
                if not df.empty:
                    subarea = subarea_name.replace(' ', '_')
                    # Save each year's data to a separate file
                    filename = f"calgary_properties_{subarea}_{year}.csv"
                    self.save_to_csv(df, filename)
                    self.logger.info(f"Saved {len(df)} properties of {subarea_name} for year {year}")
                else:
                    self.logger.info(f"No properties found for year {year}")

    def parse_property_data(self, response_data: Dict[str, Any]) -> pd.DataFrame:
        """Parse the response data into a structured format, handling both response types"""
        try:
            properties = []
            
            # Handle Type 1 response (listings dictionary)
            if "listings" in response_data:
                for listing_id, listing_data in response_data["listings"].items():
                    properties.append(listing_data)
            
            # Handle Type 2 response (results array)
            elif "results" in response_data:
                properties.extend(response_data["results"])
            
            if not properties:
                self.logger.info("No properties found in response")
                return pd.DataFrame()

            # Add formatted URL
            for prop in properties:
                prop['url'] = self.format_listing_url(prop)

            # Convert to DataFrame
            df = pd.DataFrame(properties)
            
            # Standardize column names if needed
            column_mapping = {
                'LIST_ID': 'id',
                'STREET_NUMBER': 'street_number',
                'STREET_NAME': 'street_name',
                'STREET_DIR': 'street_direction',
                'STREET_TYPE': 'street_type',
                'CITY': 'city',
                'POSTAL_CODE': 'postal_code',
                'PRICE_RAW': 'list_price',
                'SOLD_PRICE_RAW': 'sold_price',
                'LISTED_DATE': 'list_date',
                'SOLD_DATE': 'sold_date',
                'AREA_SQ_FEET': 'square_feet',
                'MLS_NUM': 'mls_number',
                'TOTAL_BEDROOMS': 'bedrooms',
                'TOTAL_BATHS': 'bathrooms',
                'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude',
                'AGENT_NAME': 'agent',
                'OFFICE_NAME': 'office',
                'LIST_SUBAREA': 'neighborhood',
                'url': 'detail_url',
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Select and order columns
            columns_to_keep = list(column_mapping.values())
            df = df[columns_to_keep]
            
            # Add metadata
            df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
            
            self.logger.info(f"Successfully parsed {len(df)} properties")
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing property data: {str(e)}")
            raise

    def save_to_csv(self, df: pd.DataFrame, filename: str = DEFAULT_OUTPUT_FILE):
        """Save the processed data to a CSV file"""
        try:
            # Ensure the data directory exists
            os.makedirs(DATA_DIR, exist_ok=True)

            pathname = os.path.join(DATA_DIR, filename)

            df.to_csv(pathname, index=False)
            self.logger.info(f"Data saved successfully to {pathname}")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise 

    def format_listing_url(self, property_data: Dict) -> str:
        """Format the listing URL based on property data and config settings"""
        try:
            # Format street components
            street_parts = [
                str(property_data.get(field, ''))
                for field in PROPERTY_URL_FIELDS['street_parts']
            ]
            
            # Clean and join street parts
            street_address = '-'.join(filter(None, street_parts)).lower()
            street_address = street_address.replace(' ', '-')
            
            # Format postal code
            postal_code = str(property_data.get('POSTAL_CODE', '')).lower()
            postal_code = postal_code.replace(' ', '-')
            
            # Check required fields
            for field in PROPERTY_URL_FIELDS['required_fields']:
                if not property_data.get(field):
                    self.logger.warning(f"Missing required field for URL: {field}")
                    return ""
            
            # Construct URL using template
            url = LISTING_URL_TEMPLATE.format(
                prefix=LISTING_URL_PREFIX,
                mls_number=str(property_data.get('MLS_NUM', '')).lower(),
                street_address=street_address,
                postal_code=postal_code,
                listing_id=str(property_data.get('LIST_ID', ''))
            )
            
            return url
        except Exception as e:
            self.logger.error(f"Error formatting listing URL: {str(e)}")
            return ""
