import upstox_client
import pandas as pd
import pprint

app = upstox_client.HistoryApi()
instrument_keys = pd.read_csv('instrument_keys.csv')
instrument_keys = instrument_keys[["instrument_key", "name"]]
result = instrument_keys[instrument_keys['name']=="Zee Entertainment Enterprises Limited"]["instrument_key"].iloc[0]
print(result)
data = app.get_historical_candle_data1('NSE_EQ|INE780C01023', 'day', '2024-01-17', '2024-01-01','v2')
# print(data)