import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

from spatial import get_node_coordinates


def plot_routes(graph, distance_path, fuel_path, start_gps, end_gps):
    all_path_nodes = list(dict.fromkeys(distance_path + fuel_path))
    coords = np.array(
        [get_node_coordinates(graph, n) for n in all_path_nodes],
        dtype=float,
    )

    min_lon, min_lat = coords.min(axis=0)
    max_lon, max_lat = coords.max(axis=0)

    lon_pad = max((max_lon - min_lon) * 0.15, 0.02)
    lat_pad = max((max_lat - min_lat) * 0.15, 0.02)

    bounds = (
        min_lon - lon_pad,
        max_lon + lon_pad,
        min_lat - lat_pad,
        max_lat + lat_pad,
    )

    min_lon, max_lon, min_lat, max_lat = bounds

    nearby_nodes = [
        n
        for n, data in graph.nodes(data=True)
        if min_lon <= float(data["x"]) <= max_lon
        and min_lat <= float(data["y"]) <= max_lat
    ]
    nearby_set = set(nearby_nodes)

    segments = []
    for u, v in graph.edges(nearby_nodes):
        if u in nearby_set and v in nearby_set:
            segments.append(
                [get_node_coordinates(graph, u), get_node_coordinates(graph, v)]
            )

    fig, ax = plt.subplots(figsize=(11, 8))

    if segments:
        ax.add_collection(LineCollection(segments, linewidths=0.4, alpha=0.20))

    if nearby_nodes:
        node_xy = np.array(
            [get_node_coordinates(graph, n) for n in nearby_nodes],
            dtype=float,
        )
        ax.scatter(node_xy[:, 0], node_xy[:, 1], s=3, alpha=0.20, label="Water graph")

    distance_xy = np.array(
        [get_node_coordinates(graph, n) for n in distance_path],
        dtype=float,
    )
    fuel_xy = np.array(
        [get_node_coordinates(graph, n) for n in fuel_path],
        dtype=float,
    )

    ax.plot(
        distance_xy[:, 0],
        distance_xy[:, 1],
        linewidth=2.0,
        label="Shortest-distance route",
    )

    ax.plot(
        fuel_xy[:, 0],
        fuel_xy[:, 1],
        linewidth=2.5,
        label="Fuel-optimal route",
    )

    start_node_xy = get_node_coordinates(graph, fuel_path[0])
    end_node_xy = get_node_coordinates(graph, fuel_path[-1])

    ax.scatter(*start_node_xy, s=90, marker="o", label="Start", zorder=5)
    ax.scatter(*end_node_xy, s=90, marker="s", label="End", zorder=5)

    ax.set_xlim(min_lon, max_lon)
    ax.set_ylim(min_lat, max_lat)

    mean_lat = float(np.mean(coords[:, 1]))
    ax.set_aspect(1.0 / max(math.cos(math.radians(mean_lat)), 1e-9))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Distance Route vs Fuel-Aware Route")
    ax.grid(True, alpha=0.20)
    ax.legend()
    fig.tight_layout()
    plt.show()
