"""Entry point for the Calgary MLX scraper"""

from src.scraper import CalgaryMLXScraper
from src.config import DEBUG_MODE

def main():
    try:
        scraper = CalgaryMLXScraper()
        
        if DEBUG_MODE:
            print("\nRunning in DEBUG MODE")
            print("You will see detailed request information and be prompted before each request")
        
        # Process all years from 1980 to current year
        scraper.fetch_all_years()
        
    except SystemExit as e:
        print(f"\nScraper stopped: {str(e)}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 