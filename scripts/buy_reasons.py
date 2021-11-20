#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
buy_reasons.py

Usage:

buy_reasons.py -c <config.json> -s <strategy_name> -t <timerange> -g<[0,1,2,3,4]> [-l <path_to_data_dir>]

Example:

buy_reasons.py -c my_config.json -s DoNothingStrategy -t 20211001- -g0,1,2

A script to parse freqtrade backtesting trades and display them with their buy_tag and sell_reason

Author: froggleston [https://github.com/froggleston]
Licence: MIT [https://github.com/froggleston/freqtrade-buyreasons/blob/main/LICENSE]

Donations:
    BTC: bc1qxdfju58lgrxscrcfgntfufx5j7xqxpdufwm9pv
    ETH: 0x581365Cff1285164E6803C4De37C37BbEaF9E5Bb
"""

import json, os
from pathlib import Path

from freqtrade.configuration import Configuration, TimeRange
from freqtrade.data.btanalysis import load_trades_from_db, load_backtest_data, load_backtest_stats
from freqtrade.data.history import load_pair_history
from freqtrade.data.dataprovider import DataProvider
from freqtrade.plugins.pairlistmanager import PairListManager
from freqtrade.exceptions import ExchangeError, OperationalException
from freqtrade.exchange import Exchange
from freqtrade.resolvers import ExchangeResolver, StrategyResolver

from joblib import Parallel, cpu_count, delayed, dump, load, wrap_non_picklable_objects

import numpy as np
import pandas as pd

import copy
import threading

from tabulate import tabulate
import argparse

import concurrent.futures as fut
from functools import reduce

lock = threading.Lock()

def do_analysis(pair=None, config=None, candles=None, trades=None, strategy=None, timeframe="5m", timerange=None, user_data_dir="user_data", data_location=None, data_format="json", verbose=False, rk_tags=False, alt_tag="buy"):
    
    if candles is None:
        if config["timeframe"] is not None:
            timeframe = config["timeframe"]
            if verbose:
                print("Using config timeframe:" , timeframe)
        elif strategy.timeframe is not None:
            timeframe = strategy.timeframe
            if verbose:
                print("Using strategy timeframe:" , timeframe)
        else:
            if verbose:
                print("Using default timeframe:" , timeframe)

        if data_location is None:
            data_location = Path(user_data_dir, 'data', config['exchange']['name'])
        
        if verbose:
            print("Loading historic data...")
            
        if timerange is not None:
            candles = load_pair_history(datadir=data_location,
                                        timeframe=timeframe,
                                        timerange=timerange,
                                        pair=pair,
                                        data_format = data_format,
                                        )
        else:
            candles = load_pair_history(datadir=data_location,
                                        timeframe=timeframe,
                                        pair=pair,
                                        data_format = data_format,
                                        )
    # Confirm success
    if verbose:
        print("Loaded " + str(len(candles)) + f" rows of data for {pair} from {data_location}")
    
    with lock:
        df = strategy.analyze_ticker(candles, {'pair': pair})
        
        if verbose:
            print(f"Generated {df['buy'].sum()} buy / {df['sell'].sum()} sell signals")
        data = df.set_index('date', drop=False)

    return do_trade_buys(pair, data, trades, rk_tags, alt_tag)

def do_trade_buys(pair, data, trades, rk_tags=False, alt_tag="buy"):
    # Filter trades to one pair
    trades_red = trades.loc[trades['pair'] == pair].copy()
    
    if trades_red.shape[0] > 0:
        
        rg = r"^" + alt_tag
        
        buyf = data[data.filter(regex=rg, axis=1).values==1]
        
        if buyf.shape[0] > 0:
            for t, v in trades_red.open_date.items():
                bt = buyf.loc[(buyf['date'] < v)].iloc[-1].filter(regex=rg, axis=0)
                bt.dropna(inplace=True)
                bt.drop(f"{alt_tag}", inplace=True)
                
                if (bt.shape[0] > 0):
                    if rk_tags:
                        trades_red.loc[t, 'buy_reason'] = bt.index.values[0]
                    else:
                        # print(trades_red.loc[t, 'buy_tag'])
                        trades_red.loc[t, 'buy_reason'] = trades_red.loc[t, 'buy_tag']

        cancelf = data[data.filter(regex=r'^cancel', axis=1).values==1]
        if cancelf.shape[0] > 0:
            for t, v in trades_red.open_date.items():
                bt = cancelf.loc[(cancelf['date'] < v)].iloc[-1].filter(regex=r'^cancel', axis=0)
                bt.dropna(inplace=True)
                #bt.drop("buy", inplace=True)
                if (bt.shape[0] > 0):
                    trades_red.loc[t, 'cancel_reason'] = bt.index.values[0]
                    
        ## comment in if you're doing plotting and want to show the values in the sell_reason
            # trades_red.loc[t, 'sell_reason'] = f"{bt.index.values[0]} / {trades_red.loc[t, 'sell_reason']}"

        return trades_red
    else:
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-c", "--config", help="config to parse")
    parser.add_argument("-t", "--timerange", nargs='?', help="timerange as per freqtrade format, e.g. 20210401-, 20210101-20210201, etc")
    parser.add_argument("-s", "--strategy", nargs='?', help="strategy available in user_data/strategies to parse, e.g. AweseomeStrategy. if not supplied, will use the strategy defined in config supplied")
    parser.add_argument("-p", "--pairlist", nargs='?', help="pairlist as 'BTC/USDT,FOO/USDT,BAR/USDT'")
    parser.add_argument("-u", "--use_trades_db", action="store_true", help="use dry/live trade DB specified in config instead of backtest results DB. Default: False")
    parser.add_argument("-w", "--write_out", help="write an output CSV per pair", action="store_true")
    parser.add_argument("-g", "--group", nargs='?', help="grouping output - 0: simple wins/losses by buy reason, 1: by buy_reason, 2: by buy_reason and sell_reason, 3: by pair and buy_reason, 4: by pair, buy_ and sell_reason (this can get quite large)")
    parser.add_argument("-o", "--outfile", help="write all trades summary table output", type=argparse.FileType('w'))
    parser.add_argument("-d", "--data_format", nargs='?', choices=["json", "hdf5"], help="specify the jsons or hdf5 datas. default is json")
    parser.add_argument("-l", "--data_dir_location", nargs='?', help="specify the path to the downloaded OHLCV jsons or hdf5 datas. default is user_data/data/<exchange_name>")
    parser.add_argument("-i", "--indicators", nargs='?', help="Indicator values to output, as a comma separated list, e.g. -i rsi,adx,macd")
    parser.add_argument("-x", "--cancels", action="store_true", help="Output buy cancel reasons. Default: False")    
    parser.add_argument("-r", "--rk_tags", action="store_true", help="Use the ConditionLabeler tags instead of the newer buy_tag tagging feature in FT. Default: False")
    parser.add_argument("-a", "--alternative_tag_name", nargs='?', help="Supply a different buy_tag name to use instead of 'buy', e.g. 'prebuy'. This is for more complex buy_tag use in strategies.")
    parser.add_argument("-v", "--verbose", help="verbose", action="store_true")
    args = parser.parse_args()
    
    configs = [args.config]

    ft_config = Configuration.from_files(files=configs)
    ft_exchange_name = ft_config['exchange']['name']
    ft_exchange = ExchangeResolver.load_exchange(ft_exchange_name, config=ft_config, validate=True)
    ft_pairlists = PairListManager(ft_exchange, ft_config)
    ft_dataprovider = DataProvider(ft_config, ft_exchange, ft_pairlists)

    user_data_dir = ft_config['user_data_dir']
    
    data_location = Path(user_data_dir, 'data', ft_exchange_name)
    if args.data_dir_location is not None:
        data_location = Path(args.data_dir_location)
    
    ft_config['datadir'] = data_location
    
    backtest_dir = Path(user_data_dir, 'backtest_results')

    if args.group is not None and args.indicators is not None:
        print("WARNING: cannot use indicator output with grouping. Ignoring indicator output")
    
    if args.pairlist is None:
        pairlist = ft_pairlists.whitelist
    else:
        pairlist = args.pairlist.split(",")
    
    if args.data_format is None:
        data_format = "json"
    else:
        data_format = args.data_format

    if args.alternative_tag_name is None:
        alternative_tag_name = "buy"
    else:
        alternative_tag_name = args.alternative_tag_name
        
    timeframe = "5m"
    backtest = False

    if args.strategy is None:
        strategy = StrategyResolver.load_strategy(ft_config)
    else:
        ft_config["strategy"] = args.strategy
        strategy = StrategyResolver.load_strategy(ft_config)

    strategy.dp = ft_dataprovider    
    
    use_trades_db = False
    if args.use_trades_db is not None:
        use_trades_db = args.use_trades_db
    
    if use_trades_db is True:
        # Fetch trades from database
        print("Loading DB trades data...")
        trades = load_trades_from_db(ft_config['db_url'])
    else:
        if args.strategy is None:
            print("Loading backtest trades data...")
            trades = load_backtest_data(backtest_dir)
        else:
            print(f"Loading backtest trades data for {args.strategy} ...")
            trades = load_backtest_data(backtest_dir, args.strategy)       

    all_candles=dict()
    print(f'Loading all candle data...')
    
    for pair in pairlist:
        if args.timerange is not None:
            ptr = TimeRange.parse_timerange(args.timerange)
            candles = load_pair_history(datadir=data_location,
                                        timeframe=timeframe,
                                        timerange=ptr,
                                        pair=pair,
                                        data_format = data_format,
                                        )
        else:
            candles = load_pair_history(datadir=data_location,
                                        timeframe=timeframe,
                                        pair=pair,
                                        data_format = data_format,
                                        )
        all_candles[pair] = candles

    columns = ['pair', 'open_date', 'close_date', 'profit_abs', 'buy_reason', 'sell_reason']
    bigdf = pd.DataFrame()
    count = 1
    tbresults = dict()
    
    for i in pairlist:
        print(f"Processing {i} [{count}/{len(pairlist)}]")
        try:
            tb = do_analysis(pair=i, trades=trades, strategy=strategy, candles=all_candles[i], config=ft_config, timeframe=timeframe, timerange=TimeRange.parse_timerange(args.timerange), user_data_dir=user_data_dir, data_location=data_location, data_format=data_format, verbose=args.verbose, rk_tags=args.rk_tags, alt_tag=alternative_tag_name)

            if args.verbose:
                print(tabulate(tb[columns], headers = 'keys', tablefmt = 'psql'))

            if args.write_out:
                tb.to_csv(f'{i.split("/")[0]}_trades.csv')

            bigdf = bigdf.append(tb, ignore_index=True)

        except Exception as e:
            print("Something got zucked: No trades with this pair or you don't have buy_tags in your dataframe:", e)
        finally:
            count += 1
    
    if args.outfile:
        args.outfile.write(bigdf.to_csv())
    else:
        bigdf.to_csv(f'all_trade_buys.csv')
    
    if bigdf.shape[0] > 0 and ('buy_reason' in bigdf.columns):
        
        if args.group is not None:
            glist = args.group.split(",")
            
            if "0" in glist:
                new = bigdf.groupby(['buy_reason']).agg({'profit_abs': ['count', lambda x: sum(x > 0), lambda x: sum(x <= 0)]}).reset_index()
                new.columns = ['buy_reason', 'total_num_buys', 'wins', 'losses']
                new['wl_ratio_pct'] = (new['wins']/new['total_num_buys']*100)
                sortcols = ['total_num_buys']
                print_table(new, sortcols)
            if "1" in glist:
                new = bigdf.groupby(['buy_reason']).agg({'profit_abs': ['count', 'sum', 'median', 'mean'], 'profit_ratio': ['sum', 'median', 'mean']}).reset_index()
                new.columns = ['buy_reason', 'num_buys', 'profit_abs_sum', 'profit_abs_median', 'profit_abs_mean', 'median_profit_pct', 'mean_profit_pct', 'total_profit_pct']
                sortcols = ['profit_abs_sum', 'buy_reason']

                new['median_profit_pct'] = new['median_profit_pct']*100
                new['mean_profit_pct'] = new['mean_profit_pct']*100
                new['total_profit_pct'] = new['total_profit_pct']*100

                print_table(new, sortcols)
            if "2" in glist:
                new = bigdf.groupby(['buy_reason', 'sell_reason']).agg({'profit_abs': ['count', 'sum', 'median', 'mean'], 'profit_ratio': ['sum', 'median', 'mean']}).reset_index()
                new.columns = ['buy_reason', 'sell_reason', 'num_buys', 'profit_abs_sum', 'profit_abs_median', 'profit_abs_mean', 'median_profit_pct', 'mean_profit_pct', 'total_profit_pct']
                sortcols = ['profit_abs_sum', 'buy_reason']

                new['median_profit_pct'] = new['median_profit_pct']*100
                new['mean_profit_pct'] = new['mean_profit_pct']*100
                new['total_profit_pct'] = new['total_profit_pct']*100

                print_table(new, sortcols)
            if "3" in glist:
                new = bigdf.groupby(['pair', 'buy_reason']).agg({'profit_abs': ['count', 'sum', 'median', 'mean'], 'profit_ratio': ['sum', 'median', 'mean']}).reset_index()
                new.columns = ['pair', 'buy_reason', 'num_buys', 'profit_abs_sum', 'profit_abs_median', 'profit_abs_mean', 'median_profit_pct', 'mean_profit_pct', 'total_profit_pct']
                sortcols = ['profit_abs_sum', 'buy_reason']

                new['median_profit_pct'] = new['median_profit_pct']*100
                new['mean_profit_pct'] = new['mean_profit_pct']*100
                new['total_profit_pct'] = new['total_profit_pct']*100

                print_table(new, sortcols)
            if "4" in glist:
                new = bigdf.groupby(['pair', 'buy_reason', 'sell_reason']).agg({'profit_abs': ['count', 'sum', 'median', 'mean'], 'profit_ratio': ['sum', 'median', 'mean']}).reset_index()
                new.columns = ['pair', 'buy_reason', 'sell_reason', 'num_buys', 'profit_abs_sum', 'profit_abs_median', 'profit_abs_mean', 'median_profit_pct', 'mean_profit_pct', 'total_profit_pct']
                sortcols = ['profit_abs_sum', 'buy_reason']

                new['median_profit_pct'] = new['median_profit_pct']*100
                new['mean_profit_pct'] = new['mean_profit_pct']*100
                new['total_profit_pct'] = new['total_profit_pct']*100

                print_table(new, sortcols)
        else:
#            if args.indicators is not None:
#                ilist = args.indicators.split(",")
#                for ind in ilist:

            print(tabulate(bigdf[columns].sort_values(['open_date', 'pair']), headers = 'keys', tablefmt = 'psql', showindex=False))
    
        if args.cancels:
            if bigdf.shape[0] > 0 and ('cancel_reason' in bigdf.columns):
                
                cs = bigdf.groupby(['buy_reason']).agg({'profit_abs': ['count'], 'cancel_reason': ['count']}).reset_index()
                cs.columns = ['buy_reason', 'num_buys', 'num_cancels']
                cs['percent_cancelled'] = (cs['num_cancels']/cs['num_buys']*100)
                
                sortcols = ['num_cancels']
                print_table(cs, sortcols)

    else:
        print("\_ No trades to show")

def print_table(df, sortcols=None):
    if (sortcols is not None):
        data = df.sort_values(sortcols)
    else:
        data = df
        
    print(
        tabulate(
            data,
            headers = 'keys',
            tablefmt = 'psql',
            showindex=False
        )
    )
    
def wl(x):
    return f"{(lambda x: sum(x > 0))}/{(lambda x: sum(x <= 0))}"

if __name__ == "__main__":
    main()
