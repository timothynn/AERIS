"""Deterministic airport-operations *simulation*. Not operational guidance."""
from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, atan2, sqrt

AIRPORTS = [
    {"icao":"HKJK", "name":"Jomo Kenyatta International", "city":"Nairobi", "lat":-1.3192, "lon":36.9278},
    {"icao":"HKMO", "name":"Moi International", "city":"Mombasa", "lat":-4.0348, "lon":39.5942},
    {"icao":"HUEN", "name":"Entebbe International", "city":"Entebbe", "lat":0.0424, "lon":32.4435},
    {"icao":"HTDA", "name":"Julius Nyerere International", "city":"Dar es Salaam", "lat":-6.8781, "lon":39.2026},
    {"icao":"HAAB", "name":"Bole International", "city":"Addis Ababa", "lat":8.9779, "lon":38.7993},
    {"icao":"HRYR", "name":"Kigali International", "city":"Kigali", "lat":-1.9686, "lon":30.1395},
    {"icao":"HKLU", "name":"Malindi Airport", "city":"Malindi", "lat":-3.2293, "lon":40.1017},
    {"icao":"HSSK", "name":"Khartoum International", "city":"Khartoum", "lat":15.5895, "lon":32.5532},
]
CODES = {a["icao"]: a for a in AIRPORTS}
FLIGHTS = [
    {"id":"AE-204", "carrier":"Aeris Demo", "origin":"HKJK", "destination":"HKMO", "departure":"07:40", "arrival":"08:50", "aircraft":"E190"},
    {"id":"AE-410", "carrier":"Aeris Demo", "origin":"HKJK", "destination":"HUEN", "departure":"08:10", "arrival":"09:20", "aircraft":"A320"},
    {"id":"AE-326", "carrier":"Aeris Demo", "origin":"HTDA", "destination":"HKJK", "departure":"09:00", "arrival":"10:15", "aircraft":"B737"},
    {"id":"AE-581", "carrier":"Aeris Demo", "origin":"HKJK", "destination":"HAAB", "departure":"10:20", "arrival":"12:10", "aircraft":"A320"},
    {"id":"AE-117", "carrier":"Aeris Demo", "origin":"HRYR", "destination":"HKJK", "departure":"11:30", "arrival":"12:35", "aircraft":"E190"},
    {"id":"AE-760", "carrier":"Aeris Demo", "origin":"HKJK", "destination":"HTDA", "departure":"12:55", "arrival":"14:05", "aircraft":"B737"},
    {"id":"AE-239", "carrier":"Aeris Demo", "origin":"HKMO", "destination":"HKJK", "departure":"15:20", "arrival":"16:30", "aircraft":"E190"},
    {"id":"AE-902", "carrier":"Aeris Demo", "origin":"HKJK", "destination":"HRYR", "departure":"16:30", "arrival":"17:45", "aircraft":"A320"},
]

WEATHER = {
    "HKJK":{"wind_kt":12,"visibility_m":10000,"condition":"Scattered clouds","metar":"HKJK 090600Z 08012KT 9999 SCT030 23/14 Q1021"},
    "HKMO":{"wind_kt":9,"visibility_m":10000,"condition":"Few clouds","metar":"HKMO 090600Z 15009KT 9999 FEW020 29/22 Q1014"},
    "HUEN":{"wind_kt":16,"visibility_m":6000,"condition":"Light showers","metar":"HUEN 090600Z 18016KT 6000 -SHRA BKN025 21/18 Q1018"},
    "HTDA":{"wind_kt":8,"visibility_m":10000,"condition":"Partly cloudy","metar":"HTDA 090600Z 09008KT 9999 SCT025 30/24 Q1013"},
    "HAAB":{"wind_kt":14,"visibility_m":8000,"condition":"Cloudy","metar":"HAAB 090600Z 24014KT 8000 BKN030 17/10 Q1025"},
    "HRYR":{"wind_kt":6,"visibility_m":10000,"condition":"Clear","metar":"HRYR 090600Z 16006KT 9999 FEW025 24/17 Q1020"},
    "HKLU":{"wind_kt":11,"visibility_m":10000,"condition":"Scattered clouds","metar":"HKLU 090600Z 13011KT 9999 SCT030 29/22 Q1015"},
    "HSSK":{"wind_kt":17,"visibility_m":7000,"condition":"Haze","metar":"HSSK 090600Z 21017KT 7000 HZ SCT035 35/19 Q1007"},
}

def distance_km(a, b):
    lat1, lon1, lat2, lon2 = map(radians, [a["lat"],a["lon"],b["lat"],b["lon"]])
    x = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return round(6371 * 2 * atan2(sqrt(x),sqrt(1-x)),1)

def shift_time(clock, minutes):
    h,m=map(int,clock.split(':'))
    total=(h*60+m+minutes)%(24*60)
    return f"{total//60:02d}:{total%60:02d}"

def simulate(flight_id: str, weather_severity: int, congestion: int, runway_capacity: int):
    flight=next((f for f in FLIGHTS if f["id"]==flight_id),None)
    if not flight: raise ValueError("Unknown flight")
    airport=CODES[flight["origin"]]
    destination=CODES[flight["destination"]]
    origin_weather=WEATHER[flight["origin"]]
    weather_delay=round(weather_severity*0.36 + max(0,origin_weather["wind_kt"]-15)*1.7)
    congestion_delay=round(congestion*0.32)
    capacity_delay=round((100-runway_capacity)*0.55)
    delay=weather_delay+congestion_delay+capacity_delay
    risk="ELEVATED" if delay>=60 else "WATCH" if delay>=25 else "NOMINAL"
    effects=[{"name":"Weather exposure","minutes":weather_delay},{"name":"Traffic congestion","minutes":congestion_delay},{"name":"Runway throughput","minutes":capacity_delay}]
    return {
      "flight":flight, "origin":airport,"destination":destination,
      "scenario":{"weather_severity":weather_severity,"congestion":congestion,"runway_capacity":runway_capacity},
      "baseline_departure":flight["departure"],"baseline_arrival":flight["arrival"],
      "projected_departure":shift_time(flight["departure"],delay),
      "projected_arrival":shift_time(flight["arrival"],delay),
      "delay_minutes":delay,"risk":risk,"effects":effects,"distance_km":distance_km(airport,destination),
      "note":"Illustrative scenario model; not a certified aviation forecasting or dispatch tool.",
    }
