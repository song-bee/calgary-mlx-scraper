"""Configuration settings for the Calgary MLX scraper"""

DEBUG_MODE = False

# API Configuration
BASE_URL = "https://calgarymlx.com/wps/recip/59854/idx.search"
REFERER = "https://calgarymlx.com/recip.html"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

START_YEAR = 1970

PRICE_FROM = 500000
PRICE_TO = 2000000
PRICE_STEP = 10000

DEFAULT_SW_LAT = "50.80385356806897"
DEFAULT_SW_LNG= "-114.73967292417584"
DEFAULT_NE_LAT = "51.21931073434607"
DEFAULT_NE_LNG = "-113.17798414259289"
DEFAULT_PX_WIDTH = 1878
DEFAULT_PX_HEIGHT = 771
DEFAULT_MIN_TILE_SIZE = 50
DEFAULT_MAX_TILE_SIZE = 150

# Default request headers
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-mrp-auto-sold": "true",
    "x-mrp-cache": "no",
    "x-mrp-tmpl": "v2",
    "x-requested-with": "XMLHttpRequest",
    "Referer": REFERER,
    "Referrer-Policy": "strict-origin-when-cross-origin",
    'User-Agent': USER_AGENT
}

# Cookie configuration
COOKIES = {
}

# File paths
DATA_DIR = "data"
LOG_DIR = "logs"
COOKIE_FILE = f"{DATA_DIR}/cookies.json"
DEFAULT_OUTPUT_FILE = "calgary_properties.csv"
LOG_FILE = f"{LOG_DIR}/calgary_mlx_scraper.log"

# Map Configuration
MAP_CONFIG = {
    "sw_lat": DEFAULT_SW_LAT,
    "sw_lng": DEFAULT_SW_LNG,
    "ne_lat": DEFAULT_NE_LAT,
    "ne_lng": DEFAULT_NE_LNG,
    "forMap": "true",
}

# Subarea Configuration
SUBAREAS = {
    "C-443": "Arbour Lake",
    "C-475": "Citadel",
    "C-451": "Hawkwood"
}

# Default search parameters
DEFAULT_SEARCH_PARAMS = {
    "__SOLD__onoff": "only",
    "__SOLD__month_range": "24",
    "PROPERTY_TYPE": "RESI|DWELLING_TYPE@DET",
    "price-from": "",
    "price-to": "",
    "DWELLING_TYPE": "DET",
    "YEAR_BUILT": "1990-2005",
    "_priceReduction": "on",
    "listingType": "AUTO_SOLD",
    "omni": "",
    "format": "tiles",
    "pxWidth": DEFAULT_PX_WIDTH,
    "pxHeight": DEFAULT_PX_HEIGHT,
    "minTileSize": DEFAULT_MIN_TILE_SIZE,
    "maxTileSize": DEFAULT_MAX_TILE_SIZE,
    **MAP_CONFIG,  # Include all map configuration parameters
}

# Parameters Configuration
OMNI_TEMPLATE = "list_subarea:{subarea_code}[{subarea_name}]"

# URL Configuration
LISTING_URL_PREFIX = "https://calgarymlx.com/recip.html/listing"
LISTING_URL_TEMPLATE = "{prefix}.{mls_number}-{street_address}-calgary-{postal_code}.{listing_id}"
LISTING_URL_CITY = "calgary"  # In case city name needs to be configurable

# Property URL formatting settings
PROPERTY_URL_FIELDS = {
    'street_parts': [
        'STREET_NUMBER',
        'STREET_NAME',
        'STREET_TYPE',
        'STREET_DIR'
    ],
    'required_fields': [
        'MLS_NUM',
        'POSTAL_CODE',
        'LIST_ID'
    ]
}

# Geocoding Configuration
GEOCODING_URL = "https://www.mapdevelopers.com/data.php"
GEOCODING_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache"
}

GEOCODING_PARAMS = {
    "operation": "geocode",
    "region": "USA",
    "lcode": "wekAzBW939q9xUX5",
    "lid": "76632848",
    "code": "splitpea"
}
