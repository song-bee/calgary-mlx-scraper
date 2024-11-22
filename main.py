"""Entry point for the Calgary MLX scraper"""

from src.scraper import CalgaryMLXScraper

def main():
    try:
        scraper = CalgaryMLXScraper()
        
        # Process all years from 1980 to current year
        scraper.fetch_all_years()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 