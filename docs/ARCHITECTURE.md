# AERIS — Architecture and modeling notes

## Runtime

```text
         Browser / operations workspace
              |            |
       selected flight    slider scenarios
              |            |
       GET /api/flights    POST /api/simulate
              |            |
              v            v
         Static flight fixtures --- deterministic disruption model
                                 |                 |
                             explainable       saved simulation
                             delay factors          SQLite
                                 |                 |
                          projected timetable  replay history
```

The frontend runs completely from files served by FastAPI. All demo flight data is fictional. Airport coordinates are included only to draw a broad, schematic projection. The UI never claims flight schedules or disruption predictions are live.

## Delay algorithm

- Weather minutes = `round(severity * 0.36 + max(0, wind_kt - 15) * 1.7)`
- Congestion minutes = `round(congestion * 0.32)`
- Capacity minutes = `round((100 - runway_capacity) * 0.55)`
- Total delay = sum of the above.
- Risk: `NOMINAL` for under 25 minutes, `WATCH` from 25, `ELEVATED` from 60.

These values are arbitrary teaching/demo coefficients, **not estimated from historical operations or certified as an aviation decision support model**. They are intentionally disclosed.

## Weather

`GET /api/weather?icao=HKJK` exposes clearly marked *scenario fixtures*. `GET /api/weather/live?icao=HKJK` attempts a separate HTTPS fetch from NOAA AviationWeather (no API key); if unavailable it returns `503` rather than substituting fictitious values. The model intentionally does not consume or turn METAR observations into operational departure forecasts.

## Production roadmap

1. Add a validated data provider and licensed flight movement source; separate actual data from scenario models.
2. Version scenario coefficients and calibration datasets, and publish evaluation methodology.
3. Incorporate runway configurations, NOTAMs and vetted airport operating constraints only with appropriate domain review.
4. Introduce authentication, audit logs, tenant isolation, telemetry, streaming ingestion, and operational SLOs.
5. Conduct aviation subject-matter and safety reviews before any real-world use.
