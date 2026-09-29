from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

Coordinate = list[float]  # [lon, lat]


class Depot(BaseModel):
    id: str
    name: str
    coord: Coordinate
    type: Literal["launch", "reserve"] = "launch"


class Camera(BaseModel):
    id: str = "default"
    name: str = "Default payload"
    fov_m: float | None = None
    gsd_cm: float | None = None


class DroneSpec(BaseModel):
    id: str
    model: str
    count: int = Field(default=1, ge=1)
    speed_mps: float = Field(default=15, gt=0)
    endurance_min: float = Field(default=45, gt=0)
    max_altitude_m: float = Field(default=150, gt=0)
    battery_wh: float = Field(default=500, gt=0)
    payloads: list[str] = Field(default_factory=lambda: ["RGB"])
    camera: Camera | None = None


class AreaGeometry(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[Coordinate]]


class Scenario(BaseModel):
    name: str = "Demo mission"
    survey_type: Literal["RGB", "multispectral", "IR", "LiDAR", "geophysical"] = "RGB"
    optimization: Literal["min_time", "min_airtime", "balanced"] = "balanced"
    wind_speed_mps: float = Field(default=0, ge=0)
    wind_direction_deg: float = Field(default=0, ge=0, le=360)
    max_work_time_min: float | None = None
    max_drones: int | None = None
    launch_points: list[Depot]
    reserve_points: list[Depot] = Field(default_factory=list)
    fleet: list[DroneSpec]
    survey_area: AreaGeometry
    allowed_airspace: AreaGeometry | None = None
    no_fly_zones: list[AreaGeometry] = Field(default_factory=list)


class RoutePoint(BaseModel):
    lon: float
    lat: float
    altitude_m: float
    speed_mps: float
    action: str


class DroneMission(BaseModel):
    drone_id: str
    model: str
    launch_point: str
    landing_point: str
    route: list[RoutePoint]
    stages: list[str]
    distance_m: float
    airtime_min: float
    survey_length_m: float
    assigned_strips: int
    status: Literal["planned", "capacity_warning"] = "planned"


class PlanSummary(BaseModel):
    optimization: str
    feasible: bool
    total_airtime_min: float
    makespan_min: float
    active_drones: int
    survey_area_ha: float
    coverage_strips: int
    warnings: list[str] = Field(default_factory=list)


class PlanResult(BaseModel):
    scenario_name: str
    summary: PlanSummary
    missions: list[DroneMission]
    exports: dict[str, Any] = Field(default_factory=dict)
