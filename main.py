"""Entry point for the Calgary MLX scraper"""

import sys
import traceback

from src.scraper import CalgaryMLXScraper
from src.config import DEBUG_MODE, SUBAREAS

def main():
    try:
        scraper = CalgaryMLXScraper()
        
        if DEBUG_MODE:
            print("\nRunning in DEBUG MODE")
            print("Processing the following subareas:")
            for code, name in SUBAREAS.items():
                print(f"- {name} ({code})")
            print("\nYou will see detailed request information and be prompted before each request")
        
        # Process all subareas and years
        scraper.fetch_all_years()
        
    except SystemExit as e:
        print(f"\nScraper stopped: {str(e)}")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 