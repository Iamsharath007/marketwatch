from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import upstox_client
import pandas as pd
import uvicorn
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

upstock_app = upstox_client.HistoryApi()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
)

instrument_keys = pd.read_csv('instrument_keys.csv')
instrument_keys = instrument_keys[["instrument_key", "name"]]


def download_file(filename: str):
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        filename=filename)


@app.get('/')
def home_page(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")


@app.get('/data')
def get_data(_id, start, end):
    result = instrument_keys[instrument_keys['name'] == f"{_id}"]["instrument_key"].iloc[0]
    response = upstock_app.get_historical_candle_data1(result, 'day', end, start, 'v2')
    if response.status == "success":
        datas = response.data.candles
        data_dict = {"Date": [], "Open": [], "Close": [], "Percentage": []}
        for data in datas:
            date = data[0].split("T")[0]
            data_dict["Date"].append(date)
            data_dict["Open"].append(data[1])
            data_dict["Close"].append(data[4])
            data_dict["Percentage"].append(f"{round(((data[4] - data[1]) / data[1]) * 100, 3)}%")
        data_df = pd.DataFrame(data_dict)
        data_df.to_excel(f"{_id}.xlsx", index=False)
    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code} - {response.text}")


@app.get("/download")
def download_file(filename: str):
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        filename=filename)


uvicorn.run(app)
