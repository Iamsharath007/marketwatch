import io
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import upstox_client
import pandas as pd

from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

# Load instrument keys and extract symbol names
instrument_keys = pd.read_csv('instrument_keys.csv')[["instrument_key", "name"]]
symbol_names = instrument_keys['name']

# Create Jinja2 templates instance
templates = Jinja2Templates(directory="templates")

# Create Upstox API instance
upstox_app = upstox_client.HistoryApi()

# FastAPI application
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def search_suggestions(target):
    try:
        target = target.lower()
        matches = {word for word in symbol_names if target in str(word).lower()}
        return matches
    except Exception as e:
        print(f"Error in search_suggestions: {e}")
        return {}


def extractor(_id, start, end, instrument_keys, data_dict):
    try:
        result = instrument_keys.loc[instrument_keys['name'] == f"{_id}", "instrument_key"].iloc[0]
        response = upstox_app.get_historical_candle_data1(result, 'day', end, start, 'v2')

        if response.status != "success":
            raise HTTPException(status_code=500, detail=f"Error in extractor: {response.status_code} - {response.text}")

        datas = response.data.candles

        for data in datas:
            date = data[0].split("T")[0]

            # Check if the key exists, create it if not
            for key in ['open', 'close', 'percen']:
                if (date, key) not in data_dict:
                    data_dict[(date, key)] = {}

            # Assign values to the keys
            data_dict[(date, 'open')][_id] = data[1]
            data_dict[(date, 'close')][_id] = data[4]
            data_dict[(date, 'percen')][_id] = f"{round(((data[4] - data[1]) / data[1]) * 100, 3)}%"

    except Exception as e:
        print(f"Error in extractor for {_id}: {e}")


def get_excel_response(data_df):
    excel_buffer = io.BytesIO()
    data_df.to_excel(excel_buffer)
    excel_buffer.seek(0)
    return Response(
        content=excel_buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=result.xlsx"}
    )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/data")
async def get_data(companies: str, start: str, end: str):
    data_dict = {}
    companies = companies.split(',')

    for company in companies:
        extractor(company, start, end, instrument_keys, data_dict)

    data_df = pd.DataFrame.from_dict(data_dict)
    return get_excel_response(data_df)


@app.get('/suggest')
async def suggest(query: str):
    if not query:
        return {'suggestions': {}}

    results = search_suggestions(query)
    return {'suggestions': results}
