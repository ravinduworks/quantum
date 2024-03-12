import time
import threading
from login import AngelBrokingAPI
from pubsub import RedisConnection

from constants import INDICES_LIST
from constants import STREAMING_QUEUE
from constants import MARKET_OPEN_HOUR
from constants import MARKET_OPEN_MINUTE
from constants import DOWNTREND_STREAMING_QUEUE
from constants import UPTREND_STREAMING_QUEUE

class DataStreamer:
    def __init__(self, redis_queue='my_queue', correlation_id="stream_1", mode=3, token_list=None):
        self.redis_queue = redis_queue
        self.redis_client = RedisConnection()
        self.api = AngelBrokingAPI()
        self.websocket = self.api.create_websocket()
        self.correlation_id = correlation_id
        self.mode = mode
        self.token_list = token_list

    def on_data(self, wsapp, message):
        self.redis_client.publish_data(self.redis_queue, message)
        self.redis_client.publish_data(DOWNTREND_STREAMING_QUEUE, message)
        self.redis_client.publish_data(UPTREND_STREAMING_QUEUE, message)
        print(message)
        time.sleep(0.005)

    def on_open(self, wsapp):
        print("WebSocket connection established. Subscribing to data streams...")
        self.websocket.subscribe(self.correlation_id, self.mode, self.token_list)

    def on_error(self, wsapp, error):
        print(f"WebSocket error: {error}")

    def on_close(self, wsapp, close):
        print("WebSocket connection closed.")
        self.websocket.unsubscribe(self.correlation_id, self.mode, self.token_list)
        print("Unsubscribed from data streams.")
        self.websocket.close_connection()
        print("WebSocket connection closed.")

    def unsubscribe_and_close(self):
        print("Unsubscribing from data streams...")
        self.websocket.unsubscribe(self.correlation_id, self.mode, self.token_list)
        print("Unsubscribed from data streams.")
        print("Closing the WebSocket connection...")
        self.websocket.close_connection()
        print("WebSocket connection closed.")

    def wait_for_market_open(self, market_open_hour, market_open_minute):

        market_open_time = f"{market_open_hour:02}:{market_open_minute:02}" 
        print(f"Waiting for the stock market to open at {market_open_time}...")

        while True:
            current_time = time.localtime()
            formatted_time = time.strftime("%H:%M:%S", current_time) 
            print(f"Current time: {formatted_time}", end="\r")
            if (
                (current_time.tm_hour == market_open_hour and current_time.tm_min >= market_open_minute) or
                (current_time.tm_hour > market_open_hour)
            ) and current_time.tm_sec >= 0: 
                print("\nStock market is open now! Starting streaming...")
                break 
            time.sleep(1) 

    def start_streaming(self):

        # Wait until market open.
        self.wait_for_market_open(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)


        self.websocket.on_open = self.on_open
        self.websocket.on_data = self.on_data
        self.websocket.on_error = self.on_error
        self.websocket.close = self.on_close
        con_thread = threading.Thread(target=self.websocket.connect)
        con_thread.start()
        print("WebSocket connection initiated. Waiting for data...")
        # time.sleep(0.1)
        # self.unsubscribe_and_close()

# Usage
redis_queue_name = STREAMING_QUEUE
correlation_id = "stream_1"
mode = 3
token_list = [{"exchangeType": 1, "tokens": INDICES_LIST}]
data_streamer = DataStreamer(redis_queue_name, correlation_id, mode, token_list)
data_streamer.start_streaming()
