from utilities import convert_last_two_digits_to_float

from constants import MINIMUM_STOCK_PRICE
from constants import MAXIMUM_STOCK_PRICE

from constants import ENTRY_UPTREND_COUNT
from constants import ENTRY_DOWNTREND_COUNT

from constants import EXIT_UPTREND_COUNT
from constants import EXIT_DOWNTREND_COUNT

ticks_collection = {}
price_analysis = {}
    
def analyse_stock_movement(ticks_data, tokens_list, number_of_top_items):

    global ticks_collection
    global price_analysis

    for _ in ticks_data:
        ticks_collection[ticks_data['token']] = ticks_data

    all_items_present = all(item in ticks_collection for item in tokens_list)

    if all_items_present:
        for key in ticks_collection:

            tick_info = ticks_collection[key]

            try:
                upper_circuit_limit = convert_last_two_digits_to_float(tick_info['upper_circuit_limit'])
                lower_circuit_limit = convert_last_two_digits_to_float(tick_info['lower_circuit_limit'])
                current_price = convert_last_two_digits_to_float(tick_info['last_traded_price'])
                previous_price = convert_last_two_digits_to_float(tick_info['closed_price'])
                                
                if previous_price != 0.0:
                    percentage_change = ((current_price - previous_price) / previous_price) * 100
                else:
                    percentage_change = 0.0

                # if MINIMUM_STOCK_PRICE <= current_price <= MAXIMUM_STOCK_PRICE:
                #     price_analysis[ticks_collection[key]['token']] = {
                #         'upper_circuit_limit': str(upper_circuit_limit),
                #         'lower_circuit_limit': str(lower_circuit_limit),
                #         'last_traded_price': str(current_price),
                #         'closed_price': str(previous_price),
                #         'percentage_change': str(percentage_change),
                #     }

                price_analysis[ticks_collection[key]['token']] = {
                    'upper_circuit_limit': str(upper_circuit_limit),
                    'lower_circuit_limit': str(lower_circuit_limit),
                    'last_traded_price': str(current_price),
                    'closed_price': str(previous_price),
                    'percentage_change': str(percentage_change),
                }
                
            except ValueError as e:
                print(f"Error converting to float: {e}. Current Price: {tick_info['last_traded_price']}. Previous Price: {tick_info['closed_price']}")
                continue

        buy_data_sorted = dict(sorted(price_analysis.items(), key=lambda item: float(item[1]['percentage_change']), reverse=True))
        top_buy_data = dict(list(buy_data_sorted.items())[:number_of_top_items])

        short_data_sorted = dict(sorted(price_analysis.items(), key=lambda item: float(item[1]['percentage_change'])))
        top_short_data = dict(list(short_data_sorted.items())[:number_of_top_items])

        top_trading_data = {
            'top_buy_data': top_buy_data,
            'top_short_data': top_short_data
        }
        return top_trading_data
    

# If buy, we use this class for tracking enter market, if short, we use this class for exiting the stock.
# class StockUpTrendTracker:
class EntryUpTrendTracker:
    def __init__(self):
        self.stock_data = {}
        self.reversal_counts = {}

    def update_stock_data(self, stock_symbol, current_price):
        if stock_symbol not in self.stock_data:
            self.stock_data[stock_symbol] = {
                'last_traded_price': current_price,
                'previous_traded_price': current_price
            }
        else:
            self.stock_data[stock_symbol]['previous_traded_price'] = self.stock_data[stock_symbol]['last_traded_price']
            self.stock_data[stock_symbol]['last_traded_price'] = current_price


    def initialize_reversal_count(self, stock_symbol):
        if stock_symbol not in self.reversal_counts:
            self.reversal_counts[stock_symbol] = {
                'reversal_count': 0,
                'previous_reversal_count': 0,  # Include previous reversal count
                'downward_movement': True,
                'entry_price': None,
                'lowest_price': self.stock_data[stock_symbol]['last_traded_price']
            }

    def reset_entry_conditions(self, stock_symbol):
        if stock_symbol in self.reversal_counts:
            self.reversal_counts[stock_symbol]['reversal_count'] = 0
            self.reversal_counts[stock_symbol]['previous_reversal_count'] = 0
            self.reversal_counts[stock_symbol]['downward_movement'] = True
            self.reversal_counts[stock_symbol]['entry_price'] = None
            self.reversal_counts[stock_symbol]['lowest_price'] = self.stock_data[stock_symbol]['last_traded_price']

    def track_price_movement(self, stock_symbol, current_price):
        reversal_info = self.reversal_counts[stock_symbol]

        if current_price < reversal_info['lowest_price']:
            reversal_info['lowest_price'] = current_price

        previous_price = self.stock_data[stock_symbol]['previous_traded_price']

        if current_price < previous_price and reversal_info['reversal_count'] <= (ENTRY_UPTREND_COUNT - 1):
            self.reset_entry_conditions(stock_symbol)

        if current_price > previous_price:
            if not reversal_info['downward_movement']:
                reversal_info['reversal_count'] += 1
                if reversal_info['reversal_count'] == ENTRY_UPTREND_COUNT:  # Update count
                    reversal_info['entry_price'] = round(current_price - (current_price - reversal_info['lowest_price']) / 2, 2)
            else:
                reversal_info['downward_movement'] = False
                reversal_info['reversal_count'] = 1
                reversal_info['lowest_price'] = current_price

        if reversal_info['reversal_count'] == ENTRY_UPTREND_COUNT and reversal_info['entry_price']:
            self.reset_entry_conditions(stock_symbol)
            reversal_info['previous_reversal_count'] = ENTRY_UPTREND_COUNT
            return True  # Indicates to enter the position
        return False
    
    def is_uptrend(self, stock_symbol, updated_last_traded_price):
            if stock_symbol not in self.stock_data:
                print(f"No data found for stock: {stock_symbol}")
                return False
                        
            self.initialize_reversal_count(stock_symbol)

            return self.track_price_movement(stock_symbol, updated_last_traded_price)


# If buy, we use this class for tracking exit price, if short, we use this class for entering the stock.
# class StockDownTrendTracker:
class EntryDownTrendTracker:
    def __init__(self):
        self.stock_data = {}
        self.reversal_counts = {}

    def update_stock_data(self, stock_symbol, current_price):
        if stock_symbol not in self.stock_data:
            self.stock_data[stock_symbol] = {
                'last_traded_price': current_price,
                'previous_traded_price': current_price
            }
        else:
            self.stock_data[stock_symbol]['previous_traded_price'] = self.stock_data[stock_symbol]['last_traded_price']
            self.stock_data[stock_symbol]['last_traded_price'] = current_price

    def initialize_reversal_count(self, stock_symbol):
        if stock_symbol not in self.reversal_counts:
            self.reversal_counts[stock_symbol] = {
                'reversal_count': 0,
                'previous_reversal_count': 0,
                'upward_movement': True,
                'exit_profit_price': None,
                'highest_price': self.stock_data[stock_symbol]['last_traded_price']
            }

    def reset_exit_conditions(self, stock_symbol):
        if stock_symbol in self.reversal_counts:
            self.reversal_counts[stock_symbol]['reversal_count'] = 0
            self.reversal_counts[stock_symbol]['previous_reversal_count'] = 0
            self.reversal_counts[stock_symbol]['upward_movement'] = True
            self.reversal_counts[stock_symbol]['exit_profit_price'] = None
            self.reversal_counts[stock_symbol]['highest_price'] = self.stock_data[stock_symbol]['last_traded_price']

    def track_price_movement(self, stock_symbol, current_price):
           
        reversal_info = self.reversal_counts[stock_symbol]

        if current_price > reversal_info['highest_price']:
            reversal_info['highest_price'] = current_price

        previous_price = self.stock_data[stock_symbol]['previous_traded_price']

        # if current_price > previous_price and 1 <= reversal_info['reversal_count'] <= 1:
        if current_price > previous_price and reversal_info['reversal_count'] <= (ENTRY_DOWNTREND_COUNT - 1):
            self.reset_exit_conditions(stock_symbol)

        if current_price < previous_price:
            if not reversal_info['upward_movement']:
                reversal_info['reversal_count'] += 1
                if reversal_info['reversal_count'] == ENTRY_DOWNTREND_COUNT: # update count
                    reversal_info['exit_profit_price'] = round(current_price + (reversal_info['highest_price'] - current_price) / 2, 2)

            else:
                reversal_info['upward_movement'] = False
                reversal_info['reversal_count'] = 1
                reversal_info['highest_price'] = current_price

        if reversal_info['reversal_count'] == ENTRY_DOWNTREND_COUNT and reversal_info['exit_profit_price']: # update count
            self.reset_exit_conditions(stock_symbol)
            reversal_info['previous_reversal_count'] = ENTRY_DOWNTREND_COUNT

            return True 
        
        return False

    def is_downtrend(self, stock_symbol, updated_last_traded_price):
        if stock_symbol not in self.stock_data:
            print(f"No data found for stock: {stock_symbol}")
            return False
        
        self.initialize_reversal_count(stock_symbol)

        return self.track_price_movement(stock_symbol, updated_last_traded_price)

# Exit Trackers
class ExitUpTrendTracker:
    def __init__(self):
        self.stock_data = {}
        self.reversal_counts = {}

    def update_stock_data(self, stock_symbol, current_price):
        if stock_symbol not in self.stock_data:
            self.stock_data[stock_symbol] = {
                'last_traded_price': current_price,
                'previous_traded_price': current_price
            }
        else:
            self.stock_data[stock_symbol]['previous_traded_price'] = self.stock_data[stock_symbol]['last_traded_price']
            self.stock_data[stock_symbol]['last_traded_price'] = current_price


    def initialize_reversal_count(self, stock_symbol):
        if stock_symbol not in self.reversal_counts:
            self.reversal_counts[stock_symbol] = {
                'reversal_count': 0,
                'previous_reversal_count': 0,  # Include previous reversal count
                'downward_movement': True,
                'entry_price': None,
                'lowest_price': self.stock_data[stock_symbol]['last_traded_price']
            }

    def reset_entry_conditions(self, stock_symbol):
        if stock_symbol in self.reversal_counts:
            self.reversal_counts[stock_symbol]['reversal_count'] = 0
            self.reversal_counts[stock_symbol]['previous_reversal_count'] = 0
            self.reversal_counts[stock_symbol]['downward_movement'] = True
            self.reversal_counts[stock_symbol]['entry_price'] = None
            self.reversal_counts[stock_symbol]['lowest_price'] = self.stock_data[stock_symbol]['last_traded_price']

    def track_price_movement(self, stock_symbol, current_price):
        reversal_info = self.reversal_counts[stock_symbol]

        if current_price < reversal_info['lowest_price']:
            reversal_info['lowest_price'] = current_price

        previous_price = self.stock_data[stock_symbol]['previous_traded_price']

        if current_price < previous_price and reversal_info['reversal_count'] <= (EXIT_UPTREND_COUNT - 1):
            self.reset_entry_conditions(stock_symbol)

        if current_price > previous_price:
            if not reversal_info['downward_movement']:
                reversal_info['reversal_count'] += 1
                if reversal_info['reversal_count'] == EXIT_UPTREND_COUNT:  # Update count
                    reversal_info['entry_price'] = round(current_price - (current_price - reversal_info['lowest_price']) / 2, 2)
            else:
                reversal_info['downward_movement'] = False
                reversal_info['reversal_count'] = 1
                reversal_info['lowest_price'] = current_price

        if reversal_info['reversal_count'] == EXIT_UPTREND_COUNT and reversal_info['entry_price']:
            self.reset_entry_conditions(stock_symbol)
            reversal_info['previous_reversal_count'] = EXIT_UPTREND_COUNT
            return True  # Indicates to enter the position
        return False
    
    # def is_uptrend(self, stock_symbol, updated_last_traded_price, purchase_price=None):
    #         if stock_symbol not in self.stock_data:
    #             print(f"No data found for stock: {stock_symbol}")
    #             return False

    #         if purchase_price is not None:
    #             if updated_last_traded_price >= purchase_price:
    #                 return False
                        
    #         self.initialize_reversal_count(stock_symbol)

    #         return self.track_price_movement(stock_symbol, updated_last_traded_price)

    def is_uptrend(self, stock_symbol, updated_last_traded_price):
            if stock_symbol not in self.stock_data:
                print(f"No data found for stock: {stock_symbol}")
                return False
                        
            self.initialize_reversal_count(stock_symbol)

            return self.track_price_movement(stock_symbol, updated_last_traded_price)
    
class ExitDownTrendTracker:
    def __init__(self):
        self.stock_data = {}
        self.reversal_counts = {}

    def update_stock_data(self, stock_symbol, current_price):
        if stock_symbol not in self.stock_data:
            self.stock_data[stock_symbol] = {
                'last_traded_price': current_price,
                'previous_traded_price': current_price
            }
        else:
            self.stock_data[stock_symbol]['previous_traded_price'] = self.stock_data[stock_symbol]['last_traded_price']
            self.stock_data[stock_symbol]['last_traded_price'] = current_price

    def initialize_reversal_count(self, stock_symbol):
        if stock_symbol not in self.reversal_counts:
            self.reversal_counts[stock_symbol] = {
                'reversal_count': 0,
                'previous_reversal_count': 0,
                'upward_movement': True,
                'exit_profit_price': None,
                'highest_price': self.stock_data[stock_symbol]['last_traded_price']
            }

    def reset_exit_conditions(self, stock_symbol):
        if stock_symbol in self.reversal_counts:
            self.reversal_counts[stock_symbol]['reversal_count'] = 0
            self.reversal_counts[stock_symbol]['previous_reversal_count'] = 0
            self.reversal_counts[stock_symbol]['upward_movement'] = True
            self.reversal_counts[stock_symbol]['exit_profit_price'] = None
            self.reversal_counts[stock_symbol]['highest_price'] = self.stock_data[stock_symbol]['last_traded_price']

    def track_price_movement(self, stock_symbol, current_price):
           
        reversal_info = self.reversal_counts[stock_symbol]

        if current_price > reversal_info['highest_price']:
            reversal_info['highest_price'] = current_price

        previous_price = self.stock_data[stock_symbol]['previous_traded_price']

        # if current_price > previous_price and 1 <= reversal_info['reversal_count'] <= 1:
        if current_price > previous_price and reversal_info['reversal_count'] <= (EXIT_DOWNTREND_COUNT - 1):
            self.reset_exit_conditions(stock_symbol)

        if current_price < previous_price:
            if not reversal_info['upward_movement']:
                reversal_info['reversal_count'] += 1
                if reversal_info['reversal_count'] == EXIT_DOWNTREND_COUNT: # update count
                    reversal_info['exit_profit_price'] = round(current_price + (reversal_info['highest_price'] - current_price) / 2, 2)

            else:
                reversal_info['upward_movement'] = False
                reversal_info['reversal_count'] = 1
                reversal_info['highest_price'] = current_price

        if reversal_info['reversal_count'] == EXIT_DOWNTREND_COUNT and reversal_info['exit_profit_price']: # update count
            self.reset_exit_conditions(stock_symbol)
            reversal_info['previous_reversal_count'] = EXIT_DOWNTREND_COUNT

            return True 
        
        return False

    # def is_downtrend(self, stock_symbol, updated_last_traded_price, purchase_price=None):
    #     if stock_symbol not in self.stock_data:
    #         print(f"No data found for stock: {stock_symbol}")
    #         return False
        
    #     if purchase_price is not None:
    #         if updated_last_traded_price <= purchase_price:
    #             return False

    #     self.initialize_reversal_count(stock_symbol)

    #     return self.track_price_movement(stock_symbol, updated_last_traded_price)

    def is_downtrend(self, stock_symbol, updated_last_traded_price):
        if stock_symbol not in self.stock_data:
            print(f"No data found for stock: {stock_symbol}")
            return False

        self.initialize_reversal_count(stock_symbol)

        return self.track_price_movement(stock_symbol, updated_last_traded_price)