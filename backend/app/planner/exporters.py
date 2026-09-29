from __future__ import annotations

import html
from typing import Any


def to_geojson(plan: dict[str, Any]) -> dict[str, Any]:
    features = []
    for mission in plan.get("missions", []):
        coords = [[p["lon"], p["lat"], p.get("altitude_m", 0)] for p in mission.get("route", [])]
        features.append({
            "type": "Feature",
            "properties": {
                "drone_id": mission["drone_id"],
                "model": mission["model"],
                "airtime_min": mission["airtime_min"],
                "distance_m": mission["distance_m"],
                "strips": mission["assigned_strips"],
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })
        for idx, p in enumerate(mission.get("route", []), 1):
            features.append({
                "type": "Feature",
                "properties": {"drone_id": mission["drone_id"], "order": idx, "action": p.get("action", "waypoint")},
                "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"], p.get("altitude_m", 0)]},
            })
    return {"type": "FeatureCollection", "features": features}


def to_kml(plan: dict[str, Any]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        f'<name>{html.escape(plan.get("scenario_name", "Aero mission"))}</name>',
    ]
    colors = ["ff0053ff", "ff22c55e", "ffffc107", "ff8a83d1", "ff00d1ff", "ffff6b00"]
    for idx, mission in enumerate(plan.get("missions", [])):
        color = colors[idx % len(colors)]
        coords = " ".join(f'{p["lon"]},{p["lat"]},{p.get("altitude_m", 0)}' for p in mission.get("route", []))
        name = html.escape(f'{mission["drone_id"]} {mission["model"]}')
        lines.extend([
            '<Placemark>', f'<name>{name}</name>',
            '<Style><LineStyle><color>%s</color><width>4</width></LineStyle></Style>' % color,
            '<LineString><altitudeMode>relativeToGround</altitudeMode><coordinates>', coords, '</coordinates></LineString>',
            '</Placemark>'
        ])
    lines.extend(['</Document>', '</kml>'])
    return "\n".join(lines)
