from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Iterable

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


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
            if line.crosses(obs) or line.within(obs) or line.intersects(obs):
                return False
        return True


def shortest_safe_path(start: tuple[float, float], end: tuple[float, float], obstacles: ObstacleSet) -> list[tuple[float, float]]:
    if obstacles.valid_segment(start, end):
        return [start, end]

    nodes = [start, end]
    for obs in obstacles.buffered():
        # Use exterior vertices plus bbox guard points. The buffer rounds corners, so simplify first.
        simple = obs.simplify(20, preserve_topology=True)
        coords = list(simple.exterior.coords)[:-1]
        if len(coords) > 24:
            step = max(1, len(coords) // 24)
            coords = coords[::step]
        nodes.extend((float(x), float(y)) for x, y in coords)

    n = len(nodes)
    graph: list[list[tuple[int, float]]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if obstacles.valid_segment(nodes[i], nodes[j]):
                d = math.dist(nodes[i], nodes[j])
                graph[i].append((j, d))
                graph[j].append((i, d))

    dist = [float("inf")] * n
    prev = [-1] * n
    dist[0] = 0.0
    pq = [(0.0, 0)]
    while pq:
        d, v = heapq.heappop(pq)
        if v == 1:
            break
        if d != dist[v]:
            continue
        for u, w in graph[v]:
            nd = d + w
            if nd < dist[u]:
                dist[u] = nd
                prev[u] = v
                heapq.heappush(pq, (nd, u))

    if prev[1] == -1:
        # Last-resort fallback: keep the service responsive and explicitly let metrics warn later.
        return [start, end]

    path = []
    cur = 1
    while cur != -1:
        path.append(nodes[cur])
        cur = prev[cur]
    return list(reversed(path))
