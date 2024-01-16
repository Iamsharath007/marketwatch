from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi.responses import FileResponse
# from nsetools import Nse
import pandas as pd


# def get_stock_name_from_isin(isin_code):
#     nse = Nse()
#
#     try:
#         stock_info = nse.get_quote(isin_code)
#         if stock_info:
#             return stock_info['companyName']
#         else:
#             return "Stock not found"
#     except Exception as e:
#         return f"Error: {str(e)}"


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to the specific domain(s) you want to allow
    allow_credentials=True,
    allow_methods=["*"],  # Set this to the specific HTTP methods you want to allow
    allow_headers=["*"],  # Set this to the specific HTTP headers you want to allow
)


@app.get('/data')
def get_data(_id, start, end):
    url = f"https://api.upstox.com/v2/historical-candle/NSE_EQ%7C{_id}/day/{end}/{start}"
    headers = {
        'Accept': 'application/json'
    }

    response = requests.get(url, headers=headers)

    # Check the response status
    if response.status_code == 200:
        # Do something with the response data (e.g., print it)
        datas = response.json()["data"]["candles"]
        data_dict = {"Date": [], "Open": [], "Close": [], "Percentage": []}
        for data in datas:
            date = data[0].split("T")[0]
            data_dict["Date"].append(date)
            data_dict["Open"].append(data[1])
            data_dict["Close"].append(data[4])
            data_dict["Percentage"].append(f"{round(((data[4] - data[1]) / data[1])*100, 3)}%")
        data_df = pd.DataFrame(data_dict)
        data_df.to_excel("result.xlsx", index=False)

    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code} - {response.text}")

@app.get("/download")
def download_file(filename: str):
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=filename)
