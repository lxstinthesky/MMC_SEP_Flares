from connectivity_tool.downloader import _download_set
from connectivity_tool.goes import get_goes_classification, compute_goes_flux
from datetime import datetime
import zipfile

import unittest


class TestMisc(unittest.TestCase):

    def test_download(self):
        date = datetime(year=2024, month=4, day=3, hour=12) # Random Day
        virtual_file = _download_set(date) 

        with zipfile.ZipFile(virtual_file) as zip:
            needed_files = [file.filename for file in zip.filelist if file.filename.endswith("_fileconnectivity.ascii")]
            self.assertEqual(len(needed_files), 1)

            file_content = zip.read(needed_files[0])
            # Each file contains the exact time of recording
            # 2024-05-31 18:00:00
            file_date = file_content.decode().splitlines()[17]
            parsed_date = datetime.fromisoformat(file_date)

            self.assertEqual(parsed_date, date)
    
    def test_goes_classification(self):
        self.assertEqual(get_goes_classification(3 * 10 ** -8), "A")

        self.assertEqual(get_goes_classification(4.11 * 10 ** -7), "B4")

        self.assertEqual(get_goes_classification(1.02 * 10 ** -6), "C1")
        self.assertEqual(get_goes_classification(2.68 * 10 ** -6), "C2")

        self.assertEqual(get_goes_classification(9.8 * 10 ** -5), "M9")
        
        self.assertEqual(get_goes_classification(7.111 * 10 ** -4), "X7")
    
    def test_goes(self):
        self.assertEqual(get_goes_classification(compute_goes_flux(500)), "C2")
        self.assertEqual(get_goes_classification(compute_goes_flux(7000)), "M1")


        




if __name__ == "__main__":
    unittest.main()