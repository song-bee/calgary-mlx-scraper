import logging
import requests
import sys
import traceback

from typing import List, Dict, Optional, Union
from dataclasses import dataclass

from .cookie_manager import CookieManager
from .debug_utils import DebugHelper
from .config import (
    HOME_URL,
    SEARCH_URL,
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
        year: int,
        dwelling_type: str,
        tile: Tile = None,
        price_from: int = 0,
        price_to: int = 0,
        radius: float = 0.02,
    ) -> MLXAPIResponse:
        """Fetch data from the search API"""
        try:
            payload = DEFAULT_SEARCH_PARAMS.copy()

            year_range = f"{year}-{year}"
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
                f"Error fetching data for tile at {tile.lat}, {tile.lon}, year {year}: {str(e)}"
            )


class APIError(Exception):
    """Custom exception for API-related errors."""

    pass
