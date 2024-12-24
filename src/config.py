"""Configuration settings for the Calgary MLX scraper"""

DEBUG_MODE = False

# API Configuration
HOME_URL = "https://calgarymlx.com/"
SEARCH_URL = "https://calgarymlx.com/wps/recip/59854/idx.search"
REFERER = "https://calgarymlx.com/recip.html"
TYPEAHEAD_URL = "https://listings.myrealpage.com/wps/rest/api/59854/typeahead"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'

START_YEAR = 2000
END_YEAR = 0

PRICE_FROM = 100000
PRICE_TO = 2000000
PRICE_STEP = 100000
MIN_PRICE_STEP = 1000

DEFAULT_SW_LAT = "50.80385356806897"
DEFAULT_SW_LNG = "-114.73967292417584"
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
    "User-Agent": USER_AGENT,
}

# Cookie configuration
COOKIES = {}

# File paths
DATA_DIR = "data"
DATABASE_DIR = "db"
LOG_DIR = "logs"
COOKIE_FILE = f"{DATA_DIR}/cookies.json"
DEFAULT_OUTPUT_FILE = "calgary_properties.csv"
LOG_FILE = f"{LOG_DIR}/calgary_mlx_scraper.log"
DEFAULT_DB_FILE = "properties.sqlite3"

# Map Configuration
MAP_CONFIG = {
    "sw_lat": DEFAULT_SW_LAT,
    "sw_lng": DEFAULT_SW_LNG,
    "ne_lat": DEFAULT_NE_LAT,
    "ne_lng": DEFAULT_NE_LNG,
    "forMap": "true",
}

RUN_ALL_AREAS = False
TEST_AREA = "C-027"

# Area Types and Their Codes
AREA_TYPES = {"SUBAREA": "list_subarea", "COMMUNITY": "community"}

AREAS = [
    # NORTH (N) CALGARY
    "Beddington Heights",
    "Carrington",
    "Country Hills",
    "Country Hills Village",
    "Coventry Hills",
    "Evanston",
    "Harvest Hills",
    "Hidden Valley",
    "Huntington Hills",
    "Kincora",
    "MacEwan Glen",
    "Nolan Hill",
    "North Haven",
    "North Haven Upper",
    "Panorama Hills",
    "Sage Hill",
    "Sandstone Valley",
    "Sherwood",
    "Thorncliffe",

    # NORTHWEST (NW) CALGARY
    "Arbour Lake",
    "Bowness",
    "Brentwood",
    "Charleswood",
    "Citadel",
    "Collingwood",
    "Dalhousie",
    "Edgemont",
    "Greenwood/Greenbriar",
    "Hamptons",
    "Hawkwood",
    "Montgomery",
    "Ranchlands",
    "Rocky Ridge",
    "Royal Oak",
    "Scenic Acres",
    "Silver Springs",
    "Tuscany",
    "University Heights",
    "Varsity",

    # WEST (W) CALGARY"
    "Aspen Woods",
    "Christie Park",
    "Coach Hill",
    "Cougar Ridge",
    "Crestmont",
    "Currie Barracks",
    "Discovery Ridge",
    "Garrison Green",
    "Glamorgan",
    "Glenbrook",
    "Glendale",
    "Lakeview",
    "Lincoln Park",
    "North Glenmore Park",
    "Patterson",
    "Rosscarrock",
    "Rutland Park",
    "Signal Hill",
    "Springbank Hill",
    "Spruce Cliff",
    "Strathcona Park",
    "Valley Ridge",
    "West Springs",
    "Westgate",
    "Wildwood",

    # NORTHEAST (NE) CALGARY
    "Abbeydale",
    "Castleridge",
    "Cityscape",
    "Coral Springs",
    "Falconridge",
    "Marlborough",
    "Marlborough Park",
    "Martindale",
    "Mayland Heights",
    "Monterey Park",
    "Pineridge",
    "Redstone",
    "Rundle",
    "Saddle Ridge",
    "Skyview Ranch",
    "Taradale",
    "Temple",
    "Vista Heights",
    "Whitehorn",

    # EAST (E) CALGARY
    "Albert Park/Radisson Heights",
    "Applewood Park",
    "Dover",
    "Erin Woods",
    "Forest Heights",
    "Forest Lawn",
    "Penbrooke Meadows",
    "Red Carpet",
    "Southview",

    # SOUTHEAST (SE) CALGARY
    "Auburn Bay",
    "Copperfield",
    "Cranston",
    "Douglasdale/Glen",
    "Mahogany",
    "McKenzie Lake",
    "McKenzie Towne",
    "New Brighton",
    "Ogden",
    "Riverbend",
    "Seton",

    # CITY CENTRE (CC) CALGARY
    "Altadore",
    "Banff Trail",
    "Bankview",
    "Bel Aire", # "Bel-Aire",
    "Beltline",
    "Bridgeland/Riverside",
    "Britannia",
    "Cambrian Heights",
    "Capitol Hill",
    "Chinatown",
    "Cliff Bungalow",
    "Crescent Heights",
    "Downtown Commercial Core",
    "Downtown East Village",
    "Downtown West End",
    "Eau Claire",
    "Elbow Park",
    "Elboya",
    "Erlton",
    "Garrison Woods",
    "Greenview",
    "Highland Park",
    "Highwood",
    "Hillhurst",
    # "Housefield Heights/Briar Hill",
    "Housefield Heights",
    "Briar Hill",
    "Inglewood",
    "Killarney/Glengarry",
    "Lower Mount Royal",
    "Manchester",
    "Mayfair",
    "Meadowlark Park",
    "Mission",
    "Parkdale",
    "Parkhill",
    "Point McKay",
    "Ramsay",
    "Renfrew",
    "Richmond",
    "Rideau Park",
    "Rosedale",
    "Rosemont",
    "Roxboro",
    "Scarboro",
    "Scarboro/Sunalta West",
    "Shaganappi",
    "South Calgary",
    "St Andrews Heights",
    "Sunalta",
    "Sunnyside",
    "Tuxedo Park",
    "Upper Mount Royal",
    "West Hillhurst",
    "Windsor Park",
    "Winston Heights/Mountview",

    # SOUTH (S) CALGARY
    "Acadia",
    "Bayview",
    "Bonavista Downs",
    "Braeside",
    "Bridlewood",
    "Canyon Meadows",
    "Cedarbrae",
    "Chaparral",
    "Chinook Park",
    "Deer Ridge",
    "Deer Run",
    "Diamond Cove",
    "Eagle Ridge",
    "Evergreen",
    "Fairview",
    "Haysboro",
    "Kelvin Grove",
    "Kingsland",
    "Lake Bonavista",
    "Legacy",
    "Maple Ridge",
    "Midnapore",
    "Millrise",
    "Oakridge",
    "Palliser",
    "Parkland",
    "Pump Hill",
    "Queensland",
    "Shawnee Slopes",
    "Shawnessy",
    "Silverado",
    "Somerset",
    "Southwood",
    "Sundance",
    "Walden",
    "Willow Park",
    "Woodbine",
    "Woodlands",
]

# Subarea Configuration
SUBAREAS = {
    # Northwest Areas
    "C-443": "Arbour Lake",
    "C-475": "Citadel",
    "C-451": "Hawkwood",
    "C-441": "Ranchlands",
    "C-471": "Hamptons",
    "C-461": "Edgemont",
    "C-422": "Dalhousie",
    "C-424": "Varsity",
    "C-420": "Brentwood",
    "C-419": "Charleswood",
    "C-482": "Tuscany",
    "C-418": "Collingwood",
    "C-519": "Evanston",
    "C-526": "Sage Hill",
    "C-484": "Rocky Ridge",
    "C-485": "Royal Vista",
    "C-486": "Royal Oak",
    # West/Southwest Areas
    "C-075": "West Springs",
    "C-049": "Coach Hill",
    "C-073": "Aspen Woods",
    "C-051": "Strathcona Park",
    "C-065": "Springbank Hill",
    "C-053": "Signal Hill",
    "C-031": "Lakeview",
    # South/Southwest Areas
    "C-143": "Oakridge",
    "C-131": "Pump Hill",
    "C-022": "North Glenmore Park",
    "C-147": "Woodbine",
    "C-125": "Canyon Meadows",
    "C-019": "Altadore",
    "C-017": "South Calgary",
    "C-220": "Willow Park",
    "C-230": "Maple Ridge",
    "C-157": "Evergreen",
    # Inner City Areas
    "C-415": "Banff Trail",
    "C-414": "Capitol Hill",
    "C-410": "West Hillhurst",
    "C-408": "Hounsfield Heights/Briar Hill",
    "C-407": "Hillhurst",
    "C-404": "Crescent Heights",
    "C-494": "Mount Pleasant",
    "C-492": "Tuxedo Park",
    "C-476": "Montgomery",
    "C-411": "Parkdale",
    "C-015": "Bankview",
    "C-003": "Beltline",
    "C-200": "Inglewood",
    # North Central
    "C-512": "MacEwan Glen",
    "C-510": "Sandstone Valley",
    "C-508": "Beddington Heights",
    "C-505": "Huntington Hills",
    "C-502": "Thorncliffe",
    "C-430": "Silver Springs",
    # Southeast Areas
    "C-365": "Auburn Bay",
    "C-375": "Mahogany",
    "C-345": "McKenzie Towne",
    # Additional South/Southwest
    "C-155": "Shawnessy",
    "C-151": "Shawnee Slopes",
    "C-153": "Millrise",
    "C-161": "Bridlewood",
    "C-159": "Somerset",
    # Far Northwest
    "C-515": "Panorama Hills",
    "C-477": "Sherwood",
    "C-474": "Nolan Hill",
    "C-524": "Kincora",
    "C-111": "Mayfair",
    "C-110": "Bel-Aire",
    "C-107": "Windsor Park",
    "C-310": "Riverbend",
    "C-305": "Ogden",
    "C-133": "Palliser",
    "C-145": "Cedarbrae",
    "C-135": "Braeside",
}

# Communities Configuration
COMMUNITIES = {
    #"157": "Evergreen",
    #"031": "Lakeview",
    "139": "Woodlands",
    "129": "Bayview",
}

# Combined areas for processing
ALL_AREAS = {"SUBAREAS": SUBAREAS, "COMMUNITIES": COMMUNITIES}

# Area groupings
AREA_GROUPS = {
    "NORTHWEST": [
        {"type": "SUBAREA", "code": "C-443"},  # Arbour Lake
        {"type": "SUBAREA", "code": "C-475"},  # Citadel
        # ... other northwest areas ...
    ],
    "SOUTHWEST": [
        {"type": "SUBAREA", "code": "C-143"},  # Oakridge
        {"type": "COMMUNITY", "code": "031"},  # Lakeview
        # ... other southwest areas ...
    ],
    "SOUTHEAST": [
        {"type": "COMMUNITY", "code": "157"},  # Evergreen
        # ... other southeast areas ...
    ],
}

# Optional: Add region metadata
REGION_INFO = {
    "NORTHWEST": {
        "description": "Established communities in Calgary's northwest quadrant",
        "avg_elevation": "1100-1200m",
    },
    "WEST": {
        "description": "Newer communities along Calgary's western edge",
        "avg_elevation": "1200-1300m",
    },
    "SOUTHWEST": {
        "description": "Mixed established and newer communities in southwest Calgary",
        "avg_elevation": "1050-1150m",
    },
}

PROPERTIES_TYPES = {

    'row-town-house': {
        'name': 'row_town_house',
        'display-name': 'Row or Town House',
        'type': 'RTHS',
    },

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
OMNI_SUBAREA_TEMPLATE = "list_subarea:{subarea_code}[{subarea_name}]"
OMNI_COMMUNITY_TEMPLATE = "community:{subarea_code}[{subarea_name}]"

# URL Configuration
LISTING_URL_PREFIX = "https://calgarymlx.com/recip.html/listing"
LISTING_URL_TEMPLATE = (
    "{prefix}.{mls_number}-{street_address}-calgary-{postal_code}.{listing_id}"
)
LISTING_URL_CITY = "calgary"  # In case city name needs to be configurable

# Property URL formatting settings
PROPERTY_URL_FIELDS = {
    "street_parts": ["STREET_NUMBER", "STREET_NAME", "STREET_TYPE", "STREET_DIR"],
    "required_fields": ["MLS_NUM", "POSTAL_CODE", "LIST_ID"],
}

# Location Configuration
CITY = "Calgary"
PROVINCE = "Alberta"
COUNTRY = "Canada"

# Default coordinates for Calgary city center
DEFAULT_LATITUDE = 51.0447
DEFAULT_LONGITUDE = -114.0719

# Geocoding Configuration
GEOCODER_USER_AGENT = USER_AGENT
GEOCODER_MAX_RETRIES = 3
GEOCODER_RETRY_DELAY = 1  # seconds
