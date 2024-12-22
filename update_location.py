from src.api import CalgaryMLXAPI
from src.database import Database
from src.location_search import LocationSearch

def main():
    api = CalgaryMLXAPI()
    db = Database('calgary_mlx.db')
    db.connect()
    
    location_search = LocationSearch(api, db)
    
    # Search for Beddington Heights
    subareas, communities = location_search.search_and_store("Beddington Heights")
    
    print("Subareas:", subareas)
    print("Communities:", communities)
    
    # Search for Carrington
    subareas, communities = location_search.search_and_store("Carrington")
    
    print("Subareas:", subareas)
    print("Communities:", communities)

if __name__ == "__main__":
    main() 