import math
import numpy as np
from scipy.spatial import cKDTree

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lon1, lat1, lon2, lat2):
    lon1 = math.radians(float(lon1))
    lat1 = math.radians(float(lat1))
    lon2 = math.radians(float(lon2))
    lat2 = math.radians(float(lat2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    a = min(1.0, max(0.0, a))
    return EARTH_RADIUS_M * 2 * math.asin(math.sqrt(a))


def lon_lat_to_xyz(lon, lat):
    lon = math.radians(float(lon))
    lat = math.radians(float(lat))
    return (
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    )


class SpatialIndex:
    def __init__(self, graph):
        self.graph = graph
        self.node_ids = list(graph.nodes)

        xyz = np.array(
            [
                lon_lat_to_xyz(graph.nodes[n]["x"], graph.nodes[n]["y"])
                for n in self.node_ids
            ],
            dtype=float,
        )
        self.tree = cKDTree(xyz)

    def nearest_node(self, lon, lat):
        _, i = self.tree.query(lon_lat_to_xyz(lon, lat), k=1)
        node = self.node_ids[int(i)]
        data = self.graph.nodes[node]
        distance = haversine_m(lon, lat, data["x"], data["y"])
        return node, distance


def get_node_coordinates(graph, node):
    data = graph.nodes[node]
    return float(data["x"]), float(data["y"])
