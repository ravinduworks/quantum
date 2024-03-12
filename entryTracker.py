import time
import json

import redis
from datetime import datetime
from orders import OrderManagement
from pubsub import RedisConnection
from instruments import InstrumentLookup
from marketpulse import EntryUpTrendTracker
from marketpulse import EntryDownTrendTracker

from utilities import is_sold
from utilities import convert_last_two_digits_to_float

from constants import BUY_OPEN_POSITIONS_DB
from constants import DEFAULT_STOP_LOSS
from constants import STOCKS_BLOCKED_LIST
from constants import MINIMUM_STOCK_PRICE
from constants import MAXIMUM_STOCK_PRICE
from constants import DEFAULT_PROFIT_TARGET
from constants import BUY_QUANTITY
from constants import TODAYS_TOP_BUY_STOCKS
from constants import TODAYS_TOP_SHORT_STOCKS
from constants import UPTREND_STREAMING_QUEUE
from constants import INSTRUMENT_PATH
from constants import SHORT_DEFAULT_STOP_LOSS
from constants import SHORT_DEFAULT_PROFIT_TARGET
from constants import SHORT_QUANTITY
from constants import SHORT_OPEN_POSITIONS_DB

from constants import ENTRY_UPTREND_COUNT
from constants import ENTRY_DOWNTREND_COUNT

redis_client = RedisConnection()
order_client = OrderManagement()
uptrend_tracker = EntryUpTrendTracker()
downtrend_tracker = EntryDownTrendTracker()
instrument_lookup = InstrumentLookup(INSTRUMENT_PATH)

buy_open_positions = set(redis_client.get_tickers(BUY_OPEN_POSITIONS_DB))
short_open_positions = set(redis_client.get_tickers(SHORT_OPEN_POSITIONS_DB))

def print_order_details(ticker, buy_price, stoploss_price, profit_target, buy_quantity, profit_percentage, order_type):
    current_time = datetime.now().strftime("%H:%M")
    
    order_details = (
        f'Order type : {order_type}\n'
        f'Order time : {current_time}\n'
        f'Entry Percentage: {profit_percentage}%\n'
        f'Placing an order for {buy_quantity} shares of {ticker} at a price of {buy_price} each\n'
        f'Placing stop loss order for {ticker} for the price at {stoploss_price}\n'
        f'Placing Profit SELL order for {ticker} for the price at {profit_target}\n'
    )

    success_message = f'Success! Order placed for {ticker}\n'

    print(order_details + success_message)


while True:
    try:
        print(f'Listening to data stream...')
        subscription = redis_client.subscribe(UPTREND_STREAMING_QUEUE)
        subscription.listen()

        for message in subscription.listen():
            if message['type'] == 'message':
                data_json = message['data']
                tickers = json.loads(data_json)
                stock_symbol = instrument_lookup.symbol_lookup(tickers['token'])

                # BUY CALL
                top_buy_stocks = set(redis_client.get_tickers(TODAYS_TOP_BUY_STOCKS))

                for tick in top_buy_stocks:
                    if tick == stock_symbol:

                        last_traded_price = convert_last_two_digits_to_float(tickers['last_traded_price'])
                        uptrend_tracker.update_stock_data(stock_symbol, last_traded_price)

                        if stock_symbol not in uptrend_tracker.reversal_counts:
                            uptrend_tracker.initialize_reversal_count(stock_symbol)
                
                        now = datetime.now()

                        start_time = datetime(now.year, now.month, now.day, 9, 15)
                        end_time = datetime(now.year, now.month, now.day, 17, 30)

                        if start_time <= now < end_time:
                            if now.minute % 1 == 0:
                                low_price_of_the_day = convert_last_two_digits_to_float(tickers.get('low_price_of_the_day', 0))

                                # buy_price = convert_last_two_digits_to_float(tickers.get('last_traded_price'))
                                upper_circuit = convert_last_two_digits_to_float(tickers.get('upper_circuit_limit'))
                    
                                entry_previous_count = uptrend_tracker.reversal_counts[stock_symbol]['previous_reversal_count']
                                should_enter_buy = uptrend_tracker.is_uptrend(stock_symbol, last_traded_price)
                                
                                if should_enter_buy: # and entry_previous_count == ENTRY_UPTREND_COUNT:
                                
                                    if (
                                        stock_symbol not in STOCKS_BLOCKED_LIST 
                                        and MINIMUM_STOCK_PRICE < last_traded_price < MAXIMUM_STOCK_PRICE 
                                        and stock_symbol not in buy_open_positions
                                        and stock_symbol not in short_open_positions
                                    ):

                                        buy_stoploss_price = order_client.calculate_buy_stoploss_price(DEFAULT_STOP_LOSS, last_traded_price)
                                        buy_profit_target = min(float(order_client.calculate_buy_target_price(DEFAULT_PROFIT_TARGET, last_traded_price)), upper_circuit)

                                        # order_client.place_limit_order(stock_symbol, "BUY", last_traded_price, BUY_QUANTITY)
                                        order_client.place_market_order(stock_symbol, "BUY", BUY_QUANTITY)
                                        order_client.place_sl_limit_order(stock_symbol, "SELL", buy_stoploss_price, BUY_QUANTITY)
                                        order_client.place_limit_order(stock_symbol, "SELL", buy_profit_target, BUY_QUANTITY)

                                        print(stock_symbol, tickers['last_traded_timestamp'])
                                        print_order_details(stock_symbol, last_traded_price, buy_stoploss_price, buy_profit_target, BUY_QUANTITY, DEFAULT_PROFIT_TARGET, 'BUY')

                                        buy_open_positions.add(stock_symbol)
                                        redis_client.update_tickers(BUY_OPEN_POSITIONS_DB, [stock_symbol])  
                                        uptrend_tracker.reset_entry_conditions(stock_symbol)

                                    # Second time entry
                                    # if (
                                    #     stock_symbol not in STOCKS_BLOCKED_LIST 
                                    #     and MINIMUM_STOCK_PRICE < last_traded_price < MAXIMUM_STOCK_PRICE 
                                    #     and stock_symbol not in short_open_positions
                                    #     and stock_symbol in buy_open_positions
                                    # ):
                                    #     time.sleep(3)
                                    #     order_book = order_client.orderbook()
                                    #     if is_sold(order_book, stock_symbol) and entry_previous_count == ENTRY_UPTREND_COUNT:

                                    #             DEFAULT_STOP_LOSS = 0.01
                                    #             BUY_QUANTITY = 50

                                    #             buy_stoploss_price = order_client.calculate_buy_stoploss_price(DEFAULT_STOP_LOSS, last_traded_price)
                                    #             buy_profit_target = min(float(order_client.calculate_buy_target_price(DEFAULT_PROFIT_TARGET, last_traded_price)), upper_circuit)

                                    #             # order_client.place_limit_order(stock_symbol, "BUY", last_traded_price, BUY_QUANTITY)
                                    #             order_client.place_market_order(stock_symbol, "BUY", BUY_QUANTITY)
                                    #             order_client.place_sl_limit_order(stock_symbol, "SELL", buy_stoploss_price, BUY_QUANTITY)
                                    #             order_client.place_limit_order(stock_symbol, "SELL", buy_profit_target, BUY_QUANTITY)

                                    #             print(stock_symbol, tickers['last_traded_timestamp'])
                                    #             print_order_details(stock_symbol, last_traded_price, buy_stoploss_price, buy_profit_target, BUY_QUANTITY, DEFAULT_PROFIT_TARGET, 'BUY')

                                    #             uptrend_tracker.reset_entry_conditions(stock_symbol)

                # # SHORT CALL
                # top_short_stocks = set(redis_client.get_tickers(TODAYS_TOP_SHORT_STOCKS))

                # for tick in top_short_stocks:

                #     if tick == stock_symbol:
                #         last_traded_price = convert_last_two_digits_to_float(tickers['last_traded_price'])
                #         downtrend_tracker.update_stock_data(stock_symbol, last_traded_price)

                #         if stock_symbol not in downtrend_tracker.reversal_counts:
                #             downtrend_tracker.initialize_reversal_count(stock_symbol)
                            
                #         now = datetime.now()

                #         start_time = datetime(now.year, now.month, now.day, 9, 15)
                #         end_time = datetime(now.year, now.month, now.day, 17, 30)


                #         if start_time <= now < end_time:
                #             if now.minute % 1 == 0:
                #                 previous_count = downtrend_tracker.reversal_counts[stock_symbol]['previous_reversal_count']
                #                 should_enter_short = downtrend_tracker.is_downtrend(stock_symbol, last_traded_price)

                #                 # sell_price = convert_last_two_digits_to_float(tickers.get('last_traded_price'))

                #                 lower_circuit = convert_last_two_digits_to_float(tickers.get('lower_circuit_limit'))

                #                 if should_enter_short: #and previous_count == ENTRY_DOWNTREND_COUNT:

                #                     short_stoploss_price = order_client.calculate_short_stoploss_price(SHORT_DEFAULT_STOP_LOSS, last_traded_price)
                #                     short_profit_target = max(float(order_client.calculate_short_target_price(SHORT_DEFAULT_PROFIT_TARGET, last_traded_price)), lower_circuit)


                #                     if (
                #                         stock_symbol not in STOCKS_BLOCKED_LIST 
                #                         and MINIMUM_STOCK_PRICE < last_traded_price < MAXIMUM_STOCK_PRICE 
                #                         and stock_symbol not in short_open_positions
                #                         and stock_symbol not in buy_open_positions
                #                     ):
                #                         order_client.place_limit_order(stock_symbol, "SELL", last_traded_price, SHORT_QUANTITY)
                #                         order_client.place_sl_limit_order(stock_symbol, "BUY", short_stoploss_price, SHORT_QUANTITY)
                #                         order_client.place_limit_order(stock_symbol, "BUY", profit_target, SHORT_QUANTITY)

                #                         print(stock_symbol, tickers['last_traded_timestamp'])
                #                         print_order_details(stock_symbol, last_traded_price, short_stoploss_price, profit_target, SHORT_QUANTITY, SHORT_DEFAULT_PROFIT_TARGET, 'SHORT')
                                        
                #                         short_open_positions.add(stock_symbol)
                #                         redis_client.update_tickers(SHORT_OPEN_POSITIONS_DB, [stock_symbol])
                #                         downtrend_tracker.reset_exit_conditions(stock_symbol)
                #                         # break                  
        time.sleep(300)
 
    except redis.exceptions.ConnectionError as e:
        print(f"Redis Connection Error: {e}")
        time.sleep(5) 