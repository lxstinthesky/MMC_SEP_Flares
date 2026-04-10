import datetime
import numpy as np
import math

def parker_spiral_distance(timestamp):
    from solarmach import SolarMACH
    '''
    Approximating the distance the particles have to travel until reaching SOLO
    This is done using data from the SolarMACH tool
    
    Parameters:
    utc: string of time
    '''
    utc = str(timestamp)[0:10] + ' ' + str(timestamp)[11:19]
    body_list = ['Solar Orbiter']
    df = SolarMACH(utc, body_list).coord_table
    
    mag_footpoint_lon = df['Magnetic footpoint longitude (Carrington)'][0]
    heliocentric_dist = df['Heliocentric distance (AU)'][0]
    sw_speed = df['Vsw'][0]
    solo_lon = df['Carrington longitude (°)'][0]
    solo_lat = df['Carrington latitude (°)'][0]
    
    r = 150e9 * heliocentric_dist
    theta = ((mag_footpoint_lon - solo_lon) % 360) * math.pi / 180
    
    return r / (2 * theta) * (theta * math.sqrt(1 + theta**2) + math.log(theta + math.sqrt(1 + theta**2)))

def step_delay(date, length, parker_dist=None):
    energies_32 = [0.0090, 0.0091, 0.0094, 0.0098, 0.0102, 0.0108, 0.0114, 0.0121, 0.0129, 0.0137, 0.0146, 0.0157, 0.0168, 0.0180, 0.0193, 0.0206,
                0.0221, 0.0237, 0.0254, 0.0274, 0.0295, 0.0317, 0.0341, 0.0366, 0.0394, 0.0425, 0.0459, 0.0498, 0.0539, 0.0583, 0.0629, 0.0680]
    energies_48 = [0.0090, 0.0091, 0.0092, 0.0094, 0.0096, 0.0098, 0.0101, 0.0105, 0.0109, 0.0112, 0.0128, 0.0141, 0.0148, 0.0153, 0.0163, 0.0171,
                0.0177, 0.0186, 0.0195, 0.0202, 0.0213, 0.0224, 0.0237, 0.0248, 0.0257, 0.0274, 0.0288, 0.0298, 0.0317, 0.0332, 0.0344, 0.0366,
                0.0384, 0.0411, 0.0431, 0.0447, 0.0478, 0.0502, 0.0522, 0.0560, 0.0586, 0.0609, 0.0655, 0.0683, 0.0738, 0.0771, 0.0802, 0.0865]

    if parker_dist is None:
        if type(date) == str:
            dist = parker_spiral_distance(datetime.datetime.strptime(date[2:10] + " 00:00:00", "%y-%m-%d %H:%M:%S"))
        else:
            dist = parker_spiral_distance(date)
    else:
        dist = parker_dist

    c = 299792458 # [m/s] speed of light
    m = 9.1093837015e-31 # Mass electron
        
    KE = np.empty(length)

    if length == 32:
        for i in range(length):
            KE[i] = energies_32[i] * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]
    else:
        for i in range(length):
            KE[i] = energies_48[i] * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]

    v = np.sqrt(1 - (1 / (KE / (m * c**2) + 1)**2)) * c  # relativistic formula for kinetic energy

    dt = []
    for i in range(length):
        dt.append(dist / v[i])
    
    return dt

def get_step_speeds(length):
    energies_32 = [0.0090, 0.0091, 0.0094, 0.0098, 0.0102, 0.0108, 0.0114, 0.0121, 0.0129, 0.0137, 0.0146, 0.0157, 0.0168, 0.0180, 0.0193, 0.0206,
                0.0221, 0.0237, 0.0254, 0.0274, 0.0295, 0.0317, 0.0341, 0.0366, 0.0394, 0.0425, 0.0459, 0.0498, 0.0539, 0.0583, 0.0629, 0.0680]
    energies_48 = [0.0090, 0.0091, 0.0092, 0.0094, 0.0096, 0.0098, 0.0101, 0.0105, 0.0109, 0.0112, 0.0128, 0.0141, 0.0148, 0.0153, 0.0163, 0.0171,
                0.0177, 0.0186, 0.0195, 0.0202, 0.0213, 0.0224, 0.0237, 0.0248, 0.0257, 0.0274, 0.0288, 0.0298, 0.0317, 0.0332, 0.0344, 0.0366,
                0.0384, 0.0411, 0.0431, 0.0447, 0.0478, 0.0502, 0.0522, 0.0560, 0.0586, 0.0609, 0.0655, 0.0683, 0.0738, 0.0771, 0.0802, 0.0865]

    energies = energies_48
    if length == 32:
        energies = energies_32
    
    c = 299792458 # [m/s] speed of light
    m = 9.1093837015e-31 # Mass electron
    np_energies = np.array(energies) * 1.60218e-13 # Joules
    return np.sqrt(1 - (1 / (np_energies / (m * c**2) + 1)**2)) * c