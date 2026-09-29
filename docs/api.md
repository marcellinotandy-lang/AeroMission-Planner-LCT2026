# API Reference

Base URL: `http://localhost:8000`

## GET `/api/health`

Response:

```json
{"status":"ok","service":"AeroMission Planner"}
```

## POST `/api/plan`

Request: `Scenario` JSON. Example is in `examples/demo_scenario.json`.

Response: `PlanResult`:

```json
{
  "scenario_name": "...",
  "summary": {
    "optimization": "balanced",
    "feasible": true,
    "total_airtime_min": 123.4,
    "makespan_min": 45.2,
    "active_drones": 3,
    "survey_area_ha": 210.0,
    "coverage_strips": 18,
    "warnings": []
  },
  "missions": []
}
```

## POST `/api/export/geojson`

Request: result returned by `/api/plan`.

Response: GeoJSON FeatureCollection.

## POST `/api/export/kml`

Request: result returned by `/api/plan`.

Response: KML file text.
