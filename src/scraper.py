"""Main scraper implementation for Calgary MLX"""

import requests
import pandas as pd
from typing import Dict, Any, List
from dataclasses import dataclass
import os
from datetime import datetime
import sys
import traceback
import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from .config import (
    BASE_URL,
    HEADERS,
    DEFAULT_SEARCH_PARAMS,
    DATA_DIR,
    DEFAULT_OUTPUT_FILE,
    LOG_FILE,
    COOKIES,
    START_YEAR,
    DEBUG_MODE,
    PRICE_FROM,
    PRICE_TO,
    PRICE_STEP,
    OMNI_SUBAREA_TEMPLATE,
    OMNI_COMMUNITY_TEMPLATE,
    LISTING_URL_PREFIX,
    LISTING_URL_TEMPLATE,
    LISTING_URL_CITY,
    PROPERTY_URL_FIELDS,
    SUBAREAS,
    COMMUNITIES,
    AREA_TYPES,
    CITY,
    PROVINCE,
    COUNTRY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    GEOCODER_USER_AGENT,
    GEOCODER_MAX_RETRIES,
    GEOCODER_RETRY_DELAY,
)
from .utils import (
    setup_logging,
    validate_price_range,
    format_property_data,
    repr_dict,
    random_sleep,
)
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
        self.geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT)

    def _initialize_cookies(self) -> Dict[str, str]:
        """Initialize cookies from stored file or default configuration"""
        stored_cookies = self.cookie_manager.load_cookies()
        if stored_cookies:
            self.logger.info("Using stored cookies")
            return stored_cookies

        self.logger.info("Using default cookies")
        self.cookie_manager.save_cookies(COOKIES)
        return COOKIES

    def fetch_tiles(
        self, subarea_code: str, subarea_info: dict, year: int
    ) -> Dict[str, Any]:
        """First API call to get the tiles information for a specific year"""
        try:
            payload = DEFAULT_SEARCH_PARAMS.copy()
            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range

            subarea_name = subarea_info["name"]

            area_type = subarea_info["type"]
            if area_type == "SUBAREA":
                omni = OMNI_SUBAREA_TEMPLATE.format(
                    subarea_code=subarea_code, subarea_name=subarea_name
                )
            elif area_type == "COMMUNITY":
                omni = OMNI_COMMUNITY_TEMPLATE.format(
                    subarea_code=subarea_code, subarea_name=subarea_name
                )
            else:
                raise ValueError(f"Unknown area type: {area_type}")

            payload["omni"] = omni

            # Debug request information
            self.debug.print_request_info(
                method="POST", url=self.base_url, headers=self.headers, payload=payload
            )

            self.logger.debug(f"Fetching tiles for year: {year}")

            response = requests.post(
                self.base_url, headers=self.headers, cookies=self.cookies, data=payload
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

    def create_tile_boundary(
        self, tile: Tile, radius: float = 0.02
    ) -> Dict[str, float]:
        """Create boundary coordinates for a single tile"""
        return {
            "sw_lat": tile.lat - radius,
            "sw_lng": tile.lon - radius,
            "ne_lat": tile.lat + radius,
            "ne_lng": tile.lon + radius,
            "center_lat": tile.lat,
            "center_lng": tile.lon,
        }

    def fetch_tile_data(
        self,
        tile: Tile,
        subarea_code: str,
        subarea_info: dict,
        year: int,
        radius: float = 0.02,
    ) -> pd.DataFrame:
        """Fetch data for a single tile"""
        try:
            boundary = self.create_tile_boundary(tile, radius)
            payload = DEFAULT_SEARCH_PARAMS.copy()

            year_range = f"{year}-{year}"
            payload["YEAR_BUILT"] = year_range
            payload.update(boundary)

            subarea_name = subarea_info["name"]

            area_type = subarea_info["type"]
            if area_type == "SUBAREA":
                omni = OMNI_SUBAREA_TEMPLATE.format(
                    subarea_code=subarea_code, subarea_name=subarea_name
                )
            elif area_type == "COMMUNITY":
                omni = OMNI_COMMUNITY_TEMPLATE.format(
                    subarea_code=subarea_code, subarea_name=subarea_name
                )
            else:
                raise ValueError(f"Unknown area type: {area_type}")

            payload["omni"] = omni

            # Debug request information
            self.debug.print_request_info(
                method="POST", url=self.base_url, headers=self.headers, payload=payload
            )

            response = requests.post(
                self.base_url, headers=self.headers, cookies=self.cookies, data=payload
            )
            response.raise_for_status()

            # Debug response information
            self.debug.print_response_info(response)

            data = response.json()

            # Debug pause
            if not self.debug.debug_pause(
                f"Fetching tile data for year {year}, lat: {tile.lat}, lon: {tile.lon}"
            ):
                raise SystemExit("Debug quit requested")
            else:
                # Sleep after the request
                random_sleep()

            # Check if we got any results
            if data.get("totalFound", 0) == 0 and not data.get("listings"):
                self.logger.debug(
                    f"No properties found for tile at {tile.lat}, {tile.lon}, {radius}"
                )
                return pd.DataFrame()

            return self.parse_property_data(year, data)

        except Exception as e:
            self.logger.error(
                f"Error fetching data for tile at {tile.lat}, {tile.lon}, year {year}: {str(e)}"
            )
            traceback.print_exc(file=sys.stdout)
            return pd.DataFrame()

    def parse_tiles(self, tiles_data: Dict[str, Any]) -> List[Tile]:
        """Parse the tiles response into Tile objects"""
        tiles = []
        for tile in tiles_data.get("tiles", []):
            tiles.append(
                Tile(
                    lat=tile["lat"],
                    lon=tile["lon"],
                    count=tile["count"],
                    id=tile["id"],
                    pixel_size=tile["pixelSize"],
                )
            )
        return tiles

    def fetch_properties(
        self, subarea_code: str, subarea_info: dict, year: int
    ) -> pd.DataFrame:
        """Fetch all properties for a specific year"""
        try:
            # Step 1: Get tiles for this year
            tiles_response = self.fetch_tiles(subarea_code, subarea_info, year)
            total_found = tiles_response.get("totalFound", 0)
            self.logger.info(f"Year {year}: Found {total_found} properties")

            if total_found == 0:
                return pd.DataFrame()

            # Parse tiles
            tiles = self.parse_tiles(tiles_response)
            self.logger.debug(f"Processing {len(tiles)} tiles for year {year}")

            # Step 2: Fetch data for each tile sequentially
            all_data = []
            for tile in tiles:
                self.logger.debug(
                    f"Processing tile at lat: {tile.lat}, lon: {tile.lon} for year {year}"
                )

                # First attempt with default radius
                df = self.fetch_tile_data(tile, subarea_code, subarea_info, year)

                if not df.empty:
                    all_data.append(df)
                    self.logger.debug(
                        f"Successfully processed tile with {len(df)} properties"
                    )
                    continue

                # If first attempt failed, try with reset location and smaller radius
                self.logger.debug(
                    "Initial fetch failed, attempting with reset location and smaller radius"
                )

                # Reset tile coordinates to subarea center
                tile.lat = subarea_info["latitude"]
                tile.lon = subarea_info["longitude"]

                self.logger.debug(
                    f"Retrying tile at lat: {tile.lat}, lon: {tile.lon} for year {year}"
                )
                df = self.fetch_tile_data(
                    tile, subarea_code, subarea_info, year, radius=0.03
                )

                if not df.empty:
                    all_data.append(df)
                    self.logger.debug(
                        f"Successfully processed tile with {len(df)} properties after reset"
                    )
                else:
                    self.logger.debug(
                        f"Failed to fetch data for tile even after location reset"
                    )

            # Combine all results for this year
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                final_df = final_df.drop_duplicates(subset=["id"])
                self.logger.debug(
                    f"Year {year}: Found {len(final_df)} unique properties"
                )

                if len(final_df) != total_found:
                    self.logger.warning(
                        f"Year {year}: Retrieved {len(final_df)} properties but expected {total_found}"
                    )

                return final_df
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error processing year {year}: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return pd.DataFrame()

    def fetch_all_years(self):
        # Get coordinates for all subareas first
        self.initialize_locations()

        self._fetch_all_years(self.subarea_coords)
        # self._fetch_all_years(self.community_coords)

    def _fetch_all_years(self, area_coords: list):
        """Fetch data for all years and subareas"""
        for subarea_code, subarea_info in area_coords.items():
            subarea_name = subarea_info["name"]
            subarea = subarea_name.replace(" ", "_")

            all_df = pd.DataFrame()

            self.logger.info(f"Processing subarea: {subarea_name} ({subarea_code})")

            for year in range(self.start_year, self.end_year + 1):
                self.logger.debug(f"Starting processing for year {year}")
                df = self.fetch_properties(subarea_code, subarea_info, year)

                if not df.empty:
                    all_df = pd.concat([all_df, df], ignore_index=True)
                    self.logger.info(f"Year {year}: Saved {len(df)} properties")
                else:
                    self.logger.debug(f"No properties found for year {year}")

            if all_df.size > 0:
                final_df = all_df.drop_duplicates(subset=["id"])
                self.logger.debug(
                    f"{subarea_name}: Found {len(final_df)} unique properties"
                )

                # Save each year's data to a separate file
                filename = f"calgary_properties_{subarea}.csv"
                self.save_to_csv(final_df, filename)
                self.logger.info(f"Saved {len(final_df)} properties of {subarea_name}")
            else:
                self.logger.warning(f"No properties found for {subarea_name}")

    def _add_avg_ft_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add average price per square foot column"""
        try:
            # Convert price and square_feet to numeric, handling any non-numeric values
            df["sold_price"] = pd.to_numeric(df["sold_price"], errors="coerce")
            df["square_feet"] = pd.to_numeric(df["square_feet"], errors="coerce")

            # Calculate price per square foot
            # Only calculate where both price and square feet are valid numbers and greater than 0
            mask = (df["sold_price"] > 0) & (df["square_feet"] > 0)
            df["avg_ft_price"] = 0.0  # Initialize column
            df.loc[mask, "avg_ft_price"] = (
                df.loc[mask, "sold_price"] / df.loc[mask, "square_feet"]
            )

            # Format to 2 decimal places
            df["avg_ft_price"] = df["avg_ft_price"].round(2)

            return df
        except Exception as e:
            print(f"Error calculating average price per square foot: {str(e)}")
            return df

    def parse_property_data(
        self, year: int, response_data: Dict[str, Any]
    ) -> pd.DataFrame:
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
                prop["year"] = year
                prop["url"] = self.format_listing_url(prop)

            # Convert to DataFrame
            df = pd.DataFrame(properties)

            # Standardize column names if needed
            column_mapping = {
                "LIST_ID": "id",
                "STREET_NUMBER": "street_number",
                "STREET_NAME": "street_name",
                "STREET_DIR": "street_direction",
                "STREET_TYPE": "street_type",
                "CITY": "city",
                "POSTAL_CODE": "postal_code",
                "PRICE_RAW": "list_price",
                "SOLD_PRICE_RAW": "sold_price",
                "LISTED_DATE": "list_date",
                "SOLD_DATE": "sold_date",
                "AREA_SQ_FEET": "square_feet",
                "MLS_NUM": "mls_number",
                "TOTAL_BEDROOMS": "bedrooms",
                "TOTAL_BATHS": "bathrooms",
                "LATITUDE": "latitude",
                "LONGITUDE": "longitude",
                "AGENT_NAME": "agent",
                "OFFICE_NAME": "office",
                "LIST_SUBAREA": "neighborhood",
                "url": "detail_url",
                "year": "built_year",
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Select and order columns
            columns_to_keep = list(column_mapping.values())
            df = df[columns_to_keep]

            # Add metadata
            df["fetch_date"] = datetime.now().strftime("%Y-%m-%d")

            # Add average price per square foot
            df = self._add_avg_ft_price(df)

            self.logger.debug(f"Successfully parsed {len(df)} properties")
            return df

        except Exception as e:
            self.logger.error(f"Error parsing property data: {str(e)}")
            traceback.print_exc(file=sys.stdout)
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
                str(property_data.get(field, ""))
                for field in PROPERTY_URL_FIELDS["street_parts"]
            ]

            # Clean and join street parts
            street_address = "-".join(filter(None, street_parts)).lower()
            street_address = street_address.replace(" ", "-")

            # Format postal code
            postal_code = str(property_data.get("POSTAL_CODE", "")).lower()
            postal_code = postal_code.replace(" ", "-")

            # Check required fields
            for field in PROPERTY_URL_FIELDS["required_fields"]:
                if not property_data.get(field):
                    self.logger.warning(f"Missing required field for URL: {field}")
                    return ""

            # Construct URL using template
            url = LISTING_URL_TEMPLATE.format(
                prefix=LISTING_URL_PREFIX,
                mls_number=str(property_data.get("MLS_NUM", "")).lower(),
                street_address=street_address,
                postal_code=postal_code,
                listing_id=str(property_data.get("LIST_ID", "")),
            )

            return url
        except Exception as e:
            self.logger.error(f"Error formatting listing URL: {str(e)}")
            return ""

    def get_area_coordinates(self, area_name: str) -> tuple:
        """
        Get the coordinates for a given area using geopy
        Returns a tuple of (latitude, longitude)
        """
        try:
            # Format the search query
            search_query = f"{area_name}, {CITY}, {PROVINCE}, {COUNTRY}"
            self.logger.info(f"Getting coordinates for: {search_query}")

            for attempt in range(GEOCODER_MAX_RETRIES):
                try:
                    # Get the location
                    location = self.geolocator.geocode(search_query)

                    if location:
                        self.logger.info(
                            f"Found coordinates for {area_name}: ({location.latitude}, {location.longitude})"
                        )
                        return (location.latitude, location.longitude)

                    # If no results found, try with just the area name and city
                    if attempt == 0:
                        search_query = f"{area_name}, {CITY}, {COUNTRY}"
                        continue

                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    if attempt < GEOCODER_MAX_RETRIES - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. Retrying..."
                        )
                        time.sleep(GEOCODER_RETRY_DELAY)
                        continue
                    raise

            # If we get here, no location was found
            self.logger.error(f"Could not find coordinates for {area_name}")
            # Return default Calgary coordinates as fallback
            return (DEFAULT_LATITUDE, DEFAULT_LONGITUDE)

        except Exception as e:
            self.logger.error(f"Error getting coordinates for {area_name}: {str(e)}")
            # Return default Calgary coordinates as fallback
            return (DEFAULT_LATITUDE, DEFAULT_LONGITUDE)

    def initialize_locations(self):
        """Initialize subareas with their coordinates and location info"""
        self.subarea_coords = self._initialize_coordinates("SUBAREA", SUBAREAS)
        # self.community_coords = self._initialize_coordinates("COMMUNITY", COMMUNITIES)

    def _initialize_coordinates(self, area_type: str, coords: dict) -> list:
        area_coords = {}
        for area_code, area_name in coords.items():
            location_data = self.get_area_coordinates(area_name)
            area_coords[area_code] = {
                "name": area_name,
                "type": area_type,
                "latitude": location_data[0],
                "longitude": location_data[1],
            }

            # Debug pause
            if not self.debug.debug_pause(
                f"Fetching location data for {area_name} [{area_code}]"
            ):
                raise SystemExit("Debug quit requested")
            else:
                # Sleep after the request
                random_sleep()

        return area_coords
