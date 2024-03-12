from instruments import InstrumentLookup
from login import AngelBrokingAPI

from retrying import retry
import requests
import SmartApi.smartExceptions

class OrderManagement:
    def __init__(self, instrument_path="OpenAPIScripMaster.json"):
        self.api_client = AngelBrokingAPI().init()
        self.instrument_lookup = InstrumentLookup(instrument_path)

    @retry(wait_fixed=1000, stop_max_attempt_number=5)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def orderbook(self):
        try:
            response = self.api_client.orderBook()
            response = response['data']
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise
        except SmartApi.smartExceptions.DataException as e:
            print(f"Data exception occurred: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def place_sl_limit_order(self, ticker, buy_sell, price, quantity, exchange="NSE"):
        try:
            params = {
                "variety": "STOPLOSS",
                "tradingsymbol": "{}-EQ".format(ticker),
                "symboltoken": self.instrument_lookup.token_lookup(ticker),
                "transactiontype": buy_sell,
                "exchange": exchange,
                "ordertype": "STOPLOSS_LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price - 0.05 if buy_sell == "SELL" else price + 0.05,
                "triggerprice": price,
                "quantity": quantity
            }
            response = self.api_client.placeOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def place_limit_order(self, ticker, buy_sell, price, quantity, exchange="NSE"):
        try:
            params = {
                "variety": "NORMAL",
                "tradingsymbol": "{}-EQ".format(ticker),
                "symboltoken": self.instrument_lookup.token_lookup(ticker),
                "transactiontype": buy_sell,
                "exchange": exchange,
                "ordertype": "LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "quantity": quantity
            }
            response = self.api_client.placeOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise 

    @retry(wait_fixed=1000, stop_max_attempt_number=3)        
    def place_market_order(self,ticker,buy_sell,quantity,exchange="NSE"):
        try:
            params = {
                        "variety":"NORMAL",
                        "tradingsymbol":"{}-EQ".format(ticker),
                        "symboltoken": self.instrument_lookup.token_lookup(ticker),
                        "transactiontype":buy_sell,
                        "exchange":exchange,
                        "ordertype":"MARKET",
                        "producttype":"INTRADAY",
                        "duration":"DAY",
                        "quantity":quantity
                        }

            response = self.api_client.placeOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def modify_limit_order(self, ticker, order_id, price, quantity):
        try:
            params = {
                "variety": "NORMAL",
                "orderid": order_id,
                "ordertype": "LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": price,
                "quantity": quantity,
                "tradingsymbol": "{}-EQ".format(ticker),
                "symboltoken": self.instrument_lookup.token_lookup(ticker),
                "exchange": "NSE"
            }
            response = self.api_client.modifyOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def modify_order_type(self, ticker, order_id, order_type, quantity):
        try:
            params = {
                        "variety":"NORMAL",
                        "orderid":order_id,
                        "ordertype":order_type,
                        "producttype":"INTRADAY",
                        "duration":"DAY",
                        "tradingsymbol":"{}-EQ".format(ticker),
                        "quantity":quantity,
                        "symboltoken":self.instrument_lookup.token_lookup(ticker),
                        "exchange":"NSE"
                        }
            response = self.api_client.modifyOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise
    
    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def modify_stoploss_order(self, ticker, order_id, price, quantity):
        try:
            params = {
                "variety": "STOPLOSS",
                "orderid": order_id,
                "ordertype": "STOPLOSS_LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "triggerprice": price,
                "quantity": quantity,
                "tradingsymbol": "{}-EQ".format(ticker),
                "symboltoken": self.instrument_lookup.token_lookup(ticker),
                "exchange": "NSE"
            }
            response = self.api_client.modifyOrder(params)
            return response
        except requests.exceptions.Timeout as e:
            print(f"Request timed out: {e}")
            raise 

    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def get_open_positions(self):
        open_positions = list()

        try:
            response = self.api_client.orderBook()
            response = response['data']

            if response is not None:
                for position in response:
                    if position['transactiontype'] == 'BUY' and position['orderstatus'] == 'complete':
                        open_positions.append(self.instrument_lookup.symbol_lookup(position['symboltoken']))
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise  # Re-raise the exception to trigger the retry logic

        return open_positions

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def get_open_orders(self):

        open_orders = list()

        try:
            response = self.api_client.orderBook()
            response = response['data']

            if response is not None:
                for position in response:
                    if position['transactiontype'] == 'BUY' and position['orderstatus'] == 'open':
                        open_orders.append(self.instrument_lookup.symbol_lookup(position['symboltoken']))
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise  # Re-raise the exception to trigger the retry logic

        return open_orders

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def get_open_orders_and_positions(self):

        open_orders_and_positions = list()

        try:
            response = self.api_client.orderBook()
            response = response['data']

            if response is not None:
                for position in response:
                    if position['transactiontype'] == 'BUY' and position['orderstatus'] in ['complete', 'open']:
                        open_orders_and_positions.append(self.instrument_lookup.symbol_lookup(position['symboltoken']))
            return open_orders_and_positions
        except SmartApi.smartExceptions.DataException as e:
            raise e 
        
    def get_sell_orders(self):

        open_sell_orders = list()

        response = self.api_client.orderBook()
        response = response['data']

        if response is not None:
            for position in response:
                if position['transactiontype'] == 'SELL' and position['ordertype'] == 'LIMIT':
                    open_sell_orders.append(self.instrument_lookup.symbol_lookup(position['symboltoken']))
        return open_sell_orders

    def get_buy_orders(self):

        open_buy_orders = list()

        response = self.api_client.orderBook()
        response = response['data']

        if response is not None:
            for position in response:
                if position['transactiontype'] == 'BUY' and position['ordertype'] == 'LIMIT':
                    open_buy_orders.append(self.instrument_lookup.symbol_lookup(position['symboltoken']))
        return open_buy_orders
        
    @retry(wait_fixed=1000, stop_max_attempt_number=3)         
    def get_ltp(self, ticker, exchange="NSE"):
        try:    
            params = {
                        "tradingsymbol":"{}-EQ".format(ticker),
                        "symboltoken": self.instrument_lookup.token_lookup(ticker)
                    }
            response = self.api_client.ltpData(exchange, params["tradingsymbol"], params["symboltoken"])
            return response["data"]#["ltp"]
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise 
    
    @retry(wait_fixed=1000, stop_max_attempt_number=3)  # Retries with a fixed wait time of 1 second, up to 3 attempts
    def get_live_data(self, mode, ticker, exchange="NSE"):
        params = {
            "mode": mode,
            "exchangeTokens": {
                exchange: [self.instrument_lookup.token_lookup(ticker)]
            }
        }

        try:
            response = self.api_client.getMarketData(params['mode'], params['exchangeTokens'])
            return response["data"]['fetched'][0]
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise
        except requests.exceptions.ConnectTimeout as e:
            print(f"Request timed out: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def cancel_order(self, variety, order_id):

        try:
            params = {
                    "variety":variety,
                    "orderid":order_id
                    }
            response = self.api_client.cancelOrder(params["orderid"], params["variety"])
            return response
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise

    @retry(wait_fixed=1000, stop_max_attempt_number=3)         
    def get_positions(self):
        try:
            response = self.api_client.position()
            return response["data"]
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise 

    @retry(wait_fixed=1000, stop_max_attempt_number=3)         
    def get_buy_average_price(self, ticker):
        try:
            response = self.get_positions()
            if response is not None:
                for tick in response:
                    if tick['symbolname'] == ticker:
                        return float(tick["buyavgprice"])
            return None
        
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise 

    @retry(wait_fixed=1000, stop_max_attempt_number=3)         
    def get_order_id(self, ticker):
        try:
            order_book = self.api_client.orderBook()
            order_book = order_book['data']

            if order_book is not None:
                for position in order_book:
                    if position['tradingsymbol'] == f"{ticker}-EQ" and position['transactiontype'] == 'SELL' and position['orderstatus'] == 'open':
                        return position['orderid'] 
                      
        except requests.exceptions.ReadTimeout as e:
            print(f"Request timed out: {e}")
            raise 
    @staticmethod
    def calculate_buy_stoploss_price(percentage, price):

        percentage_amount = round(percentage * price, 2)
        return  int(price - percentage_amount)

    @staticmethod
    def calculate_buy_target_price(percentage, price):

        percentage_amount = round(percentage * price, 2)
        return  int(price + percentage_amount)

    @staticmethod
    def calculate_short_target_price(percentage, price):

        percentage_amount = round(percentage * price, 2)
        return  int(price - percentage_amount)

    @staticmethod
    def calculate_short_stoploss_price(percentage, price):

        percentage_amount = round(percentage * price, 2)
        return  int(price + percentage_amount)
    

# order = OrderManagement()
# # print(order.get_target_price(0.02, 100))
# order.place_limit_order('INDOCO', "BUY", 150, 1)

