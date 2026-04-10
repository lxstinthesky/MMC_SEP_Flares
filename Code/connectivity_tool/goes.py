import math

def compute_goes_flux(scaled_counts):
    '''
    Estimates the GOES flux depending on the scaled STIX counts (Xiao et al. 2023)
    
    There is a better formula by Muriel Stiefel. For future use implement that formula to get better estimates especially for stronger flares.
    
    parameters:
    scaled counts   (float)     STIX counts for 4-10keV scaled based on SOLOS heliocentric distance
    
    output:
    goes_flux       (float)     estimate of the GOES flux
    '''
    # f = 10**(-7.376+0.622 log10(X0))
    goes_flux = 10**(-7.376 + 0.622 * math.log10(scaled_counts))
    
    return goes_flux # estimate

def get_goes_classification(flux):
    '''
    simple function to convert estimated GOES flux into the better known GOES class scheme.
    
    parameters:
    flux            (float)     the flux value one would like to convert
    
    outputs:
    classification  (string)    converted GOES class
    '''
    if (flux < 10**-7):
        classification = "A"
    elif (flux < 10**-6):
        classification = "B" + str(math.floor(flux / 10**-7))
    elif (flux < 10**-5):
        classification = "C" + str(math.floor(flux / 10**-6))
    elif (flux < 10**-4):
        classification = "M" + str(math.floor(flux / 10**-5))
    else:
        classification = "X" + str(math.floor(flux / 10**-4))
    
    return classification