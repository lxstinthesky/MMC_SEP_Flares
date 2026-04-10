import numpy as np
import pandas as pd
import math
import config

DATA_QUALITY_COLUMNS = {'QUALITY_BITMASK', 'QUALITY_FLAG', 'SMALL_PIXELS_FLAG'}

def reduce_data(_df: pd.DataFrame, sensor=""):
    '''
    Sums up particle counts for each minute to decrease amount of data load by factor (time_resolution, currently 300 (5 mins))
    Factor has to be a divisor of 86400
    
    Accounts for missing data and fills these timespans with empty data (nan)
    
    parameters:
    df: Pandas Dataframe that holds data to be reduced
    '''
    df = _df.copy()
    # Assuming that the next hour of the first index is 00:00 of the correct day
    date = df.index[0].round("d")
    grouped = df.resample(f"{config.TIME_RESOLUTION}s", origin=date)
    df_new = pd.DataFrame()
    df_new = grouped.mean()

    # Data-Quality Columns
    column_intersection = DATA_QUALITY_COLUMNS.intersection(df_new.columns)
    # Pandas doesn't like sets
    column_intersection = list(column_intersection)

    # For Quality Columns the worst (highest) value is of interest
    df_new[column_intersection] = grouped[column_intersection].max()

    # To cap it at end of day
    max_index = (24*60*60) // config.TIME_RESOLUTION

    # Filling up with NaNs, if not enough Datapoints (shouldn't happen very often)
    required_indicies = pd.date_range(date, periods=max_index, freq=f"{config.TIME_RESOLUTION}s")
    df_new = pd.DataFrame(data=df_new, index=required_indicies)
    
    return df_new[:max_index]


def is_peak_persistent(peak: pd.Timestamp, df, df_mean, df_std, sigma_factor):
    slice_start = peak
    end = peak + pd.Timedelta(minutes=5)

    current_std = df_std.loc[peak - pd.Timedelta(minutes=5)]
    current_mean = df_mean.loc[peak - pd.Timedelta(minutes=5)]

    outlier_test = df[slice_start: end] - current_mean >= sigma_factor * current_std
    mask = df[slice_start: end].isna()
    # (df_mean != 0) # Not done here for some reason?

    outlier_test |= mask
    
    # checking if both are above the threshold
    results = outlier_test.sum(axis=1) >= 5

    return results.sum() == 2


def running_average(df: pd.DataFrame, length=18):
    '''
    Computes running average to enable finding events in EPD data
    
    parameters:
    df:     Pandas Dataframe with EPD data
    '''

    df_mean = df.rolling(window=length).mean()
    df_std = df.rolling(window=length).std(ddof=0)

    # Shifting the Data to exclude the current Datapoint from the calculations
    # Creating new Dataframe to make sure the correct indecies are there
    df_mean = pd.DataFrame(df_mean.shift(5, freq="min"), index=df.index)
    df_std = pd.DataFrame(df_std.shift(5, freq="min"), index=df.index)
    
    return df_mean, df_std


def get_energies(sensor, length=1):
    _sensor = sensor.lower()

    ept_energies = [['0.0312 - 0.0354 MeV'], ['0.0334 - 0.0374 MeV'], ['0.0356 - 0.0396 MeV'], ['0.0382 - 0.0420 MeV'], ['0.0408 - 0.0439 MeV'], ['0.0439 - 0.0467 MeV'], ['0.0467 - 0.0505 MeV'],
                ['0.0505 - 0.0542 MeV'], ['0.0542 - 0.0588 MeV'], ['0.0588 - 0.0635 MeV'], ['0.0635 - 0.0682 MeV'], ['0.0682 - 0.0739 MeV'], ['0.0739 - 0.0798 MeV'], ['0.0798 - 0.0866 MeV'],
                ['0.0866 - 0.0942 MeV'], ['0.0942 - 0.1021 MeV'], ['0.1021 - 0.1107 MeV'], ['0.1107 - 0.1207 MeV'], ['0.1207 - 0.1314 MeV'], ['0.1314 - 0.1432 MeV'], ['0.1432 - 0.1552 MeV'],
                ['0.1552 - 0.1690 MeV'], ['0.1690 - 0.1849 MeV'], ['0.1849 - 0.2004 MeV'], ['0.2004 - 0.2182 MeV'], ['0.2182 - 0.2379 MeV'], ['0.2379 - 0.2590 MeV'], ['0.2590 - 0.2826 MeV'],
                ['0.2826 - 0.3067 MeV'], ['0.3067 - 0.3356 MeV'], ['0.3356 - 0.3669 MeV'], ['0.3669 - 0.3993 MeV'], ['0.3993 - 0.4352 MeV'], ['0.4353 - 0.4742 MeV']]
    energies_32 = [['0.0057 - 0.0090 MeV'], ['0.0061 - 0.0091 MeV'], ['0.0065 - 0.0094 MeV'], ['0.0070 - 0.0098 MeV'], ['0.0075 - 0.0102 MeV'], ['0.0088 - 0.0114 MeV'], ['0.0082 - 0.0108 MeV'],
                   ['0.0095 - 0.0121 MeV'], ['0.0103 - 0.0129 MeV'], ['0.0111 - 0.0137 MeV'], ['0.0120 - 0.0146 MeV'], ['0.0130 - 0.0157 MeV'], ['0.0141 - 0.0168 MeV'], ['0.0152 - 0.0180 MeV'],
                   ['0.0166 - 0.0193 MeV'], ['0.0179 - 0.0206 MeV'], ['0.0193 - 0.0221 MeV'], ['0.0209 - 0.0237 MeV'], ['0.0226 - 0.0254 MeV'], ['0.0245 - 0.0274 MeV'], ['0.0265 - 0.0295 MeV'],
                   ['0.0287 - 0.0317 MeV'], ['0.0310 - 0.0341 MeV'], ['0.0335 - 0.0366 MeV'], ['0.0362 - 0.0394 MeV'], ['0.0394 - 0.0425 MeV'], ['0.0425 - 0.0459 MeV'], ['0.0459 - 0.0498 MeV'],
                   ['0.0498 - 0.0539 MeV'], ['0.0539 - 0.0583 MeV'], ['0.0583 - 0.0629 MeV'], ['0.0629 - 0.0680 MeV']]
    energies_48 = [['0.0057 - 0.0090 MeV'], ['0.0060 - 0.0091 MeV'], ['0.0062 - 0.0092 MeV'], ['0.0065 - 0.0094 MeV'], ['0.0069 - 0.0096 MeV'], ['0.0071 - 0.0098 MeV'], ['0.0074 - 0.0101 MeV'],
                   ['0.0078 - 0.0105 MeV'], ['0.0083 - 0.0109 MeV'], ['0.0086 - 0.0112 MeV'], ['0.0097 - 0.0128 MeV'], ['0.0115 - 0.0141 MeV'], ['0.0122 - 0.0148 MeV'], ['0.0127 - 0.0153 MeV'],
                   ['0.0135 - 0.0163 MeV'], ['0.0143 - 0.0171 MeV'], ['0.0149 - 0.0177 MeV'], ['0.0159 - 0.0186 MeV'], ['0.0169 - 0.0195 MeV'], ['0.0176 - 0.0202 MeV'], ['0.0186 - 0.0213 MeV'],
                   ['0.0198 - 0.0224 MeV'], ['0.0209 - 0.0237 MeV'], ['0.0223 - 0.0248 MeV'], ['0.0231 - 0.0257 MeV'], ['0.0245 - 0.0274 MeV'], ['0.0262 - 0.0288 MeV'], ['0.0272 - 0.0298 MeV'],
                   ['0.0287 - 0.0317 MeV'], ['0.0306 - 0.0332 MeV'], ['0.0318 - 0.0344 MeV'], ['0.0335 - 0.0366 MeV'], ['0.0358 - 0.0384 MeV'], ['0.0377 - 0.0411 MeV'], ['0.0404 - 0.0431 MeV'],
                   ['0.0420 - 0.0447 MeV'], ['0.0440 - 0.0478 MeV'], ['0.0473 - 0.0502 MeV'], ['0.0494 - 0.0522 MeV'], ['0.0518 - 0.0560 MeV'], ['0.0556 - 0.0586 MeV'], ['0.0579 - 0.0609 MeV'],
                   ['0.0605 - 0.0655 MeV'], ['0.0651 - 0.0683 MeV'], ['0.0680 - 0.0738 MeV'], ['0.0736 - 0.0771 MeV'], ['0.0767 - 0.0802 MeV'], ['0.0799 - 0.0865 MeV']]
    
    if "ept" in _sensor:
        return ept_energies
    
    if "step" in _sensor:
        if length == 32:
            return energies_32
        if length == 48:
            return energies_48
    
    raise ValueError("Sensor not found")