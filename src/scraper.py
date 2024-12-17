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
    HOME_URL,
    SEARCH_URL,
    HEADERS,
    PROPERTIES_TYPES,
    DEFAULT_SEARCH_PARAMS,
    DATA_DIR,
    DATABASE_DIR,
    DEFAULT_OUTPUT_FILE,
    LOG_FILE,
    DEFAULT_DB_FILE,
    COOKIES,
    START_YEAR,
    END_YEAR,
    DEBUG_MODE,
    PRICE_FROM,
    PRICE_TO,
    PRICE_STEP,
    MIN_PRICE_STEP,
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
    getch,
)
from .debug_utils import DebugHelper
from .database import (
    create_connection,
    create_property_table,
    update_price_differences,
    create_area_coordinates_table,
    get_area_coordinates,
    save_area_coordinates,
)

from .api import Tile, MLXAPI, MLXAPIResponse, APIError


class CalgaryMLXScraper:
    def __init__(self):
        self.logger = setup_logging(LOG_FILE)
        self.start_year = START_YEAR
        self.end_year = END_YEAR if END_YEAR > 0 else datetime.now().year
        self.debug = DebugHelper(DEBUG_MODE)
        self.geolocator = Nominatim(user_agent=GEOCODER_USER_AGENT)
        self.api = MLXAPI(self.logger, self.debug)

        self._init_db()

    def _init_db(self, db_file: str = DEFAULT_DB_FILE):
        """Save the processed data to a CSV file"""
        try:
            # Ensure the database directory exists
            os.makedirs(DATABASE_DIR, exist_ok=True)

            db_file = os.path.join(DATABASE_DIR, db_file)

            self.conn = create_connection(db_file)

            for property_name, property_type in PROPERTIES_TYPES.items():
                create_property_table(self.conn, property_type["name"])

            self.logger.debug(f"Database created successfully to {db_file}")
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            raise

    def fetch_properties(
        self,
        subarea_code: str,
        subarea_info: dict,
        year: int,
        property_name: str,
        property_type: dict,
        price_from: int = 0,
        price_to: int = 0,
    ) -> dict:
        """Fetch all properties for a specific year and refine the process"""
        result = {"count": 0, "df": pd.DataFrame(), "found_all": True}

        try:
            # Initialize tiles with a default tile and a tile based on subarea_info
            tiles = [
                Tile(0, 0, 0, 0, 0),
                Tile(subarea_info["latitude"], subarea_info["longitude"], 0, 1, 0),
            ]

            # Initialize flags and counters
            is_first = True
            total_found = 0
            all_df = pd.DataFrame()
            new_tiles_count = 0
            dwelling_type = property_type["type"]

            # Iterate through tiles to fetch properties
            for i, tile in enumerate(tiles):
                self.logger.debug(
                    f"Processing tile {i}: {tile.id}, {tile.count}, {price_from}-{price_to}"
                )
                response = self.api.search(
                    subarea_code,
                    subarea_info,
                    year,
                    dwelling_type,
                    tile,
                    price_from,
                    price_to,
                )

                # Process the first response to get total_found
                if is_first:
                    total_found = response.total_found
                    is_first = False

                    self.logger.info(
                        f"Year {year} and Price {price_from}-{price_to}: Found {total_found} properties"
                    )
                    if total_found == 0:
                        return result

                # Parse and concatenate property data
                df = self.parse_property_data(year, response)
                all_df = pd.concat([all_df, df], ignore_index=True)
                all_df = all_df.drop_duplicates(subset=["id"])

                # Check if all properties have been retrieved
                total_retrived = len(all_df)
                if total_retrived >= total_found:
                    self.logger.info(f"Year {year}: Found all {total_found} properties")
                    break

                # Add new tiles to the list if not already present
                for new_tile in response.tiles:
                    if new_tile not in tiles:
                        tiles.append(new_tile)
                        new_tiles_count += 1
                        self.logger.debug(
                            f"Added new tile {new_tile.id}: {new_tile.count}"
                        )

            # Log new tiles count
            if new_tiles_count > 0:
                self.logger.debug(f"Year {year}: Added {new_tiles_count} new tiles")

            # Log processed tiles count
            self.logger.debug(f"Year {year}: Processed {len(tiles)} tiles")

            # Check if all expected properties were retrieved
            if total_retrived != total_found:
                self.logger.warning(
                    f"Year {year}: Retrieved {total_retrived} properties but expected {total_found}"
                )

            # Save the fetched properties to the database
            table_name = property_type["name"]
            self.save_to_database(table_name, all_df)

            result["count"] = len(all_df)
            result["df"] = all_df
            result["found_all"] = total_retrived == total_found

            return result

        except Exception as e:
            self.logger.error(f"Error processing year {year}: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            return result

    def fetch_properties_by_prices(
        self,
        subarea_code: str,
        subarea_info: dict,
        year: int,
        property_name: str,
        property_type: dict,
        count: int,
        price_from: int = PRICE_FROM,
        price_to: int = PRICE_TO,
        price_step: int = PRICE_STEP,
    ) -> dict:

        result = {"count": 0, "df": pd.DataFrame(), "found_all": True}

        if price_step < MIN_PRICE_STEP:
            self.logger.warning(
                f"Price step {price_step} is less than minimal {MIN_PRICE_STEP}"
            )
            return result

        all_df = pd.DataFrame()
        for price in range(price_from, price_to, price_step):
            result = self.fetch_properties(
                subarea_code,
                subarea_info,
                year,
                property_name,
                property_type,
                price_from=price,
                price_to=price + price_step,
            )

            if result["count"] == 0:
                continue

            all_df = pd.concat([all_df, result["df"]], ignore_index=True)

            if not result["found_all"]:
                result = self.fetch_properties_by_prices(
                    subarea_code,
                    subarea_info,
                    year,
                    property_name,
                    property_type,
                    count,
                    price,
                    price + price_step,
                    int(price_step / 10),
                )

                if result["count"] > 0:
                    all_df = pd.concat([all_df, result["df"]], ignore_index=True)

        result["count"] = len(all_df)
        result["df"] = all_df
        result["found_all"] = len(all_df) == count

        return result

    def fetch_properties_by_year(
        self,
        subarea_code: str,
        subarea_info: dict,
        year: int,
        property_name: str,
        property_type: dict,
    ) -> pd.DataFrame:

        self.logger.debug(f"Starting processing for year {year}")
        result = self.fetch_properties(subarea_code, subarea_info, year)

        if result["count"] == 0:
            self.logger.debug(f"No properties found for year {year}")
            return pd.DataFrame()

        df = pd.DataFrame()
        if not result["found_all"]:
            new_result = self.fetch_properties_by_prices(
                subarea_code,
                subarea_info,
                year,
                property_name,
                property_type,
                count=result["count"],
            )

            new_df = new_result["df"]
            df = pd.concat([df, new_df], ignore_index=True)

        df = pd.concat([df, result["df"]], ignore_index=True)
        if not df.empty:
            df = df.drop_duplicates(subset=["id"])
            self.logger.info(f"Year {year}: Saved {len(df)} properties")

        return df

    def fetch_all_years(
        self, subareas: dict = SUBAREAS, communities: dict = COMMUNITIES
    ):
        # Get coordinates for all subareas first
        self.initialize_locations(subareas, communities)

        self._fetch_locations(self.subarea_coords)
        self._fetch_locations(self.community_coords)

        self.update_database()

    def _fetch_locations(self, area_coords: list):
        """Fetch data for all years and subareas"""
        for subarea_code, subarea_info in area_coords.items():
            self._fetch_location(subarea_code, subarea_info)

    def _fetch_location(self, subarea_code: str, subarea_info: dict):
        for property_name, property_type in PROPERTIES_TYPES.items():
            self.logger.info(
                f"Search properties of {property_type['display-name']} ..."
            )
            self._fetch_location_with_type(
                subarea_code, subarea_info, property_name, property_type
            )

    def _fetch_location_with_type(
        self,
        subarea_code: str,
        subarea_info: dict,
        property_name: str,
        property_type: type,
    ):
        subarea_name = subarea_info["name"]

        all_df = pd.DataFrame()

        self.logger.info(f"Processing subarea: {subarea_name} ({subarea_code})")

        for year in range(self.start_year, self.end_year + 1):
            self.logger.debug(f"Starting processing for year {year}")
            result = self.fetch_properties(
                subarea_code, subarea_info, year, property_name, property_type
            )

            if result["found_all"] and result["count"] == 0:
                self.logger.debug(f"No properties found for year {year}")
                continue

            df = pd.DataFrame()
            if not result["found_all"]:
                new_result = self.fetch_properties_by_prices(
                    subarea_code,
                    subarea_info,
                    year,
                    property_name,
                    property_type,
                    count=result["count"],
                )

                new_df = new_result["df"]
                df = pd.concat([df, new_df], ignore_index=True)

                # TODO: if not found all

            df = pd.concat([df, result["df"]], ignore_index=True)
            if not df.empty:
                df = df.drop_duplicates(subset=["id"])
                all_df = pd.concat([all_df, df], ignore_index=True)
                self.logger.info(f"Year {year}: Saved {len(df)} properties")

        if all_df.size > 0:
            final_df = all_df.drop_duplicates(subset=["id"])
            self.logger.debug(
                f"{subarea_name}: Found {len(final_df)} unique properties"
            )

            # Save each year's data to a separate file
            subarea = (
                subarea_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            )
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

    def parse_property_data(self, year: int, response: MLXAPIResponse) -> pd.DataFrame:
        """Parse the response data into a structured format, handling both response types"""
        try:
            if not response.listings:
                self.logger.debug("No properties found in response")
                return pd.DataFrame()

            # Add formatted URL
            for prop in response.listings:
                prop["year"] = year
                prop["url"] = self.format_listing_url(prop)

            # Convert to DataFrame
            df = pd.DataFrame(response.listings)

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
            self.logger.debug(f"Data saved successfully to {pathname}")

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

    def _get_area_coordinates(self, area_name: str, area_code: str = "") -> tuple:
        """
        Get the coordinates for a given area using database cache or geopy
        Returns a tuple of (latitude, longitude)
        """
        try:
            # Try to get coordinates from database first
            coords = get_area_coordinates(self.conn, area_name, CITY, PROVINCE, COUNTRY)

            if coords:
                self.logger.info(
                    f"Found coordinates for {area_name} in database: ({coords[0]}, {coords[1]})"
                )
                return coords

            # If not in database, search online
            search_query = f"{area_name}, {CITY}, {PROVINCE}, {COUNTRY}"
            self.logger.info(f"Getting coordinates for: {search_query}")

            for attempt in range(GEOCODER_MAX_RETRIES):
                try:
                    location = self.geolocator.geocode(search_query)

                    # Sleep after the request
                    random_sleep()

                    if location:
                        # Save coordinates to database
                        save_area_coordinates(
                            self.conn,
                            area_name,
                            area_code,
                            CITY,
                            PROVINCE,
                            COUNTRY,
                            location.latitude,
                            location.longitude,
                        )

                        self.logger.info(
                            f"Found and saved coordinates for {area_name}: ({location.latitude}, {location.longitude})"
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

    def initialize_locations(
        self, subareas: dict = SUBAREAS, communities: dict = COMMUNITIES
    ):
        """Initialize subareas with their coordinates and location info"""
        self.subarea_coords = self._initialize_coordinates("SUBAREA", subareas)
        self.community_coords = self._initialize_coordinates("COMMUNITY", communities)

    def _initialize_coordinates(self, area_type: str, coords: dict) -> list:

        create_area_coordinates_table(self.conn)

        area_coords = {}
        for area_code, area_name in coords.items():
            location_data = self._get_area_coordinates(area_name)
            area_coords[area_code] = {
                "name": area_name,
                "type": area_type,
                "latitude": location_data[0],
                "longitude": location_data[1],
            }

        return area_coords

    def save_to_database(self, table_name, df: pd.DataFrame):
        """Save the DataFrame to the SQLite database, updating existing records."""
        try:
            for i in range(len(df)):
                try:
                    df.iloc[i : i + 1].to_sql(
                        table_name, self.conn, if_exists="append", index=False
                    )
                except Exception:
                    pass  # or any other action

            self.logger.debug(f"Saved {len(df)} records into database")
        except Exception as e:
            self.logger.error(f"Error saving data to database: {str(e)}")

    def update_database(self):
        try:
            # Update price differences after saving new data
            for property_name, property_type in PROPERTIES_TYPES.items():
                update_price_differences(self.conn, property_type["name"])
        except Exception as e:
            self.logger.error(f"Error updating data to database: {str(e)}")
