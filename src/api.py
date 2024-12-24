import logging
import re
import requests
import sys
import traceback
import time

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup

from .cookie_manager import CookieManager
from .debug_utils import DebugHelper
from .config import (
    HOME_URL,
    SEARCH_URL,
    TYPEAHEAD_URL,
    HEADERS,
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


@dataclass
class Tile:
    """Represents a tile with geographical coordinates."""

    lat: float
    lon: float
    count: int
    id: int
    pixel_size: int

    def __eq__(self, other: object) -> bool:
        """Compare tiles based on their IDs."""
        if not isinstance(other, Tile):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Make Tile hashable using tile_id."""
        return hash(self.id)


class MLXAPIResponse:
    """Handles the standardized response format from MLX API."""

    def __init__(self, response_data: Dict):
        """Initialize with raw API response data."""
        self.raw_data = response_data
        self._total_found = response_data.get("totalFound", 0)
        self._tiles = self._parse_tiles(response_data.get("tiles", []))
        self._listings = self._parse_listings(response_data)

    @property
    def total_found(self) -> int:
        """Get total number of results found."""
        return self._total_found

    @property
    def tiles(self) -> List[Tile]:
        """Get list of tiles from the response."""
        return self._tiles

    @property
    def listings(self) -> List[Dict]:
        """Get list of property listings from the response."""
        return self._listings

    def _parse_tiles(self, tiles_data: List[Dict]) -> List[Tile]:
        """Parse tiles data into Tile objects."""
        return [
            Tile(
                lat=tile.get("lat", 0),
                lon=tile.get("lon", 0),
                count=tile.get("count", 0),
                id=tile.get("id", 0),
                pixel_size=tile.get("pixelSize", 0),
            )
            for tile in tiles_data
        ]

    def _parse_listings(self, response_data: Dict) -> List[Dict]:
        """Parse listings from response data, handling different response formats."""
        properties = []

        # Handle Type 1 response (listings dictionary)
        if "listings" in response_data:
            for listing_id, listing_data in response_data["listings"].items():
                properties.append(listing_data)

        # Handle Type 2 response (results array)
        elif "results" in response_data:
            properties.extend(response_data["results"])

        return properties


class MLXAPI:
    """Handles API requests to MLX service."""

    def __init__(self, logger: logging.Logger, debug: DebugHelper):
        self.home_url = HOME_URL
        self.search_url = SEARCH_URL
        self.headers = HEADERS
        self.logger = logger
        self.debug = debug
        self.cookie_manager = CookieManager()
        self.cookies = self._initialize_cookies()

    def _initialize_cookies(self) -> Dict[str, str]:
        # Make a GET request
        response = requests.get(self.home_url)

        # Print all cookies
        for cookie in response.cookies:
            print(f"{cookie.name}: {cookie.value}")

        return response.cookies

    def _create_tile_boundary(
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

    def search(
        self,
        subarea_code: str,
        subarea_info: dict,
        year_from: int,
        year_to: int,
        dwelling_type: str,
        tile: Tile = None,
        price_from: int = 0,
        price_to: int = 0,
        radius: float = 0.02,
    ) -> MLXAPIResponse:
        """Fetch data from the search API"""
        try:
            payload = DEFAULT_SEARCH_PARAMS.copy()

            year_range = f"{year_from}-{year_to}"
            payload["YEAR_BUILT"] = year_range

            property_type = f"RESI|DWELLING_TYPE@{dwelling_type}"
            payload["PROPERTY_TYPE"] = property_type
            payload["DWELLING_TYPE"] = dwelling_type

            if tile and tile.id != 0:
                boundary = self._create_tile_boundary(tile, radius)
                payload.update(boundary)

            if price_from > 0 and price_to > 0:
                payload["price-from"] = price_from
                payload["price-to"] = price_to

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
                method="POST",
                url=self.search_url,
                headers=self.headers,
                payload=payload,
            )

            response = requests.post(
                self.search_url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload,
            )
            response.raise_for_status()

            # Debug response information
            self.debug.print_response_info(response)

            # Sleep after the request
            random_sleep()

            return MLXAPIResponse(response.json())

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            raise APIError(
                f"Error fetching data for tile at {tile.lat}, {tile.lon}, year {year_from} - {year_to}: {str(e)}"
            )

    def get_built_year_from_url(self, url: str, max_retries: int = 3, retry_delay: int = 2) -> Optional[int]:
        """
        Parse HTML from URL to extract built year with retry logic
        Returns the year as integer or None if not found
        
        Args:
            url: The URL to fetch
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
        """
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Fetching built year from URL: {url} (Attempt {attempt + 1}/{max_retries})")
                
                # Make GET request to URL with timeout
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    cookies=self.cookies,
                    timeout=10  # 10 seconds timeout
                )
                response.raise_for_status()
                
                self.logger.debug(f"Response status code: {response.status_code}")
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the span with class 'year' and then its nested highlight span
                year_span = soup.find('span', class_='year')
                if year_span:
                    self.logger.debug("Found year span")
                    highlight_span = year_span.find('span', class_='highlight')
                    if highlight_span:
                        self.logger.debug(f"Found highlight span with text: {highlight_span.text}")
                        try:
                            year = int(highlight_span.text.strip())
                            self.logger.debug(f"Successfully parsed year: {year}")
                            return year
                        except ValueError:
                            self.logger.error(f"Found year text but couldn't convert to integer: {highlight_span.text}")
                            # Continue to retry for ValueError
                    else:
                        self.logger.debug("No highlight span found within year span")
                else:
                    self.logger.debug("No year span found in HTML")
                
                if attempt < max_retries - 1:
                    self.logger.warning(f"Retry attempt {attempt + 1} failed, waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.warning(f"No built year found in {url} after {max_retries} attempts")

            except requests.Timeout:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Timeout error fetching URL {url} after {max_retries} attempts")
                    return None
                    
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Request error fetching URL {url} after {max_retries} attempts: {str(e)}")
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Error on attempt {attempt + 1}: {str(e)}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Error parsing HTML from URL {url} after {max_retries} attempts: {str(e)}")
                    return None

        return None


class TypeaheadAPIResponse:
    """Handles the standardized response format from MLX API."""

    def __init__(self, response_data: Dict):
        """Initialize with raw API response data."""
        self.raw_data = response_data

        self._subareas = []
        self._communities = []

        self._parse(response_data)

    @property
    def subareas(self) -> List[Dict]:
        """Get list of subareas from the response."""
        return self._subareas

    @property
    def communities(self) -> List[Dict]:
        """Get list of communities from the response."""
        return self._communities

    def _existing(self, locations, new_location):

        for location in locations:
            if location["code"] == new_location["code"]:
                return True
        
        return False

    def _parse_location_item(self, item: List) -> Dict:
        """Parse a location item from the API response"""
        type_code, name, confidence, polygon = item

        # Extract the code from type_code (e.g., "list_subarea:C-508" -> "C-508")
        code = type_code.split(":")[1]

        return {
            "code": code,
            "name": re.sub(r"\s*\([^)]*\)", "", name),  # Remove text in parentheses
            "confidence": confidence,
            "polygon": polygon,
        }

    def _parse(self, response_data: Dict):
        for item in response_data:
            type_code = item[0]

            if type_code.startswith("list_subarea:"):
                data = self._parse_location_item(item)
                if not self._existing(self._subareas, data):
                    self._subareas.append(data)

            elif type_code.startswith("community:"):
                data = self._parse_location_item(item)
                if not self._existing(self._communities, data):
                    self._communities.append(data)


class TypeaheadAPI:
    def __init__(self, url: str = TYPEAHEAD_URL):
        self.url = url
        self.session = requests.Session()

    def search(self, query: str, listing_type: str = "AUTO") -> Dict:
        """Search locations using typeahead API"""
        try:
            params = {"listingType": listing_type, "q": query}

            response = self.session.get(self.url, params=params)
            response.raise_for_status()
            # print(response.text)
            return response.json()
        except Exception as e:
            # traceback.print_exc(file=sys.stdout)
            raise APIError(
                f"Error fetching location for {query}: {str(e)}"
            )

    def search_all(self, location: str) -> TypeaheadAPIResponse:
        try:
            listing_types = ["AUTO", "AUTO_SOLD"]

            all_locations = []

            for listing_type in listing_types:
                locations = self.search(location, listing_type)

                if locations:
                    all_locations.extend(locations)

            return TypeaheadAPIResponse(all_locations)
        except Exception as e:
            # traceback.print_exc(file=sys.stdout)
            raise APIError(
                f"Error fetching location for {location}: {str(e)}"
            )


class APIError(Exception):
    """Custom exception for API-related errors."""

    pass
