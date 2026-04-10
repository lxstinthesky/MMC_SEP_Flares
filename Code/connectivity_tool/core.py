'''
manually download data from connectivity tool with:
http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/yyyy-mm-dd/hhmmss

where the timestamp can only be [000000, 060000, 120000, 180000] as the measurements are done 4 times per day.
'''
from .downloader import download_files

import pandas as pd
import os
from datetime import datetime, timedelta
import functools

import config

@functools.cache
def read_data(utc):
    '''
    reads data from connectivity tool database
    
    if files are not already downloaded, it will automatically do that
        -> this will open a new browser window
    '''
    timestamp = utc[0:4] + utc[5:7] + utc[8:13] + '0000'
    filename = f'{config.CACHE_DIR}/connectivity_tool_downloads/SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_' + timestamp + '_fileconnectivity.ascii'
    
    if not os.path.isfile(filename):
        start_date = datetime.fromisoformat(utc)
        try:
            download_files(start_date, start_date+timedelta(hours=6)) # as only next file is needed in this case
        except Exception as e:
            print(f"Download of {timestamp} failed:", repr(e))
        
    # generate empty dataframe with columns: [i, density(%), R(m), CRLT(degrees), CRLN(degrees), DIST(m), HPLT(degrees), HPLN(degrees)]
    df = pd.DataFrame({"SSW/FSW/M" : pd.Series(dtype = 'string'), # Mesurement / Slow / Fast
                       "density" : pd.Series(dtype = 'float'),  # Probability
                       "R" : pd.Series(dtype = 'float'),        # Distance of Sun (~700'000)
                       "CRLT" : pd.Series(dtype = 'float'),     # Carrington Latitude
                       "CRLN" : pd.Series(dtype = 'float'),     # Carrington Longitude
                       "DIST" : pd.Series(dtype = 'float'),     # S/C distance
                       "HPLT" : pd.Series(dtype = 'float'),     
                       "HPLN" : pd.Series(dtype = 'float')})
    
    if not os.path.isfile(filename):
        return df
    

    with open(filename, 'r') as connectivity_file:
        raw_data = connectivity_file.readlines()
    

    data = {
        "SSW/FSW/M" : [],
        "density" : [],
        "R" : [],
        "CRLT" : [],
        "CRLN" : [],
        "DIST" : [],
        "HPLT" : [],
        "HPLN" : []
    }

    for line in raw_data[20:]:
        line = line.strip()
        columns = line.split()

        data["SSW/FSW/M"].append(str(columns[0]))
        data["density"].append(float(columns[2]))
        data["R"].append(float(columns[3]))
        data["CRLT"].append(float(columns[4]))
        data["CRLN"].append(float(columns[5]))
        data["DIST"].append(float(columns[6]))
        data["HPLT"].append(float(columns[7]))
        data["HPLN"].append(float(columns[8]))

    return pd.DataFrame(data=data)


