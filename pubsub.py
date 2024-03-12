import redis
import json
import time

class RedisConnection:
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.connect()

    def connect(self):
        # self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db)
        while True:
            try:
                self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db)
                break
            except redis.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                time.sleep(3)
                
    def publish_data(self, channel, data):
        data_json = json.dumps(data)
        self.redis_client.publish(channel, data_json)

    def subscribe(self, channel):
        while True:
            try:
                pubsub = self.redis_client.pubsub()
                pubsub.subscribe(channel)
                return pubsub
            except redis.exceptions.ConnectionError:
                print("Connection lost. Reconnecting...")
                self.connect()
                time.sleep(1)  # Wait for a second before attempting to reconnect

    def update_tickers(self, set_name, new_members):

        if len(new_members):
            added_elements = self.redis_client.sadd(set_name, *new_members)
            return added_elements

    def get_tickers(self, key_name):

        new_stored_set = self.redis_client.smembers(key_name)
        my_list = [item.decode('utf-8') for item in new_stored_set]
        return my_list


    def create_tickers(self, set_name, new_members):

        self.redis_client.delete(set_name)

        if len(new_members):
            added_elements = self.redis_client.sadd(set_name, *new_members)
            return added_elements

    def delete_tickers(self, set_name, *tickers):
        if not tickers:
            return
        
        self.redis_client.srem(set_name, *tickers)

# # Usage
# redis_client = RedisConnection()  # Specify your custom host, port, and db

# # Update a Redis set with new members
# set_name = 'my_set'
# new_members = {'member1', 'member2', 'member3', 'member4'}
# added_elements = redis_client.update_tickers(set_name, new_members)

