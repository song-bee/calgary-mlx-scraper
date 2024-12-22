from src.api import CalgaryMLXAPI
from src.database import Database
from src.location_search import LocationSearch
from src.config import AREAS
from src.utils import random_sleep
import time

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def check_location_exists(db: Database, area_name: str) -> bool:
    """Check if location exists in either subareas or communities tables"""
    cursor = db.conn.cursor()
    
    # Check subareas table
    cursor.execute("SELECT code FROM subareas WHERE name = ?", (area_name,))
    if cursor.fetchone():
        return True
        
    # Check communities table
    cursor.execute("SELECT code FROM communities WHERE name = ?", (area_name,))
    if cursor.fetchone():
        return True
        
    return False

def update_location_with_retry(location_search: LocationSearch, area_name: str) -> bool:
    """Update location with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            subareas, communities = location_search.search_and_store(area_name)
            if subareas or communities:
                print(f"✓ Successfully updated {area_name} (Attempt {attempt + 1})")
                return True
            
            if attempt < MAX_RETRIES - 1:
                print(f"No data found for {area_name}, retrying... (Attempt {attempt + 1})")
                time.sleep(RETRY_DELAY)
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error updating {area_name}: {str(e)}")
                print(f"Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"✗ Failed to update {area_name} after {MAX_RETRIES} attempts")
                return False
    
    return False

def update_all_locations():
    """Update all locations from AREAS configs"""
    api = CalgaryMLXAPI()
    db = Database('calgary_mlx.db')
    db.connect()
    
    location_search = LocationSearch(api, db)
    
    print("\nUpdating areas...")
    for area_name in AREAS:
        # Skip if location already exists
        if check_location_exists(db, area_name):
            print(f"⚡ Skipping {area_name} (already exists)")
            continue
            
        print(f"\nProcessing {area_name}...")
        success = update_location_with_retry(location_search, area_name)
        
        if success:
            random_sleep()  # Add delay between successful updates

def main():
    try:
        update_all_locations()
        print("\nLocation update completed successfully!")
    except Exception as e:
        print(f"\nError updating locations: {str(e)}")

if __name__ == "__main__":
    main() 