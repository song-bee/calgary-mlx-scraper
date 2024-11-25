"""Entry point for the Calgary MLX scraper"""

import sys
import traceback

from src.scraper import CalgaryMLXScraper
from src.config import DEBUG_MODE, SUBAREAS, COMMUNITIES

def main():
    try:
        scraper = CalgaryMLXScraper()

        if DEBUG_MODE:
            print("\nRunning in DEBUG MODE")
            print("Processing the following subareas:")
            for code, name in SUBAREAS.items():
                print(f"- {name} ({code})")
            print(
                "\nYou will see detailed request information and be prompted before each request"
            )

        # Display all available subareas
        print("Available Subareas:")
        for subarea_id, subarea_name in SUBAREAS.items():
            print(f"ID: {subarea_id} - Name: {subarea_name}")
        
        # Display all available communities
        print("\nAvailable Communities:")
        for community_id, community_name in COMMUNITIES.items():
            print(f"ID: {community_id} - Name: {community_name}")
        
        # Prompt user for subarea or community input
        user_input = input("\nEnter a subarea or community name/ID (or press Enter for all areas): ").strip()
        
        if user_input:
            # Check if the input is a valid subarea or community
            if user_input in SUBAREAS:
                area_name = SUBAREAS[user_input]
                print(f"Fetching data for subarea: {area_name} (ID: {user_input})")
                scraper.fetch_all_years({user_input: area_name}, {})
            elif user_input in COMMUNITIES:
                community_name = COMMUNITIES[user_input]
                print(f"Fetching data for community: {community_name} (ID: {user_input})")
                scraper.fetch_all_years({}, {user_input: community_name})
            else:
                print("Invalid input. Please enter a valid subarea or community name/ID.")
                return
        else:
            print("Fetching data for all areas.")
            scraper.fetch_all_years()

    except SystemExit as e:
        print(f"\nScraper stopped: {str(e)}")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f"\nAn error occurred: {str(e)}")
    except KeyboardInterrupt:
        print(f"\nScraper interrupted")


if __name__ == "__main__":
    main()
