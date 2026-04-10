import sys
import os

# Making sure we have access to all the modules and are in the correct working directory
dirname = os.path.dirname(__file__)
code_dir = os.path.join(dirname, '../../')  # Go up to /Code/ directory
sys.path.insert(0, dirname)
sys.path.insert(0, code_dir)
os.chdir(code_dir)

import streamlit as st
import datetime
from stix import read_list, closest_timestamp
from stixdcpy.net import Request
import pandas as pd
import numpy as np
import math
from connectivity_tool import read_data
import step
import misc
import epd
from classes import Config, SensorData
import matplotlib
import matplotlib.pyplot as plt
import bundler
import config
import re

# Matplotlib settings
dpi = 80
matplotlib.rc("savefig", dpi = dpi)

# Making sure the flare time is suntime
AU_TO_M = 149597870700
SPEED = 299_792_458 # m/s

# Downloading the datasets
@st.cache_resource
def setup():
    bundler.auto_download()

# Prepare the stix flares and checking the MCT connectivity
@st.cache_resource
def get_stix_flares():
    raw_list = read_list()
    _dates = pd.to_datetime(raw_list['peak_UTC'])
    raw_list["_date"] = _dates

    raw_list["Rounded"] = raw_list["peak_UTC"].apply(closest_timestamp)

    

    time_difference = pd.to_timedelta((raw_list["solo_position_AU_distance"] * AU_TO_M) / SPEED, unit="s")

    # appending columns for solar times
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
            st.error(f"We are missing the connectivity tool data for {raw_list.loc[i]} and thus can't give a prediction.")
            st.stop()
            
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
@st.cache_resource
def get_parker_dist_series():
    return pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

setup()
stix_flares = get_stix_flares()
parker_dist_series = get_parker_dist_series()

st.title("SO-Flink: Solar Orbiter Flare Link")
st.subheader("Automated Linkage between Solar Flares and Energetic Particle Events")

with st.sidebar:
    # Filtering the flares to the date range
    first_flare = stix_flares["_date"].min()
    last_flare = stix_flares["_date"].max()
    START_DATE = st.date_input(f"Start (after {first_flare.date()})", datetime.date(2021, 5, 21), first_flare, last_flare)
    END_DATE = st.date_input(f"End (before {last_flare.date()})", START_DATE+datetime.timedelta(days=3), START_DATE, START_DATE+datetime.timedelta(days=10))

    if START_DATE > END_DATE:
        st.warning("Startdate needs to be before enddate")
        st.stop()

    sensor_switch = datetime.date(2021, 10, 22)
    if START_DATE <= sensor_switch and sensor_switch <= END_DATE:
        st.warning(f"On the {sensor_switch} the data format of STEP was changed and thus can't be compared.")
        st.stop()

    with st.expander("Settings for mag. connectivity and SEP event detection", expanded=True):
        DELTA = st.slider("Accepted distance: flare - mag. footpoint", 1, 50, 20, format="%d°")
        WINDOW_LEN = st.slider("SEP running average window length", 6*5, 24*5, 18*5, 5, format="%d min") // 5
        SIGMA_STEP = st.slider("STEP sigma threshold", 2., 5., 3.5, format="%.1fσ")
        SIGMA_EPT = st.slider("EPT sigma threshold", 1., 4., 2.5, format="%.1fσ")
        INDIRECT = st.slider("Parker Spiral extension factor", 1.1, 2., 1.5, format="%.1f")
        N_CHANNELS = st.slider("Number of channels required for connection", 1, 20, 5)


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
    st.error("No STIX Flares found in the selected timeframe.")
    st.stop()


# filtering the flares based on angular separation to magnetic footpoint
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

            selection = mask.any()
            df_conn.loc[flare_index, "channels"] = selection.sum()

            df_conn.loc[flare_index, "First Connected Channel"] = selection[selection].index.to_list()[0] if selection.any() else None
            df_conn.loc[flare_index, "Last Connected Channel"] = selection[selection].index.to_list()[-1] if selection.any() else None
            

    
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

table = pd.DataFrame(table, columns=["Sensor", f"Flares deemed connected to SEP events ({CONFIG.start_date} - {CONFIG.end_date})"])
# Making the total columns bold
def bold_total(val, props=''):
    value = props if np.isin(val, ["EPT (All Directions)", "Total (All Sensors)"]).any() else ""
    return np.array([value]*len(val))
s1 = table.style.apply(bold_total, props='color:black;background-color:lightgrey;', axis=1)

# moved to bottom



# --------------------------------------- ALL FLARES ---------------------------------------


st.subheader(f"Flare Overview from {START_DATE} to {END_DATE}")

# Add filter controls
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    filter_sensor = st.selectbox("Filter by Sensor", ["All Sensors"] + list(dict_sensor.keys()), index=1)

with filter_col2:
    filter_mct = st.selectbox("Magnetically Connected (MCT)", ["All", "Yes", "No"], index=1)

with filter_col3:
    filter_epd = st.selectbox("SEP Event Detected", ["All", "Yes", "No"], index=1)

# Apply filters
filtered_flares = flare_range.copy()

if filter_sensor != "All Sensors":
    # Get connection data for selected sensor
    sensor_conn = dict_sensor[filter_sensor].df_connection
    # Only show flares that exist in this sensor's connection data
    filtered_flares = filtered_flares.loc[sensor_conn.index]
    
    # Add EPD_EVENT column from selected sensor
    filtered_flares["EPD_EVENT"] = sensor_conn["EPD_EVENT"]
    filtered_flares["Connected_Channels"] = sensor_conn["channels"].astype(int)

# Apply MCT filter
if filter_mct == "Yes":
    filtered_flares = filtered_flares[filtered_flares["MCT"] == True]
elif filter_mct == "No":
    filtered_flares = filtered_flares[filtered_flares["MCT"] == False]

# Apply EPD Event filter (only if a specific sensor is selected)
if filter_sensor != "All Sensors":
    if filter_epd == "Yes":
        filtered_flares = filtered_flares[filtered_flares["EPD_EVENT"] == True]
    elif filter_epd == "No":
        filtered_flares = filtered_flares[filtered_flares["EPD_EVENT"] == False]

# Display filtered results
st.markdown(f"**Showing {len(filtered_flares)} of {len(flare_range)} flares**")

# Create a display dataframe with relevant columns
display_cols = ["flare_id", "MCT", "_date_peak", "hgc_lon", "hgc_lat", "Min Dist"]
if filter_sensor != "All Sensors":
    display_cols.extend(["EPD_EVENT", "Connected_Channels"])

# from here on, make the table pretty
display_df = filtered_flares[display_cols].copy()

# Convert flare_id to string to avoid comma formatting
display_df["flare_id"] = display_df["flare_id"].astype(str)

display_df["MCT"] = display_df["MCT"].apply(lambda x: "YES" if x else "NO")

if "EPD_EVENT" in display_df.columns:
    display_df["EPD_EVENT"] = display_df["EPD_EVENT"].apply(lambda x: "YES" if x else "NO")

# Round numerical columns to 1 decimal place
display_df["hgc_lon"] = display_df["hgc_lon"].round(1).apply(lambda x: f"{x:.1f}")
display_df["hgc_lat"] = display_df["hgc_lat"].round(1).apply(lambda x: f"{x:.1f}")
display_df["Min Dist"] = display_df["Min Dist"].round(1).apply(lambda x: f"{x:.1f}")

# Rename columns for prettier display
column_mapping = {
    "flare_id": "STIX flare ID",
    "MCT": "Mag. connected",
    "_date_peak": "Peak time (UT)",
    "hgc_lon": "Carrington longitude [°]",
    "hgc_lat": "Carrington latitude [°]",
    "Min Dist": "Distance: flare - mag. footpoint [°]",
    "EPD_EVENT": "SEP event",
    "Connected_Channels": f"No. of connected {filter_sensor} channels"
}
display_df = display_df.rename(columns=column_mapping)

highlighted = -1

# Reorder columns - put important columns first
column_order = ["Peak time (UT)", "STIX flare ID", "Carrington longitude [°]", "Carrington latitude [°]", "Distance: flare - mag. footpoint [°]", "Mag. connected"]
if "SEP event" in display_df.columns:
    column_order.extend(["SEP event", f"No. of connected {filter_sensor} channels"])


display_df = display_df[column_order]


# Allow user to select a flare by clicking on the table
available_flare_ids = filtered_flares["flare_id"].astype(str).tolist()

if available_flare_ids:
    # Create an interactive dataframe with selection

    st.info("👇 **Click the checkbox** on the left of any row to view detailed flare information and plots")

    event = st.dataframe(
        display_df, 
        hide_index=True, 
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="flare_table"
    )
    
    # Get selected row
    selected_rows = event.selection.rows if hasattr(event, 'selection') else []

# --------------------------------------- FLARE DETAIL VIEW ---------------------------------------

    st.divider()
    st.subheader(f"Flare Detail View")

    
    if selected_rows:
        # Get the index of the selected row in the filtered dataframe
        selected_idx = filtered_flares.index[selected_rows[0]]
        flare = flare_range.loc[selected_idx]
        flare_index = selected_idx
        
        highlighted = flare_index
        
        st.success(f"Selected Flare ID: {flare['flare_id']}")
        
        
        # Display flare information
        with st.expander("Magnetic connectivity", expanded=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"#### STIX Flare ID: {flare['flare_id']}")
                
                info_data = {
                    "Start UT": pd.to_datetime(flare["_date_start"]).strftime("%Y-%m-%d %H:%M:%S"),
                    "Peak UT": pd.to_datetime(flare["_date_peak"]).strftime("%Y-%m-%d %H:%M:%S"),
                    "End UT": pd.to_datetime(flare["_date_end"]).strftime("%Y-%m-%d %H:%M:%S"),
                    "Carrington Longitude [°]": f"{flare['hgc_lon']:.2f}",
                    "Carrington Latitude [°]": f"{flare['hgc_lat']:.2f}",
                    "SO distance [AU]": f"{flare['solo_position_AU_distance']:.3f}",
                    "Distance: flare - mag. footpoint [°]": f"{flare['Min Dist']:.2f}",
                    "Mag. connected": "YES" if flare["MCT"] else "NO"
                }
                
                st.dataframe(
                    pd.DataFrame([info_data]).T.rename(columns={0: "Value"}),
                    use_container_width=True
                )
            
            with col2:
                # Display connectivity tool image
                flare_start = flare["_date_start"].round("6h")
                file = flare_start.strftime('SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_%Y%m%dT%H0000_finallegendmag.png')
                image_path = f"{config.CACHE_DIR}/connectivity_tool_downloads/{file}"
                
                if os.path.exists(image_path):
                    st.image(image_path, caption="Magnetic connectivity tool", use_container_width=True)
                else:
                    st.warning("Connectivity tool image not available")
        
        # Sensor connection information
        with st.expander("EPD Data", expanded=True):
            st.markdown("##### Sensor Connections")
            connected_sensors = []
            
            for sensor in dict_sensor:
                df_conn = dict_sensor[sensor].df_connection
                if flare_index not in df_conn.index:
                    continue
                
                row = df_conn.loc[flare_index]
                n_channels = int(row['channels'])
                epd_event = "YES" if row["EPD_EVENT"] else "NO"
                
                if row["EPD_EVENT"] and row["MCT"] and row["First Connected Channel"] is not None:
                    first_channel = row["First Connected Channel"]
                    last_channel = row["Last Connected Channel"]
                    # Extract channel numbers
                    first_channel = re.sub(r'_Avg', '', first_channel).split("_")[-1]
                    last_channel = re.sub(r'_Avg', '', last_channel).split("_")[-1]
                    connected_sensors.append([
                        sensor, 
                        epd_event,
                        n_channels,
                        f"{first_channel}-{last_channel}"
                    ])
                else:
                    connected_sensors.append([sensor, epd_event, n_channels, "N/A"])
            
            st.dataframe(
                pd.DataFrame(connected_sensors, columns=["Sensor", "SEP event", "No. of connected channels", "Channel range (min, max)"]),
                hide_index=True,
                use_container_width=True
            )
        
        # Plot detailed view if a specific sensor is selected
        st.divider()
        st.markdown("##### Detailed Plot")
        with st.expander("Plot options & display", expanded=True):
        
            if filter_sensor == "All Sensors":
                st.info("Select a specific sensor from the filter above to view the detailed time series plot.")
            else:
                sensor_name = filter_sensor
                sensor = dict_sensor[sensor_name]
                df_sensor = sensor.df_data
                df_mean = sensor.df_mean
                df_std = sensor.df_std
                events = sensor.df_event
                df_flares = sensor.df_connection
                sigma = sensor.sigma
                
                # Plotting options
                st.markdown("**Plot options**")
                
                # Time window controls
                col1, col2, col3, col4, col5 = st.columns(5)
                
                # Default time window: ±3 hours around flare
                flare_peak = flare["_date_peak"]
                flare_start_time = flare["_date_start"]
                flare_end_time = flare["_date_end"]
                default_plot_start = flare_start_time - pd.Timedelta(hours=3)
                default_plot_end = flare_peak + pd.Timedelta(hours=3)
                
                with col1:
                    plot_start_date = st.date_input(
                        "Start", 
                        value=default_plot_start.date(),
                        key="detail_start_date"
                    )
                
                with col2:
                    plot_start_time = st.time_input(
                        "Start time", 
                        value=default_plot_start.time(),
                        label_visibility="hidden",
                        key="detail_start_time"
                    )
                
                with col3:
                    st.write("")  # Spacer
                
                with col4:
                    plot_end_date = st.date_input(
                        "End", 
                        value=default_plot_end.date(),
                        min_value=plot_start_date,
                        key="detail_end_date"
                    )
                
                with col5:
                    plot_end_time = st.time_input(
                        "End time", 
                        value=default_plot_end.time(),
                        label_visibility="hidden",
                        key="detail_end_time"
                    )
                
                # Combine date and time
                plot_start = datetime.datetime.combine(plot_start_date, plot_start_time)
                plot_end = datetime.datetime.combine(plot_end_date, plot_end_time)

                # fetch stix light curve
                stix_lc = Request.fetch_light_curves(plot_start, plot_end, ltc=False)
                
                # Channel selection
                default_columns = []
                for i in range(1, len(df_sensor.columns), len(df_sensor.columns)//3):
                    default_columns.append(df_sensor.columns[int(i)])
                if len(default_columns) < 4:
                    default_columns.append(df_sensor.columns[-1])
                default_columns = default_columns[:4]
                
                columns = st.multiselect(
                    "Select channels (exactly 4 required)", 
                    df_sensor.columns, 
                    default=default_columns, 
                    max_selections=4,
                    key="detail_channels"
                )
                columns = sorted(columns, key=lambda x: int(x.split("_")[-1]))
                
                # Toggle for arrival window - default to True only if flare has SEP event
                has_epd_event = flare_index in df_flares.index and df_flares.loc[flare_index, "EPD_EVENT"]
                show_arrival = st.checkbox("Show expected arrival window", value=has_epd_event, key="detail_arrival")
                
                
                if len(columns) != 4:
                    st.warning("Please select exactly 4 channels to display the plot.")
                else:
                    column_indecies = [df_sensor.columns.get_loc(col) for col in columns]
                    
                    st.divider()
                    
                    # Filter data to user-selected time window
                    df_sensor_plot = df_sensor[plot_start:plot_end]
                    df_mean_plot = df_mean[plot_start:plot_end]
                    df_std_plot = df_std[plot_start:plot_end]
                    
                    if df_sensor_plot.empty:
                        st.warning("No sensor data available for this time window.")
                    else:
                        # Create plot
                        plt.rcParams["figure.figsize"] = (16, 10)
                        fig, (flare_ax, *axs) = plt.subplots(5, sharex=False)
                        plt.subplots_adjust(hspace=0)

                        
                        # Plot STIX light curve in the top axis
                        if stix_lc is not None and len(stix_lc) > 0:
                            try:
                                time_difference = pd.to_timedelta((flare["solo_position_AU_distance"] * AU_TO_M) / SPEED, unit="s")

                                # Extract time and flux data from STIX light curve
                                # delta_time is in seconds relative to zero time
                                delta_time = stix_lc["delta_time"] # array
                                counts_low = stix_lc["counts"][0]  # Lowest energy bin (index 0)
                                counts_high = stix_lc["counts"][2] # 15-25keV                                
                                # Convert delta_time to absolute timestamps
 
                                stix_time = pd.to_datetime(stix_lc["start_utc"]) + pd.to_timedelta(delta_time, unit='s') -time_difference
                                
                                # Plot the light curve
                                flare_ax.plot(stix_time, counts_low, color='C0', linewidth=1, label='STIX 4-10keV')
                                flare_ax.plot(stix_time, counts_high, color='C2', linewidth=1, label='STIX 15-25keV')
                                flare_ax.set_ylabel('Counts', fontsize=10)
                                flare_ax.set_yscale('log')
                            except Exception as e:
                                st.warning(f"Could not plot STIX light curve: {e}, {len(stix_time), len(time_difference)}")
                                # Fallback to empty plot
                                df_hold = df_std_plot.copy()
                                df_hold[""] = np.nan
                                df_hold[""].plot(color="black", ax=flare_ax)
                        else:
                            # If no STIX data, create empty plot as before
                            df_hold = df_std_plot.copy()
                            df_hold[""] = np.nan
                            df_hold[""].plot(color="black", ax=flare_ax)
                        
                        # Plot each channel
                        for ax, column in zip(axs, columns):
                            num = int(column.split("_")[-1])
                            energies = epd.get_energies(sensor_name, len(df_sensor.columns))
                            
                            df_sensor_plot[column].plot(
                                color="black", 
                                logy=True, 
                                ax=ax, 
                                label=f"{sensor_name} Channel {num}\n{energies[num]}"
                            )
                            
                            df_threshold = df_std_plot[column] * sigma + df_mean_plot[column]
                            df_threshold.plot(
                                color="green", 
                                logy=True, 
                                ax=ax, 
                                label=f'threshold ({sigma}σ)'
                            )
                        
                        # Plot flare markers
                        shown_labels = set()
                        
                        # Mark the selected flare with appropriate color based on connection status
                        kwargs = {"linewidth": 2}
                        
                        # Determine color based on connection status
                        if flare_index in df_flares.index:
                            is_mct = df_flares.loc[flare_index, "MCT"]
                            is_epd = df_flares.loc[flare_index, "EPD_EVENT"]
                            
                            if is_epd and is_mct:
                                kwargs["color"] = "red"
                                kwargs["label"] = "connected flare"
                            elif is_mct:
                                kwargs["color"] = "orange"
                                kwargs["label"] = "candidate flare\n(mag. connectivity tool)"
                            else:
                                kwargs["color"] = "black"
                                kwargs["label"] = "flare"
                        else:
                            kwargs["color"] = "black"
                            kwargs["label"] = "flare"
                        
                        flare_ax.axvline(pd.to_datetime(flare["_date_peak"]), **kwargs)
                        shown_labels.add(kwargs["label"])
                        
                        # Mark flare start and end
                        flare_ax.axvline(pd.to_datetime(flare["_date_start"]), color="grey", linestyle="--", alpha=0.5, label="flare start/end")
                        flare_ax.axvline(pd.to_datetime(flare["_date_end"]), color="grey", linestyle="--", alpha=0.5)
                        
                        # Plot electron events
                        first = True
                        for col, ax in zip(columns, axs):
                            if col not in events.columns.get_level_values(0):
                                continue
                            
                            for _, event in events[col].iterrows():
                                if event.isna().all():
                                    continue
                                
                                event_start = event["Start"]
                                event_end = event["End"]
                                
                                # Only plot if within time window
                                if event_start > plot_end or event_end < plot_start:
                                    continue
                                
                                kwargs = {"color": "blue", "alpha": 0.2}
                                if first:
                                    first = False
                                    kwargs["label"] = "electron event"
                                
                                ax.axvspan(event_start, event_end, **kwargs)
                        
                        # Plot expected arrival window if enabled and connected
                        if show_arrival and flare_index in df_flares.index:
                            if sensor.is_step:
                                speeds = misc.physics.get_step_speeds(length=len(columns))
                            else:
                                speeds = misc.misc_handler.compute_particle_speed(34, "electron")
                            
                            spiral = parker_dist_series[flare_index]
                            arrive_times = pd.to_timedelta(spiral / speeds, unit="s")
                            
                            first_arrival = True
                            for col_i, ax in zip(column_indecies, axs):
                                arrive_time = arrive_times[col_i]
                                
                                # IS THIS UT? YEAS
                                low = flare["_date_start"] + arrive_time
                                high = flare["_date_end"] + arrive_time * CONFIG.indirect_factor
                                
                                kwargs = {"color": "red", "alpha": 0.15}
                                if first_arrival:
                                    first_arrival = False
                                    kwargs["label"] = "expected arrival window"
                                
                                ax.axvspan(low, high, **kwargs)
                        
                        # Format axes
                        flare_ax.set_xlim(plot_start, plot_end)
                        flare_ax.xaxis.tick_top()
                        #flare_ax.xaxis.set_label_position('top')
                        #flare_ax.tick_params(axis='x', labelsize=8, top=True, labeltop=True)
                        #flare_ax.set_ylabel('Counts', fontsize=9)
                        flare_ax.get_xaxis().set_visible(False)
                        
                        handles, labels = flare_ax.get_legend_handles_labels()
                        if labels:
                            flare_ax.legend(handles, labels, loc="upper right")
                        
                        for ax in axs[:-1]:
                            ax.legend(loc='upper right', fontsize=9)
                            ax.get_xaxis().set_visible(False)
                        
                        axs[-1].legend(loc='upper right', fontsize=9)
                        
                        # Add overall labels
                        fig.add_subplot(111, frameon=False)
                        plt.ylabel('electron intensity [$(cm^2 \ s \ sr \ MeV)^{-1}$]', fontsize=16, loc="center")
                        plt.xlabel('time', fontsize=16, labelpad=20)
                        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
                        
                        st.pyplot(fig)
                        plt.close('all')
                        del fig
    else:
        st.info("Click on a row in the table above to view flare details: tick box on the left of each row")
        highlighted = -1
else:
    st.info("No flares available with current filters.")
    highlighted = -1

# --------------------------------------- OVERVIEW PLOTTING ---------------------------------------

st.divider()

st.subheader(f"Flare Connectivity Summary from {START_DATE} to {END_DATE}")

if highlighted != -1:
    st.info(f"The Flare with ID {flare_range.loc[highlighted]['flare_id']} will be highlighted")

if filter_sensor == "All Sensors":
    st.warning("Please select a specific sensor to view the plot.")
else:
    with st.expander("Plotting options"):
        sensor_name = filter_sensor # use same as above

        sensor = dict_sensor[sensor_name]
        df_flares = sensor.df_connection
        df_mean = sensor.df_mean
        df_std = sensor.df_std
        df_sensor = sensor.df_data
        events = sensor.df_event

        start_date_col, start_time_col, _, end_date_col, end_time_col = st.columns(5)

        _max_val = df_sensor.index.max()
        _min_val = df_sensor.index.min()

        with start_date_col:
            filter_start_date = st.date_input("Start", value=_min_val, max_value=_max_val, min_value=_min_val)

        with start_time_col:
            filter_start_time = st.time_input("Start", value=_min_val, label_visibility="hidden")

        with end_date_col:
            filter_end_date = st.date_input("End", value=_max_val, min_value=filter_start_date, max_value=_max_val)

        with end_time_col:
            filter_end_time = st.time_input("End", value=_max_val, label_visibility="hidden")
        
        columns = []
        column_indecies = []

        for i in range(1, len(df_sensor.columns), len(df_sensor.columns)//3):
            columns.append(df_sensor.columns[int(i)])
            column_indecies.append(int(i))
        
        # Add last channel if length is not 4
        if len(columns) != 4:
            columns.append(df_sensor.columns[-1])
            column_indecies.append(len(df_sensor.columns) - 1)
        
        
        columns = st.multiselect("Select channels", df_sensor.columns, default=columns, max_selections=4)
        columns = sorted(columns, key=lambda x: int(x.split("_")[-1]))
        column_indecies = [df_sensor.columns.get_loc(col) for col in columns]
        if len(columns) != 4:
            st.warning("You need to select 4 channels to plot the data, otherwise the plot will not be rendered correctly.")
            st.stop()


    filter_start = datetime.datetime.combine(filter_start_date, filter_start_time)
    filter_end = datetime.datetime.combine(filter_end_date, filter_end_time)

    mask = (df_flares["_date_peak"] > filter_start) & (df_flares["_date_peak"] < filter_end ) 
    df_flares = df_flares[mask]
    df_mean = df_mean[filter_start: filter_end]
    df_std = df_std[filter_start: filter_end]
    df_sensor = df_sensor[filter_start: filter_end]


    sigma = sensor.sigma


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
        
        if i == highlighted:
            kwargs["color"] = "magenta"
            kwargs["label"] = "highlighted flare (candidate)"
        
        if kwargs["label"] in shown_labels:
            del kwargs["label"]
        else:
            shown_labels.add(kwargs["label"])
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
            if i == highlighted:
                kwargs["color"] = "magenta"
                kwargs["label"] = None
            

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

    if highlighted != -1:
        spiral = parker_dist_series[highlighted]
        arrive_times = pd.to_timedelta(spiral / speeds, unit="s")
        for col_i, ax in zip(column_indecies, axs):
            arrive_time = arrive_times[col_i]
                        
            low = flare_range["_date_start"][highlighted] + arrive_time
            high = flare_range["_date_end"][highlighted] + arrive_time * CONFIG.indirect_factor

            ax.axvspan(low, high, color = 'magenta', alpha = 0.2)

    flare_ax.set_xlim(*axs[0].get_xlim())
    flare_ax.xaxis.tick_top()
    flare_ax.get_yaxis().set_visible(False)

    handles, labels = flare_ax.get_legend_handles_labels()
    if labels:
        # sort both labels and handles by labels
        labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0], reverse=True))
        flare_ax.legend(handles, labels, loc="lower right")

    for ax in axs[:-1]:
        ax.legend(loc = 'lower right')
        ax.get_xaxis().set_visible(False)

    axs[-1].legend(loc = 'lower right')

    # Grouping the plot to align the labels
    fig.add_subplot(111, frameon = False)
    #plt.title(f"{filter_sensor} Data")# TODO needs better name
    plt.ylabel('electron intensity [$(cm^2 \ s \ sr \ MeV)^{-1}$]', fontsize = 20, loc="center")
    plt.xlabel('time', fontsize = 20, labelpad=20)
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    st.pyplot(plt)
    plt.close('all')
    del dict_sensor
    del fig

st.markdown(f"### EPD Sensor Summary from {START_DATE} to {END_DATE}")

st.dataframe(s1, hide_index=True, use_container_width=True)