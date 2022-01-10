### Example of getting the candle that trigger buy of a trade on 5m tf
```
trade_date = timeframe_to_prev_date("5m", trade.open_date_utc)
trade_candle = df.loc[(df['date'] == trade_date)]
```

### Example of using buy tag on custom_sell or stoploss
```
def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:

        sl_new = 1

        buy_tag = 'empty'
        if hasattr(trade, 'buy_tag') and trade.buy_tag is not None:
            buy_tag = trade.buy_tag
        buy_tags = buy_tag.split()

        if (current_profit > 0.2):
            sl_new = 0.05
        elif (current_profit > 0.1):
            sl_new = 0.03
        elif (current_profit > 0.06):
            sl_new = 0.02
        elif (current_profit > 0.03):
            sl_new = 0.01

        // if ema1 is one of the buy tag, always use 3% trailing
        if 'ema1' in buy_tags:
            sl_new = 0.03

        return sl_new
```
