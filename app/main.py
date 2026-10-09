from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .domain import AIRPORTS, CODES, FLIGHTS, WEATHER, simulate
WEB = Path(__file__).resolve().parent.parent / "web"

class ScenarioIn(BaseModel):
    flight_id: str = Field(default="AE-204",min_length=1,max_length=20)
    weather_severity: int = Field(default=25,ge=0,le=100)
    congestion: int = Field(default=30,ge=0,le=100)
    runway_capacity: int = Field(default=90,ge=10,le=100)
    save: bool = False

def create_app(db_path: str|None=None) -> FastAPI:
    app=FastAPI(title="AERIS — Aviation Operations Intelligence",version="1.0.0",description="Scenario simulation and illustrative airport intelligence. Not for flight operations.")
    path = db_path or str(Path(os.environ.get("DATA_DIR","."))/"aeris.db")
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    def connect():
        cx=sqlite3.connect(path,timeout=10)
        cx.row_factory=sqlite3.Row
        return cx
    with connect() as cx:
        cx.execute("CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, flight_id TEXT NOT NULL, params TEXT NOT NULL, result TEXT NOT NULL)")
    @app.get("/health")
    def health(): return {"ok":True,"service":"aeris"}
    @app.get("/api/airports")
    def airports(): return {"airports": AIRPORTS,"source":"Curated reference coordinates for fictional demo flights"}
    @app.get("/api/flights")
    def flights(): return {"flights": FLIGHTS,"source":"SIMULATED","notice":"All flight identifiers and schedules are fictional."}
    @app.get("/api/weather")
    def weather(icao:str=Query(default="HKJK",min_length=4,max_length=4)):
        if icao.upper() not in WEATHER: raise HTTPException(404,"Unsupported airport ICAO")
        return {"icao":icao.upper(),**WEATHER[icao.upper()],"source":"SCENARIO_FIXTURE","notice":"Illustrative METAR-like string; not observed weather."}
    @app.get("/api/weather/live")
    def live_weather(icao:str=Query(default="HKJK",min_length=4,max_length=4)):
        icao=icao.upper()
        if icao not in CODES: raise HTTPException(404,"Unsupported airport ICAO")
        # No silent substitution of fabricated data when live weather is unavailable.
        try:
            request=Request(f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2",headers={"User-Agent":"AerisResearchDemo/1.0 (educational software)"})
            with urlopen(request,timeout=5) as res: data=json.loads(res.read(300_000))
            if not isinstance(data,list) or not data: raise ValueError("No recent report")
            return {"icao":icao,"source":"NOAA_AVIATION_WEATHER","fetched_at":datetime.now(timezone.utc).isoformat(),"observation":data[0]}
        except Exception as exc:
            raise HTTPException(503,"Live weather unavailable; scenario fixtures remain accessible separately.") from exc
    @app.post("/api/simulate")
    def evaluate(req:ScenarioIn):
        try: result=simulate(req.flight_id,req.weather_severity,req.congestion,req.runway_capacity)
        except ValueError as exc: raise HTTPException(404,str(exc)) from exc
        if req.save:
            with connect() as cx:
                cursor=cx.execute("INSERT INTO scenarios(created_at,flight_id,params,result) VALUES(?,?,?,?)",(datetime.now(timezone.utc).isoformat(),req.flight_id,json.dumps(req.model_dump()),json.dumps(result)))
                result["saved_scenario_id"]=cursor.lastrowid
        return result
    @app.get("/api/scenarios")
    def history():
        with connect() as cx:
            rows=cx.execute("SELECT id,created_at,flight_id,result FROM scenarios ORDER BY id DESC LIMIT 30").fetchall()
        return {"scenarios":[{"id":row["id"],"created_at":row["created_at"],"flight_id":row["flight_id"],"result":json.loads(row["result"])} for row in rows]}
    @app.get("/")
    def index(): return FileResponse(WEB/"index.html")
    app.mount("/static",StaticFiles(directory=WEB),name="static")
    return app

app=create_app()
