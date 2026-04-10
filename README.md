# Modeling Magnetic Connectivity of Solar Energetic Particle Events and Solar Flares

Continuation of a masters thesis by Fabian Kistler (ETH Zurich) supervised by Louise Harra (PMOD & ETH Zurich) and Nils Janiztek (PMOD & ETH Zurich).

## Description:

This project aims to model the accuracy of the magnetic connectivity tool (MCT) [4]. This is done using data from the Spectrometer/Telescope for Imaging X-rays (STIX) [3], which is condensed by the STIX team into the STIX flare list [2] (whereas we use the data from March 18, 2021, to May 31, 2024), and the STEP and EPT sensors of the Energetic Particle Detector (EPD) [5].

This project contains the code used for this project and should allow its user to automate the process of finding magnetically connected flare - SEP electron events. As there are many factors influencing the accuracy of the automated process, it is advised to mainly use this in a pre-selection process or manually refine the results. Scientific advancements in the field of solar physics and improvements of our method will hopefully increase the accuracy of this automated process to a point where these manual steps will not be needed anymore.

## Usage:
All the code is tested to run with Python 3.13.2. I also strongly recommend using venv for your installation.
1. Install the requirements: 
    ```sh
    pip install -r requirements.txt
    ```
2. Run the streamlit app: 
    ```sh
    py -m streamlit run Code/streamlit/app.py
    ```
    Or depending on your environment:
    ```sh
    python -m streamlit run Code/streamlit/app.py
    ```

## Structure

![Image](Flare-SEP.png)

- Streamlit Application
    - Main Script
    - Creates an interactive Dashboard and Plots the Data
    - Downloads missing Magnetic Connectivity Tool Data
- bundler.py
    - Packs the generated datasets (for updating purposes)
    - Downloads and unpacks the dataset from Hugginface
- generate_epd_dataset.py
    - Downloads and Samples the EPD Data
- generate_solar_mach_dataset.py
    - Dowloads SolarMACH Data, calculates and saves Parker Spiral distances.


## References:

(1) J. Gieseler, N. Dresing, C. Palmroos, J. L. Freiherr von Forstner, D. J. Price, R. Vainio, A. Kouloumvakos, L. Rodríguez-García, D. Trotta, V. Génot et al., “Solar-mach: An opensource tool to analyze solar magnetic connection configurations,” Frontiers in Astronomy and Space Sciences, vol. 9, p. 1058810, 2023.

(2) L. Hayes, H. Collier, and A. Battaglia, “Solar orbiter/stix science flare list,” URL = [https://github.com/hayesla/stix](https://github.com/hayesla/stix_flarelist_science) flarelist science.

(3) S. Krucker, G. J. Hurford, O. Grimm, S. Kögl, H.-P. Gröbelbauer, L. Etesi, D. Casadei, A. Csillaghy, A. O. Benz, N. G. Arnold et al., “The spectrometer/telescope for imaging x-rays (stix),” Astronomy & Astrophysics, vol. 642, p. A15, 2020.

(4) N. Poirier, A. P. Rouillard, A. Kouloumvakos, A. Przybylak, N. Fargette, R. Pobeda, V. Réville, R. F. Pinto, M. Indurain, and M. Alexandre, “Exploiting white-light observations to improve estimates of magnetic connectivity,” Frontiers in Astronomy and Space Sciences, vol. 8, p. 684734, 2021.

(5) J. Rodríguez-Pacheco, R. Wimmer-Schweingruber, G. Mason, G. Ho, S. Sánchez-Prieto, M. Prieto, C. Martín, H. Seifert, G. Andrews, S. Kulkarni et al., “The energetic particle detector-energetic particle instrument suite for the solar orbiter mission,” Astronomy & Astrophysics, vol. 642, p. A7, 2020.
