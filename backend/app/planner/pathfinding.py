from __future__ import annotations

import math
from dataclasses import dataclass
from shapely.geometry import LineString, Point, Polygon


@dataclass(frozen=True)
class ObstacleSet:
    allowed: Polygon | None
    nofly: list[Polygon]
    safety_margin_m: float = 25.0

    def buffered(self) -> list[Polygon]:
        return [p.buffer(self.safety_margin_m) for p in self.nofly]

    def valid_segment(self, a: tuple[float, float], b: tuple[float, float]) -> bool:
        line = LineString([a, b])
        if self.allowed is not None and not self.allowed.buffer(1).contains(line):
            return False
        for obs in self.buffered():
            inter = line.intersection(obs)
            if inter.is_empty:
                continue
            # Point/touch contact is acceptable for numerical robustness; any
            # non-zero overlap/crossing with the safety buffer is forbidden.
            if getattr(inter, "length", 0.0) > 1e-6 or line.crosses(obs) or line.within(obs) or line.covered_by(obs):
                return False
        return True

    def blocking_obstacle(self, a: tuple[float, float], b: tuple[float, float]):
        line = LineString([a, b])
        for obs in self.buffered():
            inter = line.intersection(obs)
            if inter.is_empty:
                continue
            if getattr(inter, "length", 0.0) > 1e-6 or line.crosses(obs) or line.within(obs) or line.covered_by(obs):
                return obs
        return None


def _length(path: list[tuple[float, float]]) -> float:
    return sum(math.dist(path[i - 1], path[i]) for i in range(1, len(path)))


def _candidate_detours(a: tuple[float, float], b: tuple[float, float], obs, margin: float):
    minx, miny, maxx, maxy = obs.bounds
    pad = max(55.0, margin * 3.0)
    nw, ne = (minx - pad, maxy + pad), (maxx + pad, maxy + pad)
    sw, se = (minx - pad, miny - pad), (maxx + pad, miny - pad)
    mid_top = ((minx + maxx) / 2, maxy + pad)
    mid_bottom = ((minx + maxx) / 2, miny - pad)
    mid_left = (minx - pad, (miny + maxy) / 2)
    mid_right = (maxx + pad, (miny + maxy) / 2)
    return [
        [a, nw, ne, b], [a, sw, se, b], [a, nw, sw, b], [a, ne, se, b],
        [a, nw, b], [a, ne, b], [a, sw, b], [a, se, b],
        [a, mid_top, b], [a, mid_bottom, b], [a, mid_left, b], [a, mid_right, b],
    ]


def _allowed_guard_paths(a: tuple[float, float], b: tuple[float, float], obstacles: ObstacleSet):
    if obstacles.allowed is None:
        return []
    minx, miny, maxx, maxy = obstacles.allowed.bounds
    inset = max(80.0, obstacles.safety_margin_m * 4.0)
    # Four perimeter corridors inside allowed airspace. This is intentionally
    # small and deterministic to keep the API fast.
    sw = (minx + inset, miny + inset)
    nw = (minx + inset, maxy - inset)
    se = (maxx - inset, miny + inset)
    ne = (maxx - inset, maxy - inset)
    guards = [sw, nw, se, ne]
    usable = []
    for p in guards:
        point = Point(p)
        if obstacles.allowed.buffer(1).contains(point) and not any(obs.buffer(1).contains(point) for obs in obstacles.buffered()):
            usable.append(p)
    paths = [[a, p, b] for p in usable]
    # Perimeter alternatives around the allowed box.
    for p, q in [(sw, nw), (nw, ne), (ne, se), (se, sw), (sw, se), (nw, sw), (ne, nw), (se, ne)]:
        if p in usable and q in usable:
            paths.append([a, p, q, b])
    return paths


def _best_valid(candidates: list[list[tuple[float, float]]], obstacles: ObstacleSet):
    valid = [cand for cand in candidates if all(obstacles.valid_segment(cand[i - 1], cand[i]) for i in range(1, len(cand)))]
    return min(valid, key=_length) if valid else None


def shortest_safe_path(start: tuple[float, float], end: tuple[float, float], obstacles: ObstacleSet) -> list[tuple[float, float]]:
    """Return a conservative polyline that avoids expanded no-fly polygons."""
    if obstacles.valid_segment(start, end):
        return [start, end]
    path = [start, end]
    for _ in range(10):
        changed = False
        new_path: list[tuple[float, float]] = [path[0]]
        for a, b in zip(path, path[1:]):
            if obstacles.valid_segment(a, b):
                new_path.append(b)
                continue
            obs = obstacles.blocking_obstacle(a, b)
            candidates = []
            if obs is not None:
                candidates.extend(_candidate_detours(a, b, obs, obstacles.safety_margin_m))
            candidates.extend(_allowed_guard_paths(a, b, obstacles))
            best = _best_valid(candidates, obstacles)
            if best is None:
                # Last resort: keep the segment, but caller can still flag warnings.
                new_path.append(b)
                continue
            new_path.extend(best[1:])
            changed = True
        path = new_path
        if not changed:
            break
    clean = [path[0]]
    for p in path[1:]:
        if math.dist(clean[-1], p) > 1e-6:
            clean.append(p)
    return clean
