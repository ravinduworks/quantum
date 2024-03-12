import json
import time
import redis

from pubsub import RedisConnection
from orders import OrderManagement
from instruments import InstrumentLookup
from marketpulse import analyse_stock_movement

from constants import INDICES_LIST
from constants import STREAMING_QUEUE
from constants import NUMBER_OF_TOP_ITEMS
from constants import TODAYS_TOP_BUY_STOCKS
from constants import TODAYS_TOP_SHORT_STOCKS
from constants import TODAYS_ALL_TOP_BUY_STOCKS
from constants import TODAYS_ALL_TOP_SHORT_STOCKS

order_client = OrderManagement()
redis_client = RedisConnection()
instrument_path = "OpenAPIScripMaster.json"
instrument_lookup = InstrumentLookup(instrument_path)

buy_positions = set(redis_client.get_tickers(TODAYS_ALL_TOP_BUY_STOCKS))
print('Current open positions:')
print(buy_positions)
print()

short_positions = set(redis_client.get_tickers(TODAYS_ALL_TOP_SHORT_STOCKS))
print('Current short positions:')
print(short_positions)
print()

while True:
    try:
        print('Waiting for stream to start...\n')
        for message in redis_client.subscribe(STREAMING_QUEUE).listen():

            if message['type'] == 'message':
                data_json = message['data']
                
                # Convert JSON data back to a dictionary
                tick = json.loads(data_json)
                
                final_data = analyse_stock_movement(tick, INDICES_LIST, NUMBER_OF_TOP_ITEMS)
                
                if final_data is not None:
                    # BUY CALL
                    buy_items = final_data['top_buy_data']
                    buy_tickers = [instrument_lookup.symbol_lookup(item) for item in buy_items]
                    redis_client.update_tickers(TODAYS_TOP_BUY_STOCKS, buy_tickers)

                    existing_buy_tickers = set(redis_client.get_tickers(TODAYS_TOP_BUY_STOCKS))
                    buy_tickers_to_remove = existing_buy_tickers - set(buy_tickers)

                    if buy_tickers_to_remove:
                        redis_client.delete_tickers(TODAYS_TOP_BUY_STOCKS, *buy_tickers_to_remove)
                    print(f'buy tickers: {buy_tickers}')

                    # This is for tracking all top stocks for the day
                    redis_client.update_tickers(TODAYS_ALL_TOP_BUY_STOCKS, buy_tickers)

                    # SHORT CALL
                    short_items = final_data['top_short_data']
                    short_tickers = [instrument_lookup.symbol_lookup(item) for item in short_items]
                    redis_client.update_tickers(TODAYS_TOP_SHORT_STOCKS, short_tickers)

                    existing_short_tickers = set(redis_client.get_tickers(TODAYS_TOP_SHORT_STOCKS))
                    short_tickers_to_remove = existing_short_tickers - set(short_tickers)

                    if short_tickers_to_remove:
                        redis_client.delete_tickers(TODAYS_TOP_SHORT_STOCKS, *short_tickers_to_remove)
                    print(f'short tickers: {short_tickers}')

                    # This is for tracking all top stocks for the day
                    redis_client.update_tickers(TODAYS_ALL_TOP_SHORT_STOCKS, short_tickers)


    except redis.exceptions.ConnectionError as e:
        print(f"Redis Connection Error: {e}")
        time.sleep(5)

            