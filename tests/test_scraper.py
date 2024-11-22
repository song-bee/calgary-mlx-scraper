"""Unit tests for the Calgary MLX scraper"""

import unittest
from src.scraper import CalgaryMLXScraper
from src.utils import validate_price_range

class TestCalgaryMLXScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = CalgaryMLXScraper()

    def test_prepare_payload(self):
        payload = self.scraper.prepare_payload(600000, 650000)
        self.assertEqual(payload["price-from"], "600000")
        self.assertEqual(payload["price-to"], "650000")

    def test_validate_price_range(self):
        with self.assertRaises(ValueError):
            validate_price_range(650000, 600000)
        with self.assertRaises(ValueError):
            validate_price_range(-1, 600000)

if __name__ == '__main__':
    unittest.main() 