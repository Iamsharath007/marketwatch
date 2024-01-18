import upstox_client
import pandas as pd
import pprint

upstock_app = upstox_client.HistoryApi()

instrument_keys = pd.read_csv('instrument_keys.csv')
instrument_keys = instrument_keys[["instrument_key", "name"]]
result = instrument_keys[instrument_keys['name'] == "INDIAN RAIL TOUR CORP LTD"]["instrument_key"].iloc[0]
# print(result)
data = upstock_app.get_historical_candle_data1('NSE_EQ|INE780C01023', 'day', '2024-01-17', '2024-01-01', 'v2')


# print(data)

def extractor(_id, start, end, instrument_keys):
    result = instrument_keys[instrument_keys['name'] == f"{_id}"]["instrument_key"].iloc[0]
    response = upstock_app.get_historical_candle_data1(result, 'day', end, start, 'v2')
    # Check the response status
    if response.status != "success":
        print(f"Error: {response.status_code} - {response.text}")
        return
    datas = response.data.candles
    data_dict = {}
    print(data_dict)
    for data in datas:
        date = data[0].split("T")[0]
        data_dict[date] = date
        data_dict["Open"].append(data[1])
        data_dict["Close"].append(data[4])
        data_dict["Percentage"].append(f"{round(((data[4] - data[1]) / data[1]) * 100, 3)}%")
    return pd.DataFrame(data_dict)


def test_new_format():
    import pandas as pd
    test_dict = {'day 1': {'reliance': {'open': 0, 'close': 0, 'rate': 0},
                           'tata': {'open': 0, 'close': 0, 'rate': 0},
                           'iocl': {'open': 0, 'close': 0, 'rate': 0}
                           },
                 'day 2': {'reliance': {'open': 0, 'close': 0, 'rate': 0},
                           'tata': {'open': 0, 'close': 0, 'rate': 0},
                           'iocl': {'open': 0, 'close': 0, 'rate': 0}
                           },
                 'day 3': {'reliance': {'open': 0, 'close': 0, 'rate': 0},
                           'tata': {'open': 0, 'close': 0, 'rate': 0},
                           'iocl': {'open': 0, 'close': 0, 'rate': 0}
                           },
                 }
    pd.DataFrame(test_dict).to_excel("test.xlsx")

test_new_format()



# Assuming you have already defined the 'extractor' function and 'instrument_keys'
# Extract data for the first DataFrame
df1 = extractor("INDIAN RAIL TOUR CORP LTD", "2024-01-01", "2024-01-17", instrument_keys)

# Extract data for the second DataFrame
df2 = extractor("ZEE ENTERTAINMENT ENT LTD", "2024-01-01", "2024-01-17", instrument_keys)

# Add heading for the first DataFrame
df1_heading = "Indian Rail Tour Corp Ltd"
df1.columns = [f'{df1_heading}_{col}' for col in df1.columns]

# Add heading for the second DataFrame
df2_heading = "Zee Entertainment Ent Ltd"
df2.columns = [f'{df2_heading}_{col}' for col in df2.columns]

# Create a Pandas Excel writer using XlsxWriter as the engine
writer = pd.ExcelWriter('output_file.xlsx', engine='xlsxwriter')

# Get the xlsxwriter workbook and worksheet objects
workbook = writer.book
worksheet = workbook.add_worksheet('Sheet1')

# Write the heading for the first DataFrame and span the columns
worksheet.merge_range(0, 0, 0, df1.shape[1] - 1, df1_heading, workbook.add_format({'bold': True}))

# Write the DataFrame to the Excel file
df1.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1, startcol=0, header=False)

# Write the heading for the second DataFrame and span the columns
worksheet.merge_range(0, df1.shape[1], 0, df1.shape[1] + df2.shape[1] - 1, df2_heading,
                      workbook.add_format({'bold': True}))

# Write the DataFrame to the Excel file
df2.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1, startcol=df1.shape[1], header=False)

# Close the Excel writer to save the changes
writer._save()
