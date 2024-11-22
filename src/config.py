"""Configuration settings for the Calgary MLX scraper"""

# API Configuration
BASE_URL = "https://calgarymlx.com/wps/recip/59854/idx.search"
REFERER = "https://calgarymlx.com/recip.html"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

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
DEFAULT_OUTPUT_FILE = f"{DATA_DIR}/calgary_properties.csv"
LOG_FILE = f"{LOG_DIR}/calgary_mlx_scraper.log"

# Default search parameters
DEFAULT_SEARCH_PARAMS = {
    "__SOLD__onoff": "only",
    "__SOLD__month_range": "24",
    "PROPERTY_TYPE": "RESI|DWELLING_TYPE@DET",
    "price-from": "600000",
    "price-to": "620000",
    "DWELLING_TYPE": "DET",
    "YEAR_BUILT": "1990-2005",
    "_priceReduction": "on",
    "sw_lat": "50.80385356806897",
    "sw_lng": "-114.73967292417584",
    "ne_lat": "51.21931073434607",
    "ne_lng": "-113.17798414259289",
    "forMap": "true",
    "listingType": "AUTO_SOLD",
    "omni": "list_subarea:C-443[Arbour Lake]",
    "format": "tiles",
    "pxWidth": DEFAULT_PX_WIDTH,
    "pxHeight": DEFAULT_PX_HEIGHT,
    "minTileSize": DEFAULT_MIN_TILE_SIZE,
    "maxTileSize": DEFAULT_MAX_TILE_SIZE,
}