# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calgary MLX Scraper - A Python-based web scraper for collecting historical property sales data from Calgary MLX real estate platform. The scraper fetches sold property listings, processes them, stores them in a SQLite database, and generates interactive HTML reports with maps and statistics.

## Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Scraper
```bash
# Run the main scraper (interactive mode)
python main.py

# Update location data from the typeahead API
python update_location.py
```

### Generating HTML Reports
```bash
# Generate HTML reports from database
python -m src.database_to_html

# Convert CSV files to HTML (legacy)
python -m src.csv_to_html
```

### Database Location
- Database files are stored in `db/` directory
- Default database: `db/properties.sqlite3`
- Contains tables for each property type: `detached_house`, `row_town_house`, `semi_detached_house`

## Architecture Overview

### Core Components

**1. Scraper Flow (src/scraper.py)**
- Main class: `CalgaryMLXScraper`
- Initialization creates database connection and property tables for all property types
- Uses tile-based pagination to fetch properties from the MLX API
- Automatically handles response pagination when results exceed API limits
- Recursive price-range splitting when too many properties are found in a year
- Saves data directly to SQLite database during scraping (no intermediate CSV files)

**2. API Layer (src/api.py)**
- `MLXAPI`: Handles POST requests to search endpoint with tile-based pagination
- `TypeaheadAPI`: Searches for location codes and coordinates via typeahead endpoint
- `MLXAPIResponse`: Normalizes different API response formats (listings dict vs results array)
- `Tile` dataclass: Represents geographic tiles with lat/lon coordinates for pagination

**3. Database Layer (src/database.py)**
- Three property tables: `detached_house`, `row_town_house`, `semi_detached_house`
- `area_coordinates` table: Caches geocoded coordinates for neighborhoods
- `subareas` and `communities` tables: Store location metadata from typeahead API
- No foreign keys - simple flat table structure with duplicate property fields per table

**4. Configuration (src/config.py)**
- Centralized configuration for all settings
- `SUBAREAS`: Dict mapping subarea codes (e.g., "C-443") to neighborhood names
- `COMMUNITIES`: Dict mapping community codes to neighborhood names
- `PROPERTIES_TYPES`: Defines three property types (detached, row/town, semi-detached)
- Area groupings by quadrant: NORTHWEST, WEST, SOUTHWEST, etc.

### Data Flow

1. **Location Discovery**: TypeaheadAPI searches for area names → saves to `subareas`/`communities` tables
2. **Coordinate Resolution**: Geocodes area names using Nominatim → caches in `area_coordinates` table
3. **Property Scraping**: For each area code + property type + year range:
   - Initial search gets total count
   - If count > 150, splits into price ranges (recursive subdivision if needed)
   - Iterates through tiles (geographic pagination) to collect all listings
   - Saves each batch to database immediately
4. **HTML Generation**: Reads from database → generates neighborhood HTML pages with maps → creates index pages

### Key Patterns

**Tile-Based Pagination**
- API returns tiles with lat/lon coordinates and property counts
- Scraper iterates through tiles, requesting properties at each coordinate
- New tiles discovered during iteration are added to queue
- Continues until all unique properties are retrieved

**Price Range Splitting**
- When too many results found (>150), splits year range into price segments
- Default: $100K steps from $100K to $2M
- Recursive subdivision with smaller steps if individual segments still too large
- Minimum step size: $1K

**Geocoding Cache**
- First checks `area_coordinates` table for cached coordinates
- Falls back to Nominatim API with retry logic and rate limiting
- Saves successful geocodes to avoid repeated API calls
- Uses Calgary city center as fallback if geocoding fails

**Database-First Design**
- No intermediate CSV files during scraping
- Properties saved directly to SQLite during fetch
- HTML generation reads from database
- Legacy CSV export functionality exists but not used in main flow

## Important Gotchas

1. **API Rate Limiting**: The scraper includes random sleep delays (300ms ± 100ms) between requests. Do not remove these - they prevent rate limiting.

2. **Geocoding Rate Limits**: Nominatim has strict rate limits. The code includes retry logic and delays. Always use the cached `area_coordinates` table when possible.

3. **Duplicate Properties**: Properties can appear in multiple tiles. The scraper uses `drop_duplicates(subset=["id"])` to handle this. The database uses `INSERT OR REPLACE` logic.

4. **Year Range Handling**: `START_YEAR` and `END_YEAR` are configured in src/config.py. END_YEAR=0 means "current year". Scraper processes in 10-year chunks.

5. **Property Type Tables**: Each property type has its own table with identical schema. Always specify which table you're working with.

6. **Area Type Distinction**: Locations come in two types - SUBAREA (codes like "C-443") and COMMUNITY (numeric codes like "139"). They use different API parameters.

7. **Coordinate Boundaries**: The scraper creates tile boundaries by adding/subtracting a radius (default 0.02) from tile center coordinates. This radius affects how many properties are returned per tile.

## HTML Output Structure

```
html_data/
  <property-type>/          # e.g., detached-house
    index.html              # Main index with map and neighborhood statistics
    <Neighborhood>_properties.html  # Individual neighborhood pages with:
      - Interactive Leaflet map with property markers
      - Sortable table of all properties
      - Decade statistics charts using Chart.js
```

Each property marker on the map shows: built year, square footage, sold date, and price. Clicking reveals full details in a popup.

## Testing

The project has minimal test coverage. There is a `tests/test_scraper.py` file but it's not actively maintained. Manual testing is done by running the scraper on specific test areas configured via `TEST_AREA` in src/config.py.
