import pandas as pd

from tqdm import tqdm
import stix
import misc
import config

# read STIX flare list and extract coordinates of the origin
stix_flares = stix.read_list()

df = pd.DataFrame(index = range(len(stix_flares)), columns = ['Parker_Spiral_Distance'])

dest = f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl"

dest_temp = f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance_temp.pkl"

for i in tqdm(df.index):
    if i % 100 == 0:
        df.to_pickle(dest_temp)
        
        print("--------------------------------------------------------------")
        print("Done until", i)
        print("--------------------------------------------------------------")
    
    timestamp = stix_flares['peak_UTC'][i]
    print("working on", timestamp[0:10], timestamp[11:16])
    df['Parker_Spiral_Distance'][i] = misc.parker_spiral_distance(timestamp)

df.to_pickle(dest)