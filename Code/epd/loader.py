import pandas as pd
import config
import misc

def load_data(sensor, utc_start, utc_end, viewing = 'omni'):
    '''
    (string) sensor: 'ept', 'het', or 'step'
    (int) startdate: yyyymmdd
    (int) enddate:  yyyymmdd
    (string) level: 'l2' or 'll' -> defines level of data product: level 2 ('l2') or low-latency ('ll'). By default 'l2'.
    (string) viewing: 'sun', 'asun', 'north', 'south', 'omni' or None; not eeded for sensor = 'step'.
        'omni' is just calculated as the average of the other four viewing directions: ('sun'+'asun'+'north'+'south')/4
    (string) path: directory in which Solar Orbiter data is/should be organized; e.g. '/home/userxyz/solo/data/'. See `Data folder structure` for more details.
    (bool) autodownload: if True, will try to download missing data files from SOAR
    (bool) only_averages: If True, will for STEP only return the averaged fluxes, and not the data of each of the 15 Pixels. This will reduce the memory consumption. By default False.
    '''
    from solo_epd_loader import epd_load
    level = 'l2' # always load l2 data!
    
    startdate = int(utc_start[0:4] + utc_start[5:7] + utc_start[8:10])
    enddate = int(utc_end[0:4] + utc_end[5:7] + utc_end[8:10])
    
    # df_1: includes Ion_Flux, Ion_Uncertainty, Ion_Rate, Alpha_Flux, Alpha_Uncertainty, Alpha_Rate, ...
    # df_2: includes Electron_Flux, Electron_Uncertainty, Electron_Rate, ...
    # energies: includes the bins of energy ranges
    if sensor == 'ept':
        df_1, df_2, energies = epd_load(sensor, startdate, enddate, level, viewing, path = f"{config.CACHE_DIR}/_solo/", autodownload = True, only_averages = False, pos_timestamp="start")
        
        return df_1, df_2, energies
    
    if sensor == 'step':
        df_1, energies = epd_load(sensor, startdate, enddate, level, viewing, path = f"{config.CACHE_DIR}/_solo/", autodownload = True, only_averages = False, pos_timestamp="start")
        
        return df_1, energies
    

def load_pickles(sensor, start_date, end_date, particle = 'electron', viewing = 'none'):
    '''
    load data from self built database
    
    parameters:
    sensor:     string with name of sensor
    viewing:    string with name of viewing angle [sun, asun, north, south]
    start_date: string of starting date
    end_date:   string of end date
    particle:   string of particle type [ion, electron]
    '''
    df = pd.DataFrame()
    date = start_date
    count = 0
    while date != misc.next_date(end_date):
        if sensor == 'ept':
            df_new = pd.read_pickle(f'{config.CACHE_DIR}/EPD_Dataset/' + sensor + '/' + viewing + '/' + particle + '/' + date + '.pkl')
            
        if sensor == 'step':
            df_new = pd.read_pickle(f'{config.CACHE_DIR}/EPD_Dataset/' + sensor + '/' + date + '.pkl')
        
        df = pd.concat([df, df_new], ignore_index = True)
        
        count += 1
        date = misc.next_date(date)
    
    # change index back to datetime with correct minutes
    datetime_series = pd.Series(pd.date_range(start_date, periods = 86400 / config.TIME_RESOLUTION * count, freq = str(config.TIME_RESOLUTION) + "s"))
    df.set_index(datetime_series, inplace = True)
    return df