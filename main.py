"""Entry point for the Calgary MLX scraper"""

from src.scraper import CalgaryMLXScraper

def main():
    try:
        scraper = CalgaryMLXScraper()
        
        # Fetch all properties using the two-step process
        df = scraper.fetch_all_properties(600000, 650000)
        
        if not df.empty:
            # Save the results
            scraper.save_to_csv(df)
            print(f"Successfully processed {len(df)} properties")
        else:
            print("No properties found")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 