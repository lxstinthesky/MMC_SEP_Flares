import math
import datetime
import pandas as pd
import config
import numpy as np

def get_epd_bins(type):
    '''
    list of energy ranges of ion/electron bins
    
    parameters:
    type: string of particle type [ion, electron]
    '''
    if type == 'ion':
        return [['0.0495 - 0.0574 MeV'], ['0.0520 - 0.0602 MeV'], ['0.0552 - 0.0627 MeV'], ['0.0578 - 0.0651 MeV'], ['0.0608 - 0.0678 MeV'], ['0.0645 - 0.0718 MeV'], ['0.0689 - 0.0758 MeV'], ['0.0729 - 0.0798 MeV'],
                ['0.0768 - 0.0834 MeV'], ['0.0809 - 0.0870 MeV'], ['0.0870 - 0.0913 MeV'], ['0.0913 - 0.0974 MeV'], ['0.0974 - 0.1034 MeV'], ['0.1034 - 0.1096 MeV'], ['0.1096 - 0.1173 MeV'], ['0.1173 - 0.1246 MeV'],
                ['0.1246 - 0.1333 MeV'], ['0.1333 - 0.1419 MeV'], ['0.1419 - 0.1514 MeV'], ['0.1514 - 0.1628 MeV'], ['0.1628 - 0.1744 MeV'], ['0.1744 - 0.1879 MeV'], ['0.1879 - 0.2033 MeV'], ['0.2033 - 0.2189 MeV'],
                ['0.2189 - 0.2364 MeV'], ['0.2364 - 0.2549 MeV'], ['0.2549 - 0.2744 MeV'], ['0.2744 - 0.2980 MeV'], ['0.2980 - 0.3216 MeV'], ['0.3216 - 0.3494 MeV'], ['0.3494 - 0.3810 MeV'], ['0.3810 - 0.4117 MeV'],
                ['0.4117 - 0.4472 MeV'], ['0.4472 - 0.4850 MeV'], ['0.4850 - 0.5255 MeV'], ['0.5255 - 0.5734 MeV'], ['0.5734 - 0.6216 MeV'], ['0.6216 - 0.6767 MeV'], ['0.6767 - 0.7401 MeV'], ['0.7401 - 0.8037 MeV'],
                ['0.8037 - 0.8752 MeV'], ['0.8752 - 0.9500 MeV'], ['0.9500 - 1.0342 MeV'], ['1.0342 - 1.1294 MeV'], ['1.1294 - 1.2258 MeV'], ['1.2258 - 1.3376 MeV'], ['1.3376 - 1.4641 MeV'], ['1.4641 - 1.5934 MeV'],
                ['1.5934 - 1.7372 MeV'], ['1.7372 - 1.8867 MeV'], ['1.8867 - 2.0537 MeV'], ['2.0537 - 2.2479 MeV'], ['2.2479 - 2.4375 MeV'], ['2.4375 - 2.6602 MeV'], ['2.6602 - 2.9209 MeV'], ['2.9209 - 3.1725 MeV'],
                ['3.1725 - 3.4609 MeV'], ['3.4609 - 3.7620 MeV'], ['3.7620 - 4.0993 MeV'], ['4.0993 - 4.4821 MeV'], ['4.4821 - 4.8701 MeV'], ['4.8701 - 5.3147 MeV'], ['5.3147 - 5.8322 MeV'], ['5.8322 - 6.1316 MeV']]
    
    if type == 'electron':
        return [['0.0312 - 0.0354 MeV'], ['0.0334 - 0.0374 MeV'], ['0.0356 - 0.0396 MeV'], ['0.0382 - 0.0420 MeV'], ['0.0408 - 0.0439 MeV'], ['0.0439 - 0.0467 MeV'], ['0.0467 - 0.0505 MeV'],
                ['0.0505 - 0.0542 MeV'], ['0.0542 - 0.0588 MeV'], ['0.0588 - 0.0635 MeV'], ['0.0635 - 0.0682 MeV'], ['0.0682 - 0.0739 MeV'], ['0.0739 - 0.0798 MeV'], ['0.0798 - 0.0866 MeV'],
                ['0.0866 - 0.0942 MeV'], ['0.0942 - 0.1021 MeV'], ['0.1021 - 0.1107 MeV'], ['0.1107 - 0.1207 MeV'], ['0.1207 - 0.1314 MeV'], ['0.1314 - 0.1432 MeV'], ['0.1432 - 0.1552 MeV'],
                ['0.1552 - 0.1690 MeV'], ['0.1690 - 0.1849 MeV'], ['0.1849 - 0.2004 MeV'], ['0.2004 - 0.2182 MeV'], ['0.2182 - 0.2379 MeV'], ['0.2379 - 0.2590 MeV'], ['0.2590 - 0.2826 MeV'],
                ['0.2826 - 0.3067 MeV'], ['0.3067 - 0.3356 MeV'], ['0.3356 - 0.3669 MeV'], ['0.3669 - 0.3993 MeV'], ['0.3993 - 0.4352 MeV'], ['0.4353 - 0.4742 MeV']]
        
    return 'Invalid particle type'



def bin_upper_energy_limit(bin, type):
    '''
    returns upper energy limit of chosen bin
    
    parameters:
    bin:    int of energy bin that we look at
    type:   string of particle type [ion, electron]
    '''
    return float(get_epd_bins(type)[bin][0][9:15])
    

def compute_particle_speed(n_bins, particle_type):
    '''
    Compute the relativistic speed of the fastest particles that are measured in the corresponding bin using E = 1/2 * m * v**2
    
    Parameters:
    bin = number of bin of which the particle speed should be returned
    particle_type = ['ion', 'electron']
    '''
    m = 0
    c = 299792458 # [m/s] speed of light
    if particle_type == 'ion':
        # mass of proton
        m = 1.67262192e-27
    if particle_type == 'electron':
        # mass of electron
        m = 9.1093837015e-31
        
    KE = np.empty(n_bins)
    
    for i in range(n_bins):
        KE[i] = bin_upper_energy_limit(i, particle_type) * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]
    
    return np.sqrt(1 - (1 / (KE / (m * c**2) + 1)**2)) * c  # relativistic formula for kinetic energy