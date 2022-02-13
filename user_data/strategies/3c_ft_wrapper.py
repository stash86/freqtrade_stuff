# --- Do not remove these libs ---
import logging
from freqtrade.persistence import Trade, PairLocks
from datetime import datetime, timedelta, timezone
from py3cw.request import Py3CW

logger = logging.getLogger(__name__)

class 3c_binance_futures (your_strat):

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str, **kwargs) -> bool:
        bot_id = 1234567890

        coin, currency = pair.split('/')

        p3cw = Py3CW(
            key='1',
            secret='2',
        )

        logger.info(f"3Commas: Sending buy signal for {pair} to 3commas bot_id={bot_id}")

        error, data = p3cw.request(
            entity='bots',
            action='start_new_deal',
            action_id=f'{bot_id}',
            payload={
                "bot_id": bot_id,
                "pair": f"{currency}_{coin}{currency}",
            },
        )

        if error:
            logger.error(f"3Commas: {error['msg']}")
        
        PairLocks.lock_pair(
            pair=pair,
            until=datetime.now(timezone.utc) + timedelta(minutes=1),
            reason="Send 3c buy order"
        )

        return False
