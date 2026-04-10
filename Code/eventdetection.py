import pandas as pd
import epd
import stix
import misc
import config
import numpy as np

def cleanup_sensor(df_step: pd.DataFrame):
    """
    Removes unused Columns and Calculates the Electron count. Returns a new Dataframe with the Electron count.
    """
    length = 32
    if ('Integral_Avg_Flux_47' in df_step.columns):
        length = 48
    df_step_electron = pd.DataFrame(columns = [], index = df_step.index)
    zipped_columns = [(f'Electron_Avg_Flux_{i}', f"Integral_Avg_Flux_{i}", f"Magnet_Avg_Flux_{i}") for i in range(length)]

    for electron_col, integral_col, magnet_col in zipped_columns:
        df_step_electron[electron_col] = df_step[integral_col] - df_step[magnet_col]

    return df_step_electron


START_DATE, END_DATE = "2021-05-21", "2021-05-24"
#START_DATE, END_DATE = "2023-01-09", "2023-01-12"
sigma_factor = 2.5

_parker_dist_series = pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")
parker_dist_series = _parker_dist_series['Parker_Spiral_Distance']

stix_flares = stix.read_list()

dates = pd.to_datetime(stix_flares['peak_UTC'])
mask = (pd.Timestamp(START_DATE) <= dates) & (dates < pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
flare_range = stix_flares[mask]

# Making sure the flare time is suntime
AU_TO_M = 149597870700
SPEED = 299_792_458 # m/s
time_difference = pd.to_timedelta((flare_range["solo_position_AU_distance"] * AU_TO_M) / SPEED, unit="s")

flare_range["_date_start"] = pd.to_datetime(stix_flares['start_UTC']).dt.floor("60s") - time_difference
flare_range["_date_peak"] = pd.to_datetime(stix_flares['peak_UTC']).dt.floor("60s") - time_difference
flare_range["_date_end"] = pd.to_datetime(stix_flares['end_UTC']).dt.floor("60s")- time_difference


df = epd.load_pickles("ept", str(START_DATE), str(END_DATE), viewing="sun")
df_sensor = df
#df_sensor = cleanup_sensor(df)
running_mean, running_std = epd.running_average(df_sensor, 18)

columns =  df_sensor.columns
column = columns[1]

threshold = running_mean + sigma_factor * running_std
selected = df_sensor > threshold

# If mean is zero, we want to ignore it
selected &= (running_mean != 0) # Bitwise and

# If we have a nan we also want to ignore it
nan_mask = df_sensor.isna() | running_mean.isna() | running_std.isna() # Bitwise OR
selected &= ~nan_mask

# Implementing the idea described here for effecient detection of events: 
# https://joshdevlin.com/blog/calculate-streaks-in-pandas/

diff = (selected != selected.shift()) & ~selected.shift().isna()

indexed = diff.cumsum()
streaks = selected * indexed
streaks = streaks[streaks != 0]
streaks["Index"] = streaks.index

event_starts = []
event_ends = []


for i, column in enumerate(columns):
    time_corrected = streaks["Index"]
    group = time_corrected.groupby(streaks[column])

    # Remove singular events
    mask = group.count().reset_index(drop=True) > 1

    # Getting the Event Starts
    min_group = group.min().reset_index(drop=True)[mask]

    # And Ends
    max_group = group.max().reset_index(drop=True)[mask]


    channel_event = pd.Series(min_group)
    event_starts.append(channel_event)

    event_ends.append(pd.Series(max_group))


# Fully parallize the computation of the events and only loop over the flares
df_starts = pd.DataFrame(event_starts, index=columns).T
df_ends = pd.DataFrame(event_ends, index=columns).T
step_speeds = misc.misc_handler.compute_particle_speed(34, "electron")
for flare_index in flare_range.index:
    arrive_time = pd.to_timedelta(_parker_dist_series['Parker_Spiral_Distance'][flare_index] / step_speeds, unit="s")
    
    low = flare_range["_date_start"][flare_index] + arrive_time
    high = flare_range["_date_end"][flare_index] + arrive_time * 1.5

    mask = low < df_starts
    mask &= df_starts < high

    flare_range.loc[flare_index, "channels"] = mask.any().sum()


ax = df_sensor.plot(y="Electron_Flux_1", logy=True)
threshold.plot(ax=ax, y="Electron_Flux_1")

events = pd.concat({"Start": df_starts, "End": df_ends}, axis=1)
print(events[:]["Electron_Flux_1"])