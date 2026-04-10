from misc import *
import unittest

class TestMisc(unittest.TestCase):

    def test_next_date(self):
        self.assertEqual(next_date("2025-01-01"), "2025-01-02")
        self.assertEqual(next_date("2024-12-31"), "2025-01-01")
        self.assertEqual(next_date("1900-02-28"), "1900-03-01") # Leap Century shouldn't matter
    
    def test_previous_date(self):
        self.assertEqual("2025-01-01", previous_date("2025-01-02"))
        self.assertEqual("2024-12-31", previous_date("2025-01-01"))
        self.assertEqual("2022-10-31", previous_date("2022-11-01"))
        self.assertEqual("1900-02-28", previous_date("1900-03-01")) # Leap Century


if __name__ == "__main__":
    unittest.main()