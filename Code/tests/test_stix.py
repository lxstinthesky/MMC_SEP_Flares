from stix import *
import unittest
import pandas as pd
import config

class TestStix(unittest.TestCase):

    def test_flare_range(self):
        stix_flares = pd.read_csv(f"Code/{config.CACHE_DIR}/flare_list/STIX_flarelist_w_locations_20210318_20240801_version1_pythom.csv")

        start_date = "2021-03-01"
        end_date = "2024-07-01"

        flare_start_id, flare_end_id = flares_range(start_date, end_date, stix_flares['peak_UTC'])
        self.assertEqual(flare_start_id, 0)
        self.assertEqual(flare_end_id, 16838)
    
    def test_closest_timestamp(self):
        self.assertEqual(closest_timestamp("2021-03-18T14:51:39.337"), "2021-03-18T12:00:00.000")
        self.assertEqual(closest_timestamp("2021-03-18T23:51:39.337"), "2021-03-19T00:00:00.000")


if __name__ == "__main__":
    unittest.main()