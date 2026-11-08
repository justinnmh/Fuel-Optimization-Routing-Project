import heapq
import math
import time
from dataclasses import dataclass
from itertools import count

import networkx as nx

from spatial import haversine_m


@dataclass
class AStarResult:
    path: list
    distance_m: float
    expanded_nodes: int
    runtime_s: float


def path_distance_m(graph, path):
    return sum(
        float(graph[u][v]["weight"])
        for u, v in zip(path, path[1:])
    )


def reconstruct_path(came_from, node):
    path = [node]
    while node in came_from:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path


def distance_heuristic(graph, node, goal):
    a = graph.nodes[node]
    b = graph.nodes[goal]
    return haversine_m(a["x"], a["y"], b["x"], b["y"])


def astar_path(graph, start, goal):
    """Normal A* using distance in metres as the path cost."""
    start_time = time.perf_counter()

    queue = []
    tie = count()
    g = {start: 0.0}
    came_from = {}

    heapq.heappush(
        queue,
        (distance_heuristic(graph, start, goal), 0.0, next(tie), start),
    )

    expanded = 0

    while queue:
        _, pushed_g, _, current = heapq.heappop(queue)

        if pushed_g != g.get(current):
            continue

        if current == goal:
            path = reconstruct_path(came_from, current)
            return AStarResult(
                path=path,
                distance_m=g[current],
                expanded_nodes=expanded,
                runtime_s=time.perf_counter() - start_time,
            )

        expanded += 1

        for neighbour, edge_data in graph[current].items():
            new_g = g[current] + float(edge_data["weight"])

            if new_g < g.get(neighbour, math.inf):
                g[neighbour] = new_g
                came_from[neighbour] = current
                priority = new_g + distance_heuristic(graph, neighbour, goal)
                heapq.heappush(
                    queue,
                    (priority, new_g, next(tie), neighbour),
                )

    raise nx.NetworkXNoPath("No route found.")


def networkx_astar_path(graph, start, goal):
    """NetworkX A* used only to validate the custom distance A*."""
    path = nx.astar_path(
        graph,
        start,
        goal,
        heuristic=lambda n, g: distance_heuristic(graph, n, g),
        weight="weight",
    )
    return path, path_distance_m(graph, path)


# ------------------------------------------------------------------
# Current + fuel-aware A*
# ------------------------------------------------------------------

def bearing_deg(lon1, lat1, lon2, lat2):
    lon1 = math.radians(float(lon1))
    lat1 = math.radians(float(lat1))
    lon2 = math.radians(float(lon2))
    lat2 = math.radians(float(lat2))

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def edge_current_knots(graph, u, v):
    """Current component along edge u -> v. Positive helps the boat."""
    a = graph.nodes[u]
    b = graph.nodes[v]

    east = (
        a.get("current_east_knots", 0.0)
        + b.get("current_east_knots", 0.0)
    ) / 2

    north = (
        a.get("current_north_knots", 0.0)
        + b.get("current_north_knots", 0.0)
    ) / 2

    bearing = math.radians(
        bearing_deg(a["x"], a["y"], b["x"], b["y"])
    )

    edge_east = math.sin(bearing)
    edge_north = math.cos(bearing)

    return east * edge_east + north * edge_north


def fuel_per_nm(speed_knots):
    """Fitted boat speed -> fuel consumption equation, L/nm."""
    return 0.0028 * speed_knots**2 - 0.0121 * speed_knots + 0.0925


def fuel_rate_lph(speed_knots):
    """Approximate calm-water fuel rate in L/hour."""
    return fuel_per_nm(speed_knots) * speed_knots


def edge_fuel_metrics(graph, u, v, boat_speed_knots):
    """Return fuel, time and ground speed for one directed traversal u -> v."""
    distance_m = float(graph[u][v]["weight"])
    distance_nm = distance_m / 1852.0

    current_along = edge_current_knots(graph, u, v)
    ground_speed = boat_speed_knots + current_along

    if ground_speed <= 0:
        return math.inf, math.inf, ground_speed

    time_h = distance_nm / ground_speed
    fuel_l = fuel_rate_lph(boat_speed_knots) * time_h

    return fuel_l, time_h, ground_speed


def max_current_speed(graph):
    return max(
        float(data.get("current_speed_knots", 0.0))
        for _, data in graph.nodes(data=True)
    )


def fuel_heuristic(graph, node, goal, boat_speed_knots, max_current):
    """Optimistic lower bound on remaining fuel, in litres."""
    a = graph.nodes[node]
    b = graph.nodes[goal]

    straight_nm = haversine_m(
        a["x"], a["y"], b["x"], b["y"]
    ) / 1852.0

    best_possible_ground_speed = boat_speed_knots + max_current

    return (
        fuel_rate_lph(boat_speed_knots)
        * straight_nm
        / best_possible_ground_speed
    )


def route_fuel_metrics(graph, path, boat_speed_knots):
    distance_m = 0.0
    fuel_l = 0.0
    time_h = 0.0
    min_ground_speed = math.inf
    max_ground_speed = -math.inf

    for u, v in zip(path, path[1:]):
        distance_m += float(graph[u][v]["weight"])

        edge_fuel, edge_time, ground_speed = edge_fuel_metrics(
            graph, u, v, boat_speed_knots
        )

        fuel_l += edge_fuel
        time_h += edge_time
        min_ground_speed = min(min_ground_speed, ground_speed)
        max_ground_speed = max(max_ground_speed, ground_speed)

    if len(path) == 1:
        min_ground_speed = boat_speed_knots
        max_ground_speed = boat_speed_knots

    return {
        "distance_m": distance_m,
        "fuel_l": fuel_l,
        "time_h": time_h,
        "min_ground_speed": min_ground_speed,
        "max_ground_speed": max_ground_speed,
    }


def fuel_astar_path(graph, start, goal, boat_speed_knots, max_current=None):
    """A* using estimated fuel in litres as the path cost."""
    if max_current is None:
        max_current = max_current_speed(graph)

    start_time = time.perf_counter()
    queue = []
    tie = count()
    fuel_so_far = {start: 0.0}
    came_from = {}

    start_h = fuel_heuristic(
        graph, start, goal, boat_speed_knots, max_current
    )

    heapq.heappush(queue, (start_h, 0.0, next(tie), start))
    expanded = 0

    while queue:
        _, pushed_fuel, _, current = heapq.heappop(queue)

        if pushed_fuel != fuel_so_far.get(current):
            continue

        if current == goal:
            path = reconstruct_path(came_from, current)
            metrics = route_fuel_metrics(graph, path, boat_speed_knots)
            metrics["path"] = path
            metrics["boat_speed_knots"] = boat_speed_knots
            metrics["expanded_nodes"] = expanded
            metrics["runtime_s"] = time.perf_counter() - start_time
            return metrics

        expanded += 1

        for neighbour in graph.neighbors(current):
            edge_fuel, _, _ = edge_fuel_metrics(
                graph, current, neighbour, boat_speed_knots
            )

            if not math.isfinite(edge_fuel):
                continue

            new_fuel = fuel_so_far[current] + edge_fuel

            if new_fuel < fuel_so_far.get(neighbour, math.inf):
                fuel_so_far[neighbour] = new_fuel
                came_from[neighbour] = current

                priority = new_fuel + fuel_heuristic(
                    graph,
                    neighbour,
                    goal,
                    boat_speed_knots,
                    max_current,
                )

                heapq.heappush(
                    queue,
                    (priority, new_fuel, next(tie), neighbour),
                )

    raise nx.NetworkXNoPath("No fuel-aware route found.")


def optimize_fuel_route_and_speed(
    graph,
    start,
    goal,
    max_time_hours,
    min_speed=6.0,
    max_speed=20.0,
    speed_step=0.5,
):
    """
    Try a range of commanded boat speeds.
    For each speed, A* finds the minimum-fuel route under the synthetic current.
    The best route/speed that satisfies max_time_hours is returned.
    """
    max_current = max_current_speed(graph)
    best = None
    speed = min_speed

    while speed <= max_speed + 1e-9:
        result = fuel_astar_path(
            graph,
            start,
            goal,
            boat_speed_knots=speed,
            max_current=max_current,
        )

        if result["time_h"] <= max_time_hours:
            if best is None or result["fuel_l"] < best["fuel_l"]:
                best = result

        speed = round(speed + speed_step, 10)

    if best is None:
        raise ValueError(
            "No speed in the selected range can complete the trip within the time limit."
        )

    return best
