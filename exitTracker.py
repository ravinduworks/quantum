import time
import json
import redis

from datetime import datetime

from pubsub import RedisConnection
from orders import OrderManagement
from instruments import InstrumentLookup
from marketpulse import ExitDownTrendTracker
from marketpulse import ExitUpTrendTracker

from utilities import convert_last_two_digits_to_float
from utilities import wait_for_market_open

from constants import BUY_OPEN_POSITIONS_DB
from constants import DOWNTREND_STREAMING_QUEUE
from constants import INSTRUMENT_PATH
from constants import SHORT_OPEN_POSITIONS_DB

from constants import EXIT_UPTREND_COUNT
from constants import EXIT_DOWNTREND_COUNT

from constants import DEFAULT_STOP_LOSS
from constants import DEFAULT_PROFIT_TARGET

from constants import MARKET_OPEN_HOUR
from constants import MARKET_OPEN_MINUTE

redis_client = RedisConnection()
order_client = OrderManagement()

downtrend_tracker = ExitDownTrendTracker()
uptrend_tracker = ExitUpTrendTracker()

# instrument_path = "OpenAPIScripMaster.json"
instrument_lookup = InstrumentLookup(INSTRUMENT_PATH)

buy_open_positions = set(redis_client.get_tickers(BUY_OPEN_POSITIONS_DB))
print('Current BUY positions:')
print(buy_open_positions)
print()

short_open_positions = set(redis_client.get_tickers(SHORT_OPEN_POSITIONS_DB))
print('Current short open positions:')
print(short_open_positions)
print()

wait_for_market_open(MARKET_OPEN_HOUR, 25)

while True:
    try:
        print(f'Listening to data stream...')
        subscription = redis_client.subscribe(DOWNTREND_STREAMING_QUEUE)
        subscription.listen()

        for message in subscription.listen():
            if message['type'] == 'message':
                data_json = message['data']
                tickers = json.loads(data_json)
                stock_symbol = instrument_lookup.symbol_lookup(tickers['token'])

                # EXIT BUY CALL
                buy_open_positions = set(redis_client.get_tickers(BUY_OPEN_POSITIONS_DB))

                for tick in buy_open_positions:
                    if tick == stock_symbol:
                        last_traded_price = convert_last_two_digits_to_float(tickers['last_traded_price'])
                        downtrend_tracker.update_stock_data(stock_symbol, last_traded_price)

                        if stock_symbol not in downtrend_tracker.reversal_counts:
                            downtrend_tracker.initialize_reversal_count(stock_symbol)

                        # purchase_price = order_client.get_buy_average_price(stock_symbol)

                        now = datetime.now()

                        start_time = datetime(now.year, now.month, now.day, 9, 15)
                        end_time = datetime(now.year, now.month, now.day, 17, 30)

                        if start_time <= now < end_time:
                            if now.minute % 1 == 0:
                                highest_price_of_day = convert_last_two_digits_to_float(tickers.get('high_price_of_the_day', 0))
                                buy_previous_count = downtrend_tracker.reversal_counts[stock_symbol]['previous_reversal_count']
                                # should_exit_buy = downtrend_tracker.is_downtrend(stock_symbol, last_traded_price, purchase_price)
                                should_exit_buy = downtrend_tracker.is_downtrend(stock_symbol, last_traded_price)

                                # if should_exit_buy and buy_previous_count == EXIT_DOWNTREND_COUNT:
                                #     if highest_price_of_day:
                                #         price_difference = abs(highest_price_of_day - last_traded_price)
                                #         threshold = highest_price_of_day * 0.005

                                #         if price_difference <= threshold:
                                #             order_book = order_client.orderbook()

                                #             if order_book is not None:
                                #                 for position in order_book:
                                #                     if position['tradingsymbol'] == f"{stock_symbol}-EQ" and position['transactiontype'] == 'SELL' and position['orderstatus'] == 'open':
                                #                         print(f'highest_price_of_day {highest_price_of_day}')
                                #                         print(f'price_difference {price_difference}')
                                #                         print(f'threshold {threshold}')
                                #                         print(f'Exiting order position {stock_symbol}')
                                #                         print('last_traded_timestamp', tickers['last_traded_timestamp'])
                                #                         order_client.modify_order_type(stock_symbol, position['orderid'], "MARKET", position['quantity'])  

                                #             downtrend_tracker.reset_exit_conditions(stock_symbol)
                                #             print()

                                if should_exit_buy and buy_previous_count == EXIT_DOWNTREND_COUNT:
                                    
                                    order_book = order_client.orderbook()

                                    if order_book is not None:
                                        for position in order_book:
                                            if position['tradingsymbol'] == f"{stock_symbol}-EQ" and position['transactiontype'] == 'SELL' and position['orderstatus'] == 'open':
                                                print(f'highest_price_of_day {highest_price_of_day}')
                                                print(f'Exiting order position {stock_symbol}')
                                                print('last_traded_timestamp', tickers['last_traded_timestamp'])
                                                order_client.modify_order_type(stock_symbol, position['orderid'], "MARKET", position['quantity'])  

                                    downtrend_tracker.reset_exit_conditions(stock_symbol)
                                    print()

                # EXIT SHORT CALL
                short_open_positions = set(redis_client.get_tickers(SHORT_OPEN_POSITIONS_DB))

                for tick in short_open_positions:
                    if tick == stock_symbol:

                        last_traded_price = convert_last_two_digits_to_float(tickers['last_traded_price'])
                        uptrend_tracker.update_stock_data(stock_symbol, last_traded_price)

                        if stock_symbol not in uptrend_tracker.reversal_counts:
                            uptrend_tracker.initialize_reversal_count(stock_symbol)
                                            
                        # purchase_price = order_client.get_buy_average_price(stock_symbol)

                        now = datetime.now()

                        start_time = datetime(now.year, now.month, now.day, 9, 15)
                        end_time = datetime(now.year, now.month, now.day, 17, 30)

                        if start_time <= now < end_time:
                            if now.minute % 1 == 0:
                                low_price_of_the_day = convert_last_two_digits_to_float(tickers.get('low_price_of_the_day', 0))
                                short_previous_count = uptrend_tracker.reversal_counts[stock_symbol]['previous_reversal_count']
                                # should_exit_short = uptrend_tracker.is_uptrend(stock_symbol, last_traded_price, purchase_price)
                                should_exit_short = uptrend_tracker.is_uptrend(stock_symbol, last_traded_price)

                                if should_exit_short and short_previous_count == EXIT_UPTREND_COUNT:
                                    if low_price_of_the_day:
                                        price_difference = abs(low_price_of_the_day - last_traded_price)
                                        threshold = low_price_of_the_day * 0.005 #0.01 # threshold

                                        if price_difference <= threshold:
                                            order_book = order_client.orderbook()

                                            if order_book is not None:
                                                for position in order_book:
                                                    if position['tradingsymbol'] == f"{stock_symbol}-EQ" and position['transactiontype'] == 'BUY' and position['orderstatus'] == 'open':
                                                        print(f'highest_price_of_day {low_price_of_the_day}')
                                                        print(f'Exiting order position {stock_symbol}')
                                                        print('last_traded_timestamp', tickers['last_traded_timestamp'])
                                                        order_client.modify_order_type(stock_symbol, position['orderid'], "MARKET", position['quantity'])
                                            uptrend_tracker.reset_entry_conditions(stock_symbol)
                                            print()

        # time.sleep(300)

    except redis.exceptions.ConnectionError as e:
        print(f"Redis Connection Error: {e}")
        time.sleep(5)


