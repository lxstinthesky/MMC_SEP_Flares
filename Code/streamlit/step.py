import pandas as pd
import numpy as np
import misc
import config
from classes import Config


def cleanup_sensor(df_step: pd.DataFrame):
    """
    Removes unused Columns and Calculates the Electron count. Returns a new Dataframe with the Electron count.
    """
    length = 32
    if ('Integral_Avg_Flux_47' in df_step.columns):
        length = 48
    df_step_electron = pd.DataFrame(columns = [], index = df_step.index)
    zipped_columns = [(f'Electron_Flux_{i}', f"Integral_Avg_Flux_{i}", f"Magnet_Avg_Flux_{i}") for i in range(length)]

    for electron_col, integral_col, magnet_col in zipped_columns:
        df_step_electron[electron_col] = df_step[integral_col] - df_step[magnet_col]

    return df_step_electron

