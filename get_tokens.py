import os
import csv

from instruments import InstrumentLookup

from constants import STOCKS_BLOCKED_LIST

def get_first_items_from_csv(directory_path, instrument_lookup, blocked_list):
    first_items_set = set()

    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory_path, filename)
            
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                
                for row in csv_reader:
                    if row:
                        first_item = row[2]
                        if first_item not in blocked_list:
                            token = instrument_lookup.token_lookup(first_item)
                            if token is not None:
                                first_items_set.add(token)
    
    return list(first_items_set)

if __name__ == "__main__":
    instrument_path = "OpenAPIScripMaster.json"
    instrument_lookup = InstrumentLookup(instrument_path)
    
    subdirectory_name = 'indices'
    directory_path = os.path.join(os.getcwd(), subdirectory_name)
    
    first_items = get_first_items_from_csv(directory_path, instrument_lookup, STOCKS_BLOCKED_LIST)
    print(len(first_items))
