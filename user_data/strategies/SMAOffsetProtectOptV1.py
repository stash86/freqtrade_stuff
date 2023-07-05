# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import numpy as np
import freqtrade.vendor.qtpylib.indicators as qtpylib
import datetime
from technical.util import resample_to_interval, resampled_merge
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
from freqtrade.strategy import informative, stoploss_from_open, merge_informative_pair, DecimalParameter, IntParameter, CategoricalParameter
import technical.indicators as ftt

def EWO(dataframe, ema_length=5, ema2_length=35):
    df = dataframe.copy()
    ema1 = ta.EMA(df, timeperiod=ema_length)
    ema2 = ta.EMA(df, timeperiod=ema2_length)
    emadif = (ema1 - ema2) / df['close'] * 100
    return emadif


class SMAOffsetProtectOptV1(IStrategy):
    INTERFACE_VERSION = 3

    # Buy hyperspace params:
    buy_params = {
        "base_nb_candles_buy": 16,
        "ewo_high": 5.638,
        "ewo_low": -19.993,
        "low_offset": 0.978,
        "rsi_buy": 61,
    }

    # Sell hyperspace params:
    sell_params = {
        "base_nb_candles_sell": 49,
        "high_offset": 1.006,
    }

    # ROI table:
    minimal_roi = {
        "0": 0.013
    }

    # Stoploss:
    stoploss = -0.5

    # SMAOffset
    base_nb_candles_buy = IntParameter(
        5, 80, default=6, space='buy', optimize=True)
    base_nb_candles_sell = IntParameter(
        5, 80, default=6, space='sell', optimize=True)
    low_offset = DecimalParameter(
        0.9, 0.99, default=0.9, space='buy', optimize=True)
    high_offset = DecimalParameter(
        0.99, 1.1, default=1, space='sell', optimize=True)

    # Protection
    fast_ewo = 50
    slow_ewo = 200
    ewo_low = DecimalParameter(-20.0, -8.0,
                               default=-12, space='buy', optimize=False)
    ewo_high = DecimalParameter(
        2.0, 12.0, default=4, space='buy', optimize=False)
    rsi_buy = IntParameter(30, 70, default=50, space='buy', optimize=False)


    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.001
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    # Sell signal
    use_exit_signal = True
    exit_profit_only = False
    exit_profit_offset = 0.01
    ignore_roi_if_entry_signal = False

    # Optimal timeframe for the strategy
    timeframe = '5m'

    process_only_new_candles = True
    startup_candle_count = 30

    plot_config = {
        'main_plot': {
            'ma_buy': {'color': 'orange'},
            'ma_sell': {'color': 'orange'},
        },
    }

    use_custom_stoploss = False

    @informative('1h')
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Elliot
        dataframe['EWO'] = EWO(dataframe, self.fast_ewo, self.slow_ewo)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'enter_tag'] = ''

        dataframe['ma_buy'] = ta.EMA(dataframe, timeperiod=int(self.base_nb_candles_buy.value))

        buy_ewo_high = (
            (dataframe['close'] < (dataframe['ma_buy'] * self.low_offset.value)) &
            (dataframe['EWO'] > self.ewo_high.value) &
            (dataframe['rsi'] < self.rsi_buy.value) &
            (dataframe['volume'] > 0)
        )
        dataframe.loc[buy_ewo_high, 'enter_tag'] += 'ewo_high '
        conditions.append(buy_ewo_high)

        buy_ewo_low = (
            (dataframe['close'] < (dataframe['ma_buy'] * self.low_offset.value)) &
            (dataframe['EWO'] < self.ewo_low.value) &
            (dataframe['volume'] > 0)
        )
        dataframe.loc[buy_ewo_low, 'enter_tag'] += 'ewo_low '
        conditions.append(buy_ewo_low)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'enter_long'
            ]=1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'exit_tag'] = ''

        dataframe['ma_sell'] = ta.EMA(dataframe, timeperiod=int(self.base_nb_candles_sell.value))

        sell_cond_1 = (                   
            (dataframe['close'] > (dataframe['ma_sell'] * self.high_offset.value)) &
            (dataframe['volume'] > 0)
        )
        conditions.append(sell_cond_1)
        dataframe.loc[sell_cond_1, 'exit_tag'] += 'ema sell '

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'exit_long'
            ]=1

        return dataframe
