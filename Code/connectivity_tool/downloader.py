from datetime import datetime, timedelta
import os
import re
import requests
from urllib.parse import urljoin
import zipfile
from io import BytesIO
import config


"""
Example HTML Object
<a id="click_to_download" href="/static/download_files/EARTH_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_20211010T120000.zip" download="">here</a>
"""
# Returns the relative link, eg /static/download_files/EARTH_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_20211010T120000.zip
DOWNLOAD_URL_REGEX = re.compile(r'<a id ="click_to_download" href="(.*)" download>here<\/a>')
BASE_URL = "http://connect-tool.irap.omp.eu/"

FILE_WHITELIST_REGEX = [
    r".*_backgroundmag\.png", 
    r".*_fileconnectivity\.ascii", 
    r".*_finallegendmag\.png"
]

def extract_download_url(content):
    matches = DOWNLOAD_URL_REGEX.findall(content)
    assert len(matches) == 1, f"Something is Wrong with the Connectivity Tool: Found {len(matches)} Downloads expected 1"
    download_url: str = matches[0]
    assert download_url.endswith(".zip"), f"Something is Wrong with the Connectivity Tool: Expected zip file got {download_url}"

    # Resolving the relative url
    return urljoin(BASE_URL, download_url)



def _download_set(date_point: datetime):
    # We only allow the hours 0, 6, 12, 18
    assert date_point.hour % 6 == 0, "Somethings wrong with the date, make sure to round/floor it to the next multiple of 6 hours"
    request_link = date_point.strftime(f'{BASE_URL}/api/SOLO/ADAPT/PARKER/SCTIME/%Y-%m-%d/%H0000')
    
    req = requests.get(request_link)
    website_content = req.content.decode()
    download_link = extract_download_url(website_content)
    
    data_req = requests.get(download_link)
    virtual_file = BytesIO(data_req.content)
    return virtual_file


def download_files(start_date: datetime, end_date: datetime, download_all = False):
    '''
    Automatically download connectivity tool data and unzip the downloaded folders. Then copy the needed files into correct directory and delete unnecessary files.
    '''

    # Date should be inclusive

    directory_to_extract_to = f'{config.CACHE_DIR}/connectivity_tool_downloads'

    while start_date <= end_date:
        folder_name = start_date.strftime('SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_%Y%m%dT%H0000')
        path = f'{directory_to_extract_to}/' + folder_name + '_fileconnectivity.ascii'
        if not os.path.isfile(path) or download_all:

            zip_file = _download_set(start_date)
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for file in zip_ref.filelist:
                    if any(re.fullmatch(regex, file.filename) for regex in FILE_WHITELIST_REGEX):
                        zip_ref.extract(file.filename, directory_to_extract_to)
            
        start_date += timedelta(hours=6)
    
    return


if __name__ == "__main__":
    download_files(datetime(year=2022, month=3, day=5), datetime(year=2022, month=3, day=8))