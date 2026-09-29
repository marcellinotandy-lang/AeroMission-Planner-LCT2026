from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians
from typing import Iterable

from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.affinity import rotate
from shapely.ops import unary_union

EARTH_RADIUS_M = 6371000.0


@dataclass(frozen=True)
class LocalProjector:
    lon0: float
    lat0: float

    @classmethod
    def from_coords(cls, coords: Iterable[list[float]]) -> "LocalProjector":
        coords = list(coords)
        lon = sum(c[0] for c in coords) / max(1, len(coords))
        lat = sum(c[1] for c in coords) / max(1, len(coords))
        return cls(lon, lat)

    def to_xy(self, coord: list[float] | tuple[float, float]) -> tuple[float, float]:
        lon, lat = float(coord[0]), float(coord[1])
        x = radians(lon - self.lon0) * EARTH_RADIUS_M * cos(radians(self.lat0))
        y = radians(lat - self.lat0) * EARTH_RADIUS_M
        return x, y

    def to_lonlat(self, xy: tuple[float, float]) -> tuple[float, float]:
        x, y = xy
        lon = self.lon0 + x / (EARTH_RADIUS_M * cos(radians(self.lat0))) * 180.0 / 3.141592653589793
        lat = self.lat0 + y / EARTH_RADIUS_M * 180.0 / 3.141592653589793
        return lon, lat


def polygon_from_geojson(area, projector: LocalProjector) -> Polygon:
    exterior = [projector.to_xy(c) for c in area.coordinates[0]]
    holes = [[projector.to_xy(c) for c in ring] for ring in area.coordinates[1:]]
    return Polygon(exterior, holes).buffer(0)


def collect_area_coords(scenario) -> list[list[float]]:
    coords: list[list[float]] = []
    coords.extend(scenario.survey_area.coordinates[0])
    if scenario.allowed_airspace:
        coords.extend(scenario.allowed_airspace.coordinates[0])
    for z in scenario.no_fly_zones:
        coords.extend(z.coordinates[0])
    coords.extend([p.coord for p in scenario.launch_points])
    coords.extend([p.coord for p in scenario.reserve_points])
    return coords


def total_length(points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    return sum(LineString([points[i - 1], points[i]]).length for i in range(1, len(points)))


def normalize_lines(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    if geom.geom_type == "MultiLineString":
        return [g for g in geom.geoms if g.length > 1]
    if geom.geom_type == "GeometryCollection":
        return [g for g in geom.geoms if g.geom_type == "LineString" and g.length > 1]
    return []


def geometry_to_geojson_polygon(poly: Polygon | MultiPolygon, projector: LocalProjector):
    def ring(coords):
        return [[*projector.to_lonlat((x, y))] for x, y in coords]
    if poly.geom_type == "Polygon":
        return {"type": "Polygon", "coordinates": [ring(poly.exterior.coords)] + [ring(r.coords) for r in poly.interiors]}
    return {"type": "MultiPolygon", "coordinates": [[[ring(p.exterior.coords)[i] for i in range(len(ring(p.exterior.coords)))] for p in poly.geoms]]}
