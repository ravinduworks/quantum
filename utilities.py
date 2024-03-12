
import time

from constants import MARKET_OPEN_HOUR
from constants import MARKET_OPEN_MINUTE

def convert_last_two_digits_to_float(number):
    if isinstance(number, int):
        return number // 100 + (number % 100) / 100
    else:
        raise ValueError("Input must be an integer.")
    

def wait_for_market_open(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE):

    market_open_time = f"{MARKET_OPEN_HOUR:02}:{MARKET_OPEN_MINUTE:02}" 
    print(f"Waiting for the stock market to open at {market_open_time}...")

    while True:
        current_time = time.localtime()
        formatted_time = time.strftime("%H:%M:%S", current_time) 
        print(f"Current time: {formatted_time}", end="\r")
        if (
            (current_time.tm_hour == MARKET_OPEN_HOUR and current_time.tm_min >= MARKET_OPEN_MINUTE) or
            (current_time.tm_hour > MARKET_OPEN_HOUR)
        ) and current_time.tm_sec >= 0: 
            print("\nStock market is open now! Starting streaming...")
            break  # Exit the loop and start streaming
        time.sleep(1)  # Check every second

def is_sold(order_book, ticker):

    for order in order_book:
        if order['tradingsymbol'] == f'{ticker}-EQ' and order['transactiontype'] == 'SELL' and order['orderstatus'] == 'complete' and order['producttype'] == 'INTRADAY':
            return True

    return False

def is_bought(order_book, ticker):

    for order in order_book:
        if order['tradingsymbol'] == f'{ticker}-EQ' and order['transactiontype'] == 'BUY' and order['orderstatus'] == 'complete' and order['producttype'] == 'INTRADAY':
            return True

    return False