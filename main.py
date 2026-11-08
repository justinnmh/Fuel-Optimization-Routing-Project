import math
import networkx as nx

from graph_loader import load_graph
from spatial import SpatialIndex, get_node_coordinates
from fake_current import add_fake_current
from astar import (
    astar_path,
    networkx_astar_path,
    optimize_fuel_route_and_speed,
    route_fuel_metrics,
)
from visualize import plot_routes


MIN_SPEED = 6.0
MAX_SPEED = 20.0
SPEED_STEP = 0.5


def get_coordinates():
    print("Enter route coordinates")
    # start_lon = float(input("Start longitude: "))
    # start_lat = float(input("Start latitude:  "))
    # end_lon = float(input("End longitude:   "))
    # end_lat = float(input("End latitude:    "))
    start_lon = 103.5
    start_lat = 1.1
    end_lon = 103.9
    end_lat = 1.3
    return start_lon, start_lat, end_lon, end_lat


def main():
    start_lon, start_lat, end_lon, end_lat = get_coordinates()
    max_time_hours = float(input("Maximum travel time (hours): "))

    graph = load_graph()
    add_fake_current(graph)

    print(f"Graph: {graph.number_of_nodes():,} nodes, {graph.number_of_edges():,} edges")

    spatial = SpatialIndex(graph)
    start_node, start_snap = spatial.nearest_node(start_lon, start_lat)
    end_node, end_snap = spatial.nearest_node(end_lon, end_lat)

    print("\nSelected graph nodes")
    print(f"Start node: {start_node}  ({start_snap:.1f} m from requested GPS)")
    print(f"End node:   {end_node}  ({end_snap:.1f} m from requested GPS)")

    print("\nRunning shortest-distance A*...")
    distance_result = astar_path(graph, start_node, end_node)

    nx_path, nx_distance = networkx_astar_path(graph, start_node, end_node)
    same_cost = math.isclose(
        distance_result.distance_m,
        nx_distance,
        rel_tol=1e-9,
        abs_tol=1e-6,
    )

    print(f"Shortest distance: {distance_result.distance_m / 1000:.3f} km")
    print(f"NetworkX validation: {'PASS' if same_cost else 'FAIL'}")

    print("\nOptimising route and boat speed...")
    fuel_result = optimize_fuel_route_and_speed(
        graph,
        start_node,
        end_node,
        max_time_hours=max_time_hours,
        min_speed=MIN_SPEED,
        max_speed=MAX_SPEED,
        speed_step=SPEED_STEP,
    )

    chosen_speed = fuel_result["boat_speed_knots"]

    # Fair comparison: evaluate the ordinary shortest-distance route
    # using the same chosen boat speed and current field.
    shortest_route_at_same_speed = route_fuel_metrics(
        graph,
        distance_result.path,
        chosen_speed,
    )

    print("------")
    print(f"Optimal boat speed: {chosen_speed:.1f} knots")
    print(f"Fuel-optimal route distance: {fuel_result['distance_m'] / 1000:.3f} km")
    print(f"Fuel-optimal travel time: {fuel_result['time_h']:.3f} h")
    print(f"Fuel-optimal estimated fuel: {fuel_result['fuel_l']:.3f} L")
    print(
        f"Ground speed along route: "
        f"{fuel_result['min_ground_speed']:.2f} to "
        f"{fuel_result['max_ground_speed']:.2f} knots"
    )

    print("\nComparison at the same boat speed")
    print(f"Shortest-distance route fuel: {shortest_route_at_same_speed['fuel_l']:.3f} L")
    print(f"Fuel-aware route fuel:        {fuel_result['fuel_l']:.3f} L")

    if fuel_result["path"] == distance_result.path:
        print("Routes are the same")
    else:
        print("Fuel-aware A* selected a different route.")

    plot_routes(
        graph,
        distance_result.path,
        fuel_result["path"],
        (start_lon, start_lat),
        (end_lon, end_lat),
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, nx.NetworkXNoPath) as error:
        print(f"\nError: {error}")
    except KeyboardInterrupt:
        print("\nStopped.")
