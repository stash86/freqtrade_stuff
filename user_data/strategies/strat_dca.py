import math
import logging
from datetime import datetime, timedelta, timezone
from freqtrade.persistence import Trade
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class strat_dca (yourstrat):

    position_adjustment_enable = True
    initial_safety_order_trigger = -0.02
    max_entry_position_adjustment = 3
    safety_order_step_scale = 2
    safety_order_volume_scale = 1.8
    
    max_so_multiplier = (1 + max_entry_position_adjustment)
    if(max_entry_position_adjustment > 0):
        if(safety_order_volume_scale > 1):
            max_so_multiplier = (2 + (safety_order_volume_scale * (math.pow(safety_order_volume_scale,(max_entry_position_adjustment - 1)) - 1) / (safety_order_volume_scale - 1)))
        elif(safety_order_volume_scale < 1):
            max_so_multiplier = (2 + (safety_order_volume_scale * (1 - math.pow(safety_order_volume_scale,(max_entry_position_adjustment - 1))) / (1 - safety_order_volume_scale)))

    # Since stoploss can only go up and can't go down, if you set your stoploss here, your lowest stoploss will always be tied to the first buy rate
    # So disable the hard stoploss here, and use custom_sell or custom_stoploss to handle the stoploss trigger
    stoploss = -1

    def custom_sell(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):

        tag = super().custom_sell(pair, trade, current_time, current_rate, current_profit, **kwargs)
        if tag:
            return tag
            
        buy_tag = 'empty'
        if hasattr(trade, 'buy_tag') and trade.buy_tag is not None:
            buy_tag = trade.buy_tag
        buy_tags = buy_tag.split()

        if current_profit <= -0.35:
            return f'stop_loss ({buy_tag})'

        return None

    # Let unlimited stakes leave funds open for DCA orders
    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float, max_stake: float,
                            **kwargs) -> float:
                            
        return proposed_stake / self.max_so_multiplier

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                              current_rate: float, current_profit: float, min_stake: float,
                              max_stake: float, **kwargs) -> Optional[float]:
        if current_profit > self.initial_safety_order_trigger:
            return None

        filled_buys = trade.select_filled_orders('buy')
        count_of_buys = len(filled_buys)

        if 1 <= count_of_buys <= self.max_entry_position_adjustment:
            safety_order_trigger = (abs(self.initial_safety_order_trigger) * count_of_buys)
            if (self.safety_order_step_scale > 1):
                safety_order_trigger = abs(self.initial_safety_order_trigger) + (abs(self.initial_safety_order_trigger) * self.safety_order_step_scale * (math.pow(self.safety_order_step_scale,(count_of_buys - 1)) - 1) / (self.safety_order_step_scale - 1))
            elif (self.safety_order_step_scale < 1):
                safety_order_trigger = abs(self.initial_safety_order_trigger) + (abs(self.initial_safety_order_trigger) * self.safety_order_step_scale * (1 - math.pow(self.safety_order_step_scale,(count_of_buys - 1))) / (1 - self.safety_order_step_scale))

            if current_profit <= (-1 * abs(safety_order_trigger)):
                try:
                    # This returns first order stake size
                    stake_amount = filled_buys[0].cost
                    # This then calculates current safety order size
                    stake_amount = stake_amount * math.pow(self.safety_order_volume_scale,(count_of_buys - 1))
                    amount = stake_amount / current_rate
                    logger.info(f"Initiating safety order buy #{count_of_buys} for {trade.pair} with stake amount of {stake_amount} which equals {amount}")
                    return stake_amount
                except Exception as exception:
                    logger.info(f'Error occured while trying to get stake amount for {trade.pair}: {str(exception)}') 
                    return None

        return None
