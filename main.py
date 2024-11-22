"""Entry point for the Calgary MLX scraper"""

from src.scraper import CalgaryMLXScraper

def main():
    try:
        scraper = CalgaryMLXScraper()
        
        # Fetch data for properties between 600k and 650k
        raw_data = scraper.fetch_data(600000, 650000)

        print(raw_data)
        
        # Parse the data into a DataFrame
        df = scraper.parse_property_data(raw_data)
        
        # Save the results
        scraper.save_to_csv(df)
        
        print(f"Successfully processed {len(df)} properties")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 