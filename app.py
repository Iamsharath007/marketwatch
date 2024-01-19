import io
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import upstox_client
import pandas as pd
import uvicorn
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

instrument_keys = pd.read_csv('instrument_keys.csv')
instrument_keys = instrument_keys[["instrument_key", "name"]]
symbol_names = instrument_keys['name']

templates = Jinja2Templates(directory="templates")


def search_suggestions(target):
    try:
        target = target.lower()
        matches = {word for word in symbol_names if target in str(word).lower()}
        return matches
    except:
        return {}


def extractor(_id, start, end, instrument_keys, data_dict):
    result = instrument_keys[instrument_keys['name'] == f"{_id}"]["instrument_key"].iloc[0]
    response = upstock_app.get_historical_candle_data1(result, 'day', end, start, 'v2')
    # Check the response status
    if response.status != "success":
        print(f"Error: {response.status_code} - {response.text}")
        return
    datas = response.data.candles

    print(data_dict)
    for data in datas:
        date = data[0].split("T")[0]

        # Check if the key exists, create it if not
        if (date, 'open') not in data_dict:
            data_dict[(date, 'open')] = {}
        if (date, 'close') not in data_dict:
            data_dict[(date, 'close')] = {}
        if (date, 'percen') not in data_dict:
            data_dict[(date, 'percen')] = {}

        # Assign values to the keys
        data_dict[(date, 'open')][_id] = data[1]
        data_dict[(date, 'close')][_id] = data[4]
        data_dict[(date, 'percen')][_id] = f"{round(((data[4] - data[1]) / data[1]) * 100, 3)}%"

    data_df = pd.DataFrame.from_dict(data_dict)
    data_df.to_excel('output.xlsx')


upstock_app = upstox_client.HistoryApi()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to the specific domain(s) you want to allow
    allow_credentials=True,
    allow_methods=["*"],  # Set this to the specific HTTP methods you want to allow
    allow_headers=["*"],  # Set this to the specific HTTP headers you want to allow
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
    print(companies)
    for company in companies:
        extractor(company, start, end, instrument_keys, data_dict)
    data_df = pd.DataFrame.from_dict(data_dict)
    excel_buffer = io.BytesIO()
    data_df.to_excel(excel_buffer)
    excel_buffer.seek(0)
    return Response(
        content=excel_buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=result.xlsx"}
    )


@app.get('/suggest')
async def suggest(query: str):
    results = search_suggestions(query)
    return {'suggestions': results}


uvicorn.run(app)
