import json

class InstrumentLookup:
    def __init__(self, instrument_path):
        self.instrument_data = self.load_instrument_data(instrument_path)

    def load_instrument_data(self, instrument_path):
        try:
            with open(instrument_path, 'r') as file:
                instrument_data = json.load(file)
            return instrument_data
        except FileNotFoundError:
            raise Exception(f"File not found: {instrument_path}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON data in {instrument_path}")

    def token_lookup(self, ticker, exchange="NSE"):
        for instrument in self.instrument_data:
            if (
                instrument["name"] == ticker
                and instrument["exch_seg"] == exchange
                and instrument["symbol"].split('-')[-1] == "EQ"
            ):
                return instrument["token"]

    def symbol_lookup(self, token, exchange="NSE"):
        for instrument in self.instrument_data:
            if (
                instrument["token"] == token
                and instrument["exch_seg"] == exchange
                and instrument["symbol"].split('-')[-1] == "EQ"
            ):
                return instrument["name"]

# Usage
# instrument_path = "OpenAPIScripMaster.json"
# instrument_lookup = InstrumentLookup(instrument_path)

# # Example usage of the methods
# token = instrument_lookup.token_lookup("INDOCO")
# print(token)

# symbol = instrument_lookup.symbol_lookup(token, "NSE")
# print("Symbol for token", token, ":", symbol)
