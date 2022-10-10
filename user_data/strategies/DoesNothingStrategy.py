# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List, Optional
from functools import reduce
from pandas import DataFrame, Series
# --------------------------------

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from freqtrade.persistence import Trade
import time

logger = logging.getLogger(__name__)


class DoesNothingStrategy(IStrategy):
    """

    author@: Gert Wohlgemuth

    just a skeleton

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 1000
    }

    # Optimal stoploss designed for the strategy
    stoploss = -1

    # Optimal timeframe for the strategy
    timeframe = '1d'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['enter_long'] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['exit_long'] = 0
        return dataframe
