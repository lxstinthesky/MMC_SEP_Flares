from dataclasses import dataclass
import datetime
import pandas as pd
from typing import Optional

@dataclass
class Config:
    window_length: int
    start_date: datetime.date
    end_date: datetime.date
    step_sigma: float
    ept_sigma: float
    delta_flares: float
    needed_channels: int
    indirect_factor: float = 1.5

@dataclass
class SensorData:
    is_step: bool
    sigma: float

    df_data: Optional[pd.DataFrame] = None
    df_mean: Optional[pd.DataFrame] = None
    df_std: Optional[pd.DataFrame] = None
    df_event: Optional[pd.DataFrame] = None
    df_connection: Optional[pd.DataFrame] = None