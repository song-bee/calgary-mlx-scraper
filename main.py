"""Entry point for the Calgary MLX scraper"""

import sys
import traceback

from src.scraper import CalgaryMLXScraper
from src.config import TEST_AREA, RUN_ALL_AREAS

def run_specific_areas(scraper: CalgaryMLXScraper, subareas: dict, communities: dict) -> None:
    """Run scraper for specific areas selected by user"""
    if not TEST_AREA:
        # Display all available subareas
        print("\nAvailable Subareas:")
        for subarea_id, subarea_name in subareas.items():
            print(f"ID: {subarea_id} - Name: {subarea_name}")

        # Display all available communities
        print("\nAvailable Communities:")
        for community_id, community_name in communities.items():
            print(f"ID: {community_id} - Name: {community_name}")

        print("\nEnter multiple area IDs separated by commas (,)")
        print("Example: C-111,C-110,139")
        user_input = ''
    else:
        user_input = TEST_AREA

    while True:
        if not user_input:
            # Prompt user for subarea or community input
            user_input = input(
                "\nEnter area IDs (or press Enter for all areas): "
            ).strip()

        if not user_input:
            print("No input provided. Try again.")
            continue

        # Split input into individual area codes
        area_codes = [code.strip().upper() for code in user_input.split(',')]
        
        # Initialize dictionaries for selected areas
        selected_subareas = {}
        selected_communities = {}
        invalid_codes = []

        # Process each area code
        for code in area_codes:
            if code in subareas:
                selected_subareas[code] = subareas[code]
                print(f"Added subarea: {subareas[code]} (ID: {code})")
            elif code in communities:
                selected_communities[code] = communities[code]
                print(f"Added community: {communities[code]} (ID: {code})")
            else:
                invalid_codes.append(code)

        # Report any invalid codes
        if invalid_codes:
            print("\nInvalid area codes found:", ", ".join(invalid_codes))
            print("Please try again with valid codes.")
            user_input = ''
            continue

        # If at least one valid area was found, proceed with scraping
        if selected_subareas or selected_communities:
            print(f"\nFetching data for {len(selected_subareas) + len(selected_communities)} areas...")
            scraper.fetch_all_years(selected_subareas, selected_communities)
            break
        else:
            print("No valid areas selected. Please try again.")
            user_input = ''

def main():
    try:
        scraper = CalgaryMLXScraper()

        scraper.update_all_locations()

        subareas, communities = scraper.get_all_locations()

        if RUN_ALL_AREAS:
            print("Fetching data for all areas.")
            scraper.fetch_all_years(subareas, {})
        else:
            run_specific_areas(scraper, subareas, communities)

    except SystemExit as e:
        print(f"\nScraper stopped: {str(e)}")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f"\nAn error occurred: {str(e)}")
    except KeyboardInterrupt:
        print(f"\nScraper interrupted")


if __name__ == "__main__":
    main()
