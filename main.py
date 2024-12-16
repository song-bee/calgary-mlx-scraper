"""Entry point for the Calgary MLX scraper"""

import sys
import traceback

from src.scraper import CalgaryMLXScraper
from src.config import SUBAREAS, COMMUNITIES, TEST_AREA, RUN_ALL_AREAS

def run_specific_area(scraper: CalgaryMLXScraper):

    if not TEST_AREA:
        # Display all available subareas
        print("Available Subareas:")
        for subarea_id, subarea_name in SUBAREAS.items():
            print(f"ID: {subarea_id} - Name: {subarea_name}")

        # Display all available communities
        print("\nAvailable Communities:")
        for community_id, community_name in COMMUNITIES.items():
            print(f"ID: {community_id} - Name: {community_name}")

        user_input = ''
    else:
        user_input = TEST_AREA

    while True:
        if not user_input:
            # Prompt user for subarea or community input
            user_input = input(
                "\nEnter a subarea or community name/ID (or press Enter for all areas): "
            ).strip()

        if not user_input:
            print("No input provided. Try again.")
            continue

        user_input = user_input.upper()

        # Check if the input is a valid subarea or community
        if user_input in SUBAREAS:
            area_name = SUBAREAS[user_input]
            print(f"Fetching data for subarea: {area_name} (ID: {user_input})")
            scraper.fetch_all_years({user_input: area_name}, {})
            break
        elif user_input in COMMUNITIES:
            community_name = COMMUNITIES[user_input]
            print(
                f"Fetching data for community: {community_name} (ID: {user_input})"
            )
            scraper.fetch_all_years({}, {user_input: community_name})
            break

        print(
            "Invalid input. Please enter a valid subarea or community name/ID. Try again."
        )

def main():
    try:
        scraper = CalgaryMLXScraper()

        if RUN_ALL_AREAS:
            print("Fetching data for all areas.")
            scraper.fetch_all_years()
        else:
            run_specific_area(scraper)

    except SystemExit as e:
        print(f"\nScraper stopped: {str(e)}")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f"\nAn error occurred: {str(e)}")
    except KeyboardInterrupt:
        print(f"\nScraper interrupted")


if __name__ == "__main__":
    main()
