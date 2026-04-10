import sys
import os
# Making sure we have access to all the modules and are in the correct working directory
dirname = os.path.dirname(__file__)
code_dir = os.path.join(dirname, '../')
sys.path.insert(0, dirname)
sys.path.insert(0, code_dir)
os.chdir(code_dir)
import datetime
from stix import read_list, closest_timestamp
import pandas as pd
import numpy as np
import math
from connectivity_tool import read_data
import epd
import step
import misc
from classes import Config, SensorData
import matplotlib
import matplotlib.pyplot as plt
import bundler
import config


# Matplotlib settings
dpi = 100
matplotlib.rc("savefig", dpi = dpi)

# Downloading the datasets
def setup():
    bundler.auto_download()

# Prepare the stix flares and checking the MCT connectivity
def get_stix_flares():
    raw_list = read_list()
    _dates = pd.to_datetime(raw_list['peak_UTC'])
    raw_list["_date"] = _dates

    raw_list["Rounded"] = raw_list["peak_UTC"].apply(closest_timestamp)

    # Making sure the flare time is suntime
    AU_TO_M = 149597870700
    SPEED = 299_792_458 # m/s
    time_difference = pd.to_timedelta((raw_list["solo_position_AU_distance"] * AU_TO_M) / SPEED, unit="s")

    raw_list["_date_start"] = pd.to_datetime(raw_list['start_UTC']).dt.floor("60s") - time_difference
    raw_list["_date_peak"]  = pd.to_datetime(raw_list['peak_UTC']).dt.floor("60s")  - time_difference
    raw_list["_date_end"]   = pd.to_datetime(raw_list['end_UTC']).dt.floor("60s")   - time_difference

    # Looping over all flare candidates because connectivity Tool returns Dataframe
    for i in raw_list.index:
        flare_lon = raw_list['hgc_lon'][i]
        flare_lat = raw_list['hgc_lat'][i]
        # Returns Dataframe
        try:
            # Getting the connectivity tool data
            con_tool_data = read_data(raw_list["Rounded"][i])
        except Exception as e:
            print(raw_list["Rounded"][i], repr(e))
            exit()
            
        con_longitudes = con_tool_data["CRLN"]
        con_latitudes = con_tool_data["CRLT"]

        # Making sure we get the shortest distance
        lon_dist = np.min([(con_longitudes-flare_lon) % 360, (flare_lon-con_longitudes) % 360], axis=0)
        lat_dist = con_latitudes - flare_lat

        dist_sq = lon_dist ** 2 + lat_dist ** 2

        min_dist = math.sqrt(np.min(dist_sq))

        raw_list.loc[i, "Min Dist"] = min_dist

    return raw_list

# Getting the Parker Spiral distance series
def get_parker_dist_series():
    return pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

setup()
stix_flares = get_stix_flares()
parker_dist_series = get_parker_dist_series()



# Filtering the flares to the date range
first_flare = stix_flares["_date"].min()
last_flare = stix_flares["_date"].max()


MIN_DATE = datetime.date(2021, 2, 14)

import tqdm
for s_year, s_month, e_year, e_month in tqdm.tqdm([(x//12 + 2021, x % 12+1, (x+1)//12 + 2021, (x+1) % 12+1) for x in range(1, 4*12)]):
    START_DATE = datetime.date(s_year, s_month, 1)
    if START_DATE < MIN_DATE:
        START_DATE = MIN_DATE
    END_DATE = datetime.date(e_year, e_month, 1) - datetime.timedelta(days=1)


    sensor_switch = datetime.date(2021, 10, 22)
    if START_DATE <= sensor_switch and sensor_switch <= END_DATE:
        #exit(-1)
        pass


    DELTA = 20
    WINDOW_LEN = 18
    SIGMA_STEP = 3.5 
    SIGMA_EPT = 2.5
    INDIRECT = 1.5
    N_CHANNELS = 5


    CONFIG = Config(window_length=WINDOW_LEN, 
                        step_sigma=SIGMA_STEP, 
                        ept_sigma=SIGMA_EPT, 
                        delta_flares=DELTA, 
                        start_date=START_DATE, 
                        end_date=END_DATE,
                        indirect_factor=INDIRECT,
                        needed_channels=N_CHANNELS)

    # --------------------------------------- STIX ---------------------------------------
    # Filtering the flares to the date range
    dates = stix_flares['_date']
    mask = (pd.Timestamp(START_DATE) <= dates) & (dates < pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
    flare_range = stix_flares[mask]
    if not mask.any():
        exit(-1)


    flare_range["MCT"] = flare_range["Min Dist"] <= CONFIG.delta_flares

    # --------------------------------------- EPD ---------------------------------------
    dict_sensor: dict[str, SensorData] = {}

    for direction in ["sun", "asun", "north", "south"]:
        sensor = SensorData(is_step=False, sigma=CONFIG.ept_sigma)
        sensor.df_data = epd.load_pickles("ept", str(START_DATE), str(END_DATE), viewing=direction)

        sensor.df_mean, sensor.df_std = epd.running_average(sensor.df_data, CONFIG.window_length)

        dict_sensor[f"EPT-{direction.upper()}"] = sensor



    step_sensor = SensorData(is_step=True, sigma=CONFIG.step_sigma)
    df_step = epd.load_pickles("step", str(START_DATE), str(END_DATE))
    df_step = step.cleanup_sensor(df_step)

    step_sensor.df_data = df_step
    step_sensor.df_mean, step_sensor.df_std = epd.running_average(step_sensor.df_data, CONFIG.window_length)

    dict_sensor["STEP"] = step_sensor

    for sensor_name in dict_sensor:
        # Getting the Sensor Object
        sensor = dict_sensor[sensor_name]

        # To shorten the code
        df_sensor = sensor.df_data
        running_mean = sensor.df_mean
        running_std = sensor.df_std
        sigma = sensor.sigma


        # Getting all events
        columns =  df_sensor.columns

        threshold = running_mean + sigma * running_std
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

        df_conn = flare_range.copy()

        if sensor.is_step:
            speeds = misc.physics.get_step_speeds(length=len(columns))
        else:
            speeds = misc.misc_handler.compute_particle_speed(34, "electron")
        
        if df_starts.empty:
            df_conn["channels"] = 0
        else:
            for flare_index in flare_range.index:
                arrive_time = pd.to_timedelta(parker_dist_series[flare_index] / speeds, unit="s")
                
                low = df_conn["_date_start"][flare_index] + arrive_time
                high = df_conn["_date_end"][flare_index] + arrive_time * CONFIG.indirect_factor

                mask = low < df_starts
                mask &= df_starts < high

                df_conn.loc[flare_index, "channels"] = mask.any().sum()
        
        events = pd.concat({"Start": df_starts, "End": df_ends}, axis=1)
        events = events.swaplevel(axis=1)
        df_conn["EPD_EVENT"] = df_conn["channels"] >= CONFIG.needed_channels

        dict_sensor[sensor_name].df_event = events
        dict_sensor[sensor_name].df_connection = df_conn
        

                
                
    table = []
    total_indecies = set()
    ept_indecies = set()
    # Collecting the events in sets to display which sensor captured which events

    for sensor_name in dict_sensor:
        df_conn = dict_sensor[sensor_name].df_connection
        mask = df_conn["EPD_EVENT"] & df_conn["MCT"]
        table.append([sensor_name, len(df_conn[mask])])
        total_indecies = total_indecies.union(df_conn[mask].index)
        if not dict_sensor[sensor_name].is_step:
            ept_indecies = ept_indecies.union(df_conn[mask].index)

    table.append(["Total (All Sensors)", len(total_indecies)])
    table.append(["EPT (All Directions)", len(ept_indecies)])

    ORDER = ["EPT-SUN", "EPT-ASUN", "EPT-NORTH", 
            "EPT-SOUTH", "EPT (All Directions)","STEP", 
            "Total (All Sensors)"]

    table = sorted(table, key=lambda x: ORDER.index(x[0]))

    table = pd.DataFrame(table, columns=["Sensor", f"Flares deemed connected ({CONFIG.start_date} - {CONFIG.end_date})"])
    # Making the total columns bold
    def bold_total(val, props=''):
        value = props if np.isin(val, ["EPT (All Directions)", "Total (All Sensors)"]).any() else ""
        return np.array([value]*len(val))
    s1 = table.style.apply(bold_total, props='color:black;background-color:lightgrey;', axis=1)




    # --------------------------------------- PLOTTING ---------------------------------------
    sensor_name = "EPT-SOUTH"


    sensor = dict_sensor[sensor_name]
    df_flares = sensor.df_connection
    df_mean = sensor.df_mean
    df_std = sensor.df_std
    df_sensor = sensor.df_data
    events = sensor.df_event

    sigma = sensor.sigma
    columns = []
    column_indecies = []

    for i in range(1, len(df_sensor.columns), len(df_sensor.columns)//4):
        columns.append(df_sensor.columns[int(i)])
        column_indecies.append(int(i))

    plt.rcParams["figure.figsize"] = (20, 9)

    fig, (flare_ax, *axs) = plt.subplots(5, sharex = False)
    plt.subplots_adjust(hspace = 0)

    df_hold = df_std.copy()
    df_hold[""] = np.nan
    df_hold[""].plot(color="black", ax=flare_ax)


    for ax, column in zip(axs, columns):
        num = int(column.split("_")[-1])
        energies = epd.get_energies(sensor_name, len(df_sensor.columns))
        df_sensor[column].plot(color="black", logy=True, ax=ax, label=f"{sensor_name} Channel {num}\n{energies[num]}")
        df_threshhold = df_std[column] * sigma + df_mean[column]
        df_threshhold.plot(color="g", logy=True, ax=ax, label=f'run. avg. mean + {sigma} $\sigma$')


    # Only plot each label once, else the whole legend is filled
    shown_labels = set()

    for i in df_flares.index:
        kwargs = {"color": "black", "label": "flare"}

        if df_flares["MCT"][i]:
            kwargs["color"] = "orange"
            kwargs["label"] = "candidate flare\n(mag. connectivity tool)"
        
        if kwargs["label"] in shown_labels:
            del kwargs["label"]
        else:
            shown_labels.add(kwargs["label"])
        
        if kwargs["color"] == "black":
            continue
        flare_ax.axvline(df_flares["_date"][i], **kwargs)

    first = True
    for col, ax in zip(columns, axs):
        for event in events[col].iloc:
            if event.isna().all():
                continue
            kwargs = {}
            if first:
                first = False
                kwargs["label"] = "electron event"

            ax.axvspan(event["Start"], event["End"], color = 'b', alpha = 0.2, **kwargs)

    # Plotting EPD-Connected Flares (candidates/connected)
    shown_labels = set()

    # Used for showing the connections, we use top and bottom to not upstruct the plot
    positions = axs[0].get_ylim()
    for i in df_flares[df_flares["EPD_EVENT"] == True].index:
        kwargs = {"color": "blue", "label": "coincidence flare"}

        if df_flares["MCT"][i]:
            kwargs["color"] = "red"
            kwargs["label"] = "connected flare"
            

        for ax in axs:
            if kwargs.get("label", None) in shown_labels:
                del kwargs["label"]
            elif kwargs.get("label", None):
                shown_labels.add(kwargs["label"])
            
            ax.axvline(df_flares["_date"][i], **kwargs)


    if sensor.is_step:
        speeds = misc.physics.get_step_speeds(length=len(columns))
    else:
        speeds = misc.misc_handler.compute_particle_speed(34, "electron")


    flare_ax.set_xlim(*axs[0].get_xlim())
    flare_ax.xaxis.tick_top()
    flare_ax.get_yaxis().set_visible(False)

    handles, labels = flare_ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    if handles:
        labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0], reverse=True))
    flare_ax.legend(handles, labels, loc="lower right")

    for ax in axs[:-1]:
        ax.legend(loc = 'lower right')
        ax.get_xaxis().set_visible(False)

    axs[-1].legend(loc = 'lower right')

    # Grouping the plot to align the labels
    fig.add_subplot(111, frameon = False)
    plt.ylabel('electron intensity [$(cm^2 \ s \ sr \ MeV)^{-1}$]', fontsize = 20, loc="center")
    plt.xlabel('time', fontsize = 20, labelpad=20)
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)

    plt.savefig(f"monthly/{sensor_name.lower()}/{START_DATE}.png")

    plt.close('all')