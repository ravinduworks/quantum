import time

from utilities import is_bought
from utilities import is_sold
from utilities import wait_for_market_open

from orders import OrderManagement
from pubsub import RedisConnection

from constants import SHORT_OPEN_POSITIONS_DB
from constants import BUY_OPEN_POSITIONS_DB
from constants import DEFAULT_STOP_LOSS
from constants import SHORT_DEFAULT_STOP_LOSS

from constants import MARKET_OPEN_HOUR
from constants import MARKET_OPEN_MINUTE

order_client = OrderManagement()
redis_client = RedisConnection()

buy_stoploss_tickers = []
short_stoploss_tickers = []



def manage_buy_orders(order_book, ticker):

    if is_sold(order_book, ticker):

        for order in order_book:
            if order['tradingsymbol'] == f'{ticker}-EQ' and order['orderstatus'] in ['open', 'trigger pending']:
                print(f'Canceling {order["transactiontype"]} order for {ticker} as position is already sold.')
                order_client.cancel_order(order['variety'], order['orderid'])

def manage_short_orders(order_book, ticker):

    if is_bought(order_book, ticker):

        for order in order_book:
            if order['tradingsymbol'] == f'{ticker}-EQ' and order['orderstatus'] in ['open', 'trigger pending']:
                print(f'Canceling {order["transactiontype"]} order for {ticker} as position is already executed.')
                order_client.cancel_order(order['variety'], order['orderid'])


def get_buy_price(order_book, ticker):

    if order_book is not None:
        for order in order_book:
            if order['tradingsymbol'] == f'{ticker}-EQ' and order['transactiontype'] == 'BUY' and order['orderstatus'] == 'complete' and order['producttype'] == 'INTRADAY':
                price = order.get('averageprice')
                return price

def manage_buy_stop_loss(order_book, ticker):

    if is_sold(order_book, ticker):
        return
    
    buy_price = get_buy_price(order_book, ticker)

    for order in order_book:
        if order['tradingsymbol'] == f'{ticker}-EQ' and order['ordertype'] == 'STOPLOSS_LIMIT' and order['filledshares'] == '0':
            # print(order)
            if not ticker in buy_stoploss_tickers:
                stoploss_price = order_client.calculate_buy_stoploss_price(DEFAULT_STOP_LOSS, buy_price)
                print(f'Modifying STOP LOSS order for: {ticker}, buy_price:{buy_price}, stoploss_price:{stoploss_price}')
                order_client.modify_stoploss_order(ticker, order['orderid'], stoploss_price, order['quantity'])
                buy_stoploss_tickers.append(ticker)

wait_for_market_open(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)

while True:
    try:
        print('Getting orderbook...')
        order_book = order_client.orderbook()
        time.sleep(1)

        print('Getting buy positions data...')
        buy_open_positions = set(redis_client.get_tickers(BUY_OPEN_POSITIONS_DB))
        # print(buy_open_positions)
        for ticker in buy_open_positions:
            manage_buy_orders(order_book, ticker)
            # manage_buy_stop_loss(order_book, ticker)

        time.sleep(0.02)

        print('Getting short positions data...')
        short_open_positions = set(redis_client.get_tickers(SHORT_OPEN_POSITIONS_DB))
        # print(short_open_positions)
        for ticker in short_open_positions:
            manage_short_orders(order_book, ticker)
            # manage_short_stoploss(order_book, ticker)

        time.sleep(0.02)

        print()
        print('Waiting for the next cycle...')
        time.sleep(1)
        print()
    except Exception as e:
        print(f"Connection Error: {e}")
        time.sleep(5)

# from orders import OrderManagement
# import time

# from constants import DEFAULT_PROFIT_TARGET
# from constants import DEFAULT_STOP_LOSS

# order_client = OrderManagement()

# def is_sold(order_book, ticker):
#     return any(order['tradingsymbol'] == f'{ticker}-EQ' and 
#                order['transactiontype'] == 'SELL' and 
#                order['orderstatus'] == 'complete' and 
#                order['producttype'] == 'INTRADAY' 
#                for order in order_book)

# def cancel_orders(order_book, ticker):
#     if is_sold(order_book, ticker):
#         orders_to_cancel = [order for order in order_book
#                             if order['tradingsymbol'] == f'{ticker}-EQ' and 
#                                order['orderstatus'] in ['open', 'trigger pending']]
#         for order in orders_to_cancel:
#             print(f'Canceling {order["transactiontype"]} order for {ticker} as position is already sold.')
#             order_client.cancel_order(order['variety'], order['orderid'])

# while True:
#     print('Getting orderbook...')
#     order_book = order_client.orderbook() or []  # Use empty list if order_book is None
#     print('Getting open positions data...')
#     open_positions = set(order_client.get_open_positions())
#     print(f"Getting live market data...")
    
#     for ticker in open_positions:
#         print(f"Getting live market data for {ticker}")
#         live_data = order_client.get_live_data("FULL", ticker)
#         ltp = live_data['ltp']
#         upper_circuit = live_data['upperCircuit'] - 0.50
#         lower_circuit = live_data['lowerCircuit'] - 0.50

#         if order_book:
#             for order in order_book:
#                 if order['tradingsymbol'] == f'{ticker}-EQ' and \
#                    order['transactiontype'] == 'BUY' and \
#                    order['orderstatus'] == 'complete' and \
#                    order['producttype'] == 'INTRADAY':
#                     buy_price = order.get('averageprice')
#                     quantity = order['quantity']
#                     cancel_orders(order_book, ticker)
    
#     print()      
#     print('Waiting for the next cycle...')
#     print()
#     time.sleep(0.01)  # Adjust sleep time as needed


