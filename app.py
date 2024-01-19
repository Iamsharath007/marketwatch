import asyncio
import io
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import upstox_client
import pandas as pd
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

# Load data once at startup
instrument_keys = pd.read_csv('instrument_keys.csv')[["instrument_key", "name"]]
symbol_names = set(instrument_keys['name'])

templates = Jinja2Templates(directory="templates")

CANDLE_INTERVAL = 'day'
DATA_VERSION = 'v2'

upstock_app = upstox_client.HistoryApi()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")


def get_instrument_key(symbol):
    try:
        return instrument_keys[instrument_keys['name'] == symbol]["instrument_key"].iloc[0]
    except IndexError:
        raise IndexError(f"Instrument key not found for symbol: {symbol}")


async def extract_data(_id, start, end, data_dict):
    result = get_instrument_key(_id)
    response = await upstock_app.get_historical_candle_data1(result, CANDLE_INTERVAL, end, start, DATA_VERSION)

    if response.status != "success":
        print(f"Error: {response.status_code} - {response.text}")
        return

    datas = response.data.candles
    for data in datas:
        date = data[0].split("T")[0]
        data_dict.setdefault((date, 'open'), {}).setdefault(_id, data[1])
        data_dict.setdefault((date, 'close'), {}).setdefault(_id, data[4])
        data_dict.setdefault((date, 'percen'), {}).setdefault(_id,
                                                              f"{round(((data[4] - data[1]) / data[1]) * 100, 3)}%")


@app.get("/data")
async def get_data(companies: str, start: str, end: str):
    data_dict = {}
    companies = companies.split(',')
    try:
        await asyncio.gather(*(extract_data(company, start, end, data_dict) for company in companies))
        data_df = pd.DataFrame.from_dict(data_dict)
        excel_buffer = io.BytesIO()
        data_df.to_excel(excel_buffer)
        excel_buffer.seek(0)

        return Response(
            content=excel_buffer.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=result.xlsx"}
        )
    except IndexError as e:
        raise HTTPException(status_code=404, detail=f"Symbol not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get('/suggest')
async def suggest(query: str):
    if not query:
        return {'suggestions': {}}

    results = {word for word in symbol_names if query.lower() in word.lower()}
    return {'suggestions': results}
