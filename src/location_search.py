import re
from typing import Dict, List, Tuple
from .api import CalgaryMLXAPI
from .database import Database

class LocationSearch:
    def __init__(self, api: CalgaryMLXAPI, db: Database):
        self.api = api
        self.db = db

    def _parse_location_item(self, item: List) -> Dict:
        """Parse a location item from the API response"""
        type_code, name, confidence, polygon = item
        
        # Extract the code from type_code (e.g., "list_subarea:C-508" -> "C-508")
        code = type_code.split(':')[1]
        
        return {
            'code': code,
            'name': re.sub(r'\s*\([^)]*\)', '', name),  # Remove text in parentheses
            'confidence': confidence,
            'polygon': polygon
        }

    def search_and_store(self, query: str, listing_type: str = "AUTO") -> Tuple[List[Dict], List[Dict]]:
        """Search locations and store results in database"""
        results = self.api.typeahead_search(listing_type, query)
        
        subareas = []
        communities = []

        for item in results:
            type_code = item[0]
            
            if type_code.startswith('list_subarea:'):
                data = self._parse_location_item(item)
                self.db.save_location('subareas', data)
                subareas.append(data)
            
            elif type_code.startswith('community:'):
                data = self._parse_location_item(item)
                self.db.save_location('communities', data)
                communities.append(data)

        return subareas, communities 