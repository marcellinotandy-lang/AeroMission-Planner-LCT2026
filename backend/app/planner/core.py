from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from shapely.geometry import LineString, Point
from shapely.affinity import rotate
from shapely.ops import unary_union

from backend.app.models import Scenario, PlanResult, PlanSummary, DroneMission, RoutePoint
from backend.app.planner.geometry import LocalProjector, collect_area_coords, polygon_from_geojson, normalize_lines, total_length
from backend.app.planner.pathfinding import ObstacleSet, shortest_safe_path

SURVEY_PRESETS = {
    "RGB": {"altitude": 120, "swath": 95, "overlap": 0.72},
    "multispectral": {"altitude": 110, "swath": 75, "overlap": 0.76},
    "IR": {"altitude": 100, "swath": 85, "overlap": 0.70},
    "LiDAR": {"altitude": 80, "swath": 55, "overlap": 0.65},
    "geophysical": {"altitude": 70, "swath": 45, "overlap": 0.60},
}


@dataclass
class StripJob:
    id: int
    a: tuple[float, float]
    b: tuple[float, float]
    survey_length_m: float
    route_length_m: float


@dataclass
class DroneUnit:
    id: str
    model: str
    speed: float
    endurance_min: float
    altitude: float
    launch_name: str
    launch_xy: tuple[float, float]
    landing_name: str
    landing_xy: tuple[float, float]
    jobs: list[StripJob] = field(default_factory=list)
    route_xy: list[tuple[float, float]] = field(default_factory=list)
    survey_length: float = 0.0
    distance: float = 0.0
    active: bool = False

    @property
    def capacity_m(self) -> float:
        # Keep 15% battery reserve.
        return self.speed * self.endurance_min * 60.0 * 0.85


def _wind_adjusted_speed(speed: float, wind_speed: float) -> float:
    # Conservative mission-level penalty: mixed head/tail/cross wind over a lawnmower path.
    return max(3.0, speed - 0.35 * wind_speed)


def _make_strips(area, swath_m: float) -> list[StripJob]:
    def generate(angle: float) -> list[StripJob]:
        work = rotate(area, angle, origin='centroid', use_radians=False)
        minx, miny, maxx, maxy = work.bounds
        jobs = []
        y = miny - swath_m
        idx = 0
        while y <= maxy + swath_m:
            line = LineString([(minx - swath_m * 2, y), (maxx + swath_m * 2, y)])
            clipped = line.intersection(work)
            for seg in normalize_lines(clipped):
                if seg.length < swath_m * 0.35:
                    continue
                seg_back = rotate(seg, -angle, origin=area.centroid, use_radians=False)
                coords = list(seg_back.coords)
                # Alternate direction to reduce turns.
                if idx % 2:
                    coords = list(reversed(coords))
                jobs.append(StripJob(idx, coords[0], coords[-1], seg.length, seg.length))
                idx += 1
            y += swath_m
        return jobs

    candidates = [generate(0), generate(90)]
    return min(candidates, key=lambda js: (len(js), sum(j.survey_length_m for j in js)))


def _nearest_depot(xy: tuple[float, float], depots) -> tuple[str, tuple[float, float]]:
    return min(depots, key=lambda d: math.dist(xy, d[1]))


def _append_path(route: list[tuple[float, float]], path: list[tuple[float, float]]):
    for p in path:
        if not route or math.dist(route[-1], p) > 1e-6:
            route.append(p)


def _route_cost(current, job: StripJob, landing, obstacles: ObstacleSet) -> float:
    return total_length(shortest_safe_path(current, job.a, obstacles)) + job.survey_length_m + math.dist(job.b, landing)


def build_plan(scenario: Scenario) -> PlanResult:
    projector = LocalProjector.from_coords(collect_area_coords(scenario))
    survey = polygon_from_geojson(scenario.survey_area, projector)
    allowed = polygon_from_geojson(scenario.allowed_airspace, projector) if scenario.allowed_airspace else survey.buffer(500)
    nofly = [polygon_from_geojson(z, projector) for z in scenario.no_fly_zones]
    nofly_union = unary_union(nofly).buffer(0) if nofly else None
    work_area = survey.intersection(allowed)
    if nofly_union and not nofly_union.is_empty:
        work_area = work_area.difference(nofly_union)
    work_area = work_area.buffer(0)

    preset = SURVEY_PRESETS[scenario.survey_type]
    swath = float(preset["swath"])
    altitude = min(float(preset["altitude"]), 150.0)
    jobs = _make_strips(work_area, swath)
    warnings: list[str] = []
    if not jobs:
        warnings.append("Зона съемки пуста после применения разрешенного ВП и бесполетных зон.")

    launch_depots = [(d.name or d.id, projector.to_xy(d.coord)) for d in scenario.launch_points]
    reserve_depots = [(d.name or d.id, projector.to_xy(d.coord)) for d in (scenario.reserve_points or scenario.launch_points)]
    obstacles = ObstacleSet(allowed=allowed, nofly=nofly, safety_margin_m=25)

    units: list[DroneUnit] = []
    for spec in scenario.fleet:
        for i in range(spec.count):
            launch_name, launch_xy = launch_depots[i % len(launch_depots)]
            landing_name, landing_xy = _nearest_depot(launch_xy, reserve_depots)
            units.append(DroneUnit(
                id=f"{spec.id}-{i+1}",
                model=spec.model,
                speed=_wind_adjusted_speed(spec.speed_mps, scenario.wind_speed_mps),
                endurance_min=spec.endurance_min,
                altitude=min(altitude, spec.max_altitude_m),
                launch_name=launch_name,
                launch_xy=launch_xy,
                landing_name=landing_name,
                landing_xy=landing_xy,
            ))
    if scenario.max_drones:
        units = units[:scenario.max_drones]
    if not units:
        raise ValueError("Fleet is empty")

    # Long strips first improves makespan balance.
    sorted_jobs = sorted(jobs, key=lambda j: j.survey_length_m, reverse=True)
    cursors = {u.id: u.launch_xy for u in units}
    distances = {u.id: 0.0 for u in units}
    active_penalty_m = {
        "min_time": 0.0,
        "balanced": 4 * 60.0 * sum(u.speed for u in units) / len(units),
        "min_airtime": 12 * 60.0 * sum(u.speed for u in units) / len(units),
    }[scenario.optimization]

    for job in sorted_jobs:
        best = None
        for u in units:
            inc = _route_cost(cursors[u.id], job, u.landing_xy, obstacles)
            projected = distances[u.id] + inc
            feasible_cap = projected <= u.capacity_m * 1.05
            if not feasible_cap and len(units) > 1:
                continue
            if scenario.optimization == "min_time":
                score = projected / u.speed
            elif scenario.optimization == "min_airtime":
                score = inc + (0 if u.active else active_penalty_m)
            else:
                score = 0.65 * (projected / u.speed) + 0.35 * (inc + (0 if u.active else active_penalty_m)) / u.speed
            candidate = (score, u)
            if best is None or candidate[0] < best[0]:
                best = candidate
        if best is None:
            u = min(units, key=lambda x: distances[x.id] / x.speed)
            warnings.append(f"Для полосы {job.id} превышается расчетный запас батареи; полоса назначена ближайшему доступному БВС.")
        else:
            u = best[1]
        u.jobs.append(job)
        u.active = True
        inc_no_return = total_length(shortest_safe_path(cursors[u.id], job.a, obstacles)) + job.survey_length_m
        distances[u.id] += inc_no_return
        cursors[u.id] = job.b

    missions: list[DroneMission] = []
    for u in units:
        if not u.jobs:
            continue
        route: list[tuple[float, float]] = [u.launch_xy]
        current = u.launch_xy
        stages = [f"Старт: {u.launch_name}", "Набор высоты", "Выход в район съемки"]
        ordered = []
        remaining = list(u.jobs)
        while remaining:
            job = min(remaining, key=lambda j: math.dist(current, j.a))
            remaining.remove(job)
            ordered.append(job)
            _append_path(route, shortest_safe_path(current, job.a, obstacles))
            _append_path(route, [job.a, job.b])
            current = job.b
            u.survey_length += job.survey_length_m
        stages.extend([f"Съемочный галс #{j.id}" for j in ordered])
        _append_path(route, shortest_safe_path(current, u.landing_xy, obstacles))
        stages.append(f"Посадка: {u.landing_name}")
        u.route_xy = route
        u.distance = total_length(route)
        status = "planned" if u.distance <= u.capacity_m else "capacity_warning"
        if status == "capacity_warning":
            warnings.append(f"{u.id}: расчетная дальность выше безопасного запаса батареи.")
        route_points = []
        for idx, xy in enumerate(route):
            lon, lat = projector.to_lonlat(xy)
            if idx == 0:
                action = "takeoff"
                alt = 0
            elif idx == len(route) - 1:
                action = "land"
                alt = 0
            else:
                action = "survey" if any(math.dist(xy, j.a) < 1 or math.dist(xy, j.b) < 1 for j in ordered) else "transit"
                alt = u.altitude
            route_points.append(RoutePoint(lon=lon, lat=lat, altitude_m=alt, speed_mps=u.speed, action=action))
        missions.append(DroneMission(
            drone_id=u.id,
            model=u.model,
            launch_point=u.launch_name,
            landing_point=u.landing_name,
            route=route_points,
            stages=stages,
            distance_m=round(u.distance, 1),
            airtime_min=round(u.distance / u.speed / 60.0, 2),
            survey_length_m=round(u.survey_length, 1),
            assigned_strips=len(u.jobs),
            status=status,
        ))

    total_airtime = sum(m.airtime_min for m in missions)
    makespan = max([m.airtime_min for m in missions] or [0])
    feasible = not any(m.status != "planned" for m in missions)
    if scenario.max_work_time_min is not None and makespan > scenario.max_work_time_min:
        feasible = False
        warnings.append(f"Срок {scenario.max_work_time_min:.1f} мин не выполняется: расчетный makespan {makespan:.1f} мин.")
    if not missions:
        feasible = False
        warnings.append("Не сформировано ни одной миссии.")

    summary = PlanSummary(
        optimization=scenario.optimization,
        feasible=feasible,
        total_airtime_min=round(total_airtime, 2),
        makespan_min=round(makespan, 2),
        active_drones=len(missions),
        survey_area_ha=round(work_area.area / 10000.0, 2),
        coverage_strips=len(jobs),
        warnings=warnings,
    )
    return PlanResult(scenario_name=scenario.name, summary=summary, missions=missions, exports={"format": ["GeoJSON", "KML"]})
