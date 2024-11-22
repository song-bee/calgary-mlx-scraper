"""Unit tests for the Calgary MLX scraper"""

import unittest
from datetime import datetime
from src.scraper import CalgaryMLXScraper
from src.utils import validate_price_range

class TestCalgaryMLXScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = CalgaryMLXScraper()
        
        # Sample response data for testing
        self.sample_response_type1 = {
            "listings": {
                "17186820219": {
                    "LIST_ID": 17186820219,
                    "STREET_NUMBER": "101",
                    "STREET_NAME": "Arbour Crest",
                    "STREET_DIR": "NW",
                    "STREET_TYPE": "ROAD",
                    "CITY": "Calgary",
                    "POSTAL_CODE": "T3G 4L4",
                    "PRICE_RAW": 699900,
                    "SOLD_PRICE_RAW": 712000,
                    "LISTED_DATE": 20221214,
                    "SOLD_DATE": 20221216,
                    "AREA_SQ_FEET": 2003,
                    "MLS_NUM": "A2015397",
                    "TOTAL_BEDROOMS": "5",
                    "TOTAL_BATHS": "4",
                    "LATITUDE": 51.13571976,
                    "LONGITUDE": -114.20541145,
                    "AGENT_NAME": "Test Agent",
                    "OFFICE_NAME": "Test Office",
                    "LIST_SUBAREA": "Arbour Lake"
                }
            }
        }
        
        self.sample_response_type2 = {
            "results": [{
                "LIST_ID": 17186820219,
                "STREET_NUMBER": "101",
                "STREET_NAME": "Arbour Crest",
                "STREET_DIR": "NW",
                "STREET_TYPE": "ROAD",
                "CITY": "Calgary",
                "POSTAL_CODE": "T3G 4L4",
                "PRICE_RAW": 699900,
                "SOLD_PRICE_RAW": 712000,
                "LISTED_DATE": 20221214,
                "SOLD_DATE": 20221216,
                "AREA_SQ_FEET": 2003,
                "MLS_NUM": "A2015397",
                "TOTAL_BEDROOMS": "5",
                "TOTAL_BATHS": "4",
                "LATITUDE": 51.13571976,
                "LONGITUDE": -114.20541145,
                "AGENT_NAME": "Test Agent",
                "OFFICE_NAME": "Test Office",
                "LIST_SUBAREA": "Arbour Lake"
            }]
        }

    def test_parse_property_data_type1(self):
        """Test parsing of Type 1 response (listings dictionary)"""
        df = self.scraper.parse_property_data(self.sample_response_type1)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['street_number'], "101")
        self.assertEqual(df.iloc[0]['street_name'], "Arbour Crest")

    def test_parse_property_data_type2(self):
        """Test parsing of Type 2 response (results array)"""
        df = self.scraper.parse_property_data(self.sample_response_type2)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['street_number'], "101")
        self.assertEqual(df.iloc[0]['street_name'], "Arbour Crest")

    def test_empty_response(self):
        """Test handling of empty responses"""
        empty_response = {"listings": {}, "results": []}
        df = self.scraper.parse_property_data(empty_response)
        self.assertTrue(df.empty)

    def test_create_tile_boundary(self):
        """Test boundary calculation for tiles"""
        from dataclasses import dataclass
        
        @dataclass
        class TestTile:
            lat: float
            lon: float
            count: int
            id: int
            pixel_size: int
        
        tile = TestTile(lat=51.0, lon=-114.0, count=1, id=1, pixel_size=76)
        boundary = self.scraper.create_tile_boundary(tile)
        
        self.assertIn('sw_lat', boundary)
        self.assertIn('ne_lat', boundary)
        self.assertIn('sw_lng', boundary)
        self.assertIn('ne_lng', boundary)

if __name__ == '__main__':
    unittest.main() 