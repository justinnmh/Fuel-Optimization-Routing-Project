# Maritime Route and Speed Optimisation

A Python research prototype for exploring how route choice, vessel speed and ocean currents affect fuel consumption for harbour craft in Singapore waters.

The project combines custom A* search, geographic spatial indexing and a fitted fuel-consumption model. It compares a shortest-distance route with a fuel-aware route and evaluates operating speeds against a user-defined travel-time limit.

Developed by **Nguyen Minh Hieu** during a research internship at **A*STAR**, with launch boats as the main application.

## Project background

The work began with research into vessel speed, engine behaviour and fuel consumption. Fuel consumption per nautical mile was used to compare transit efficiency, since a lower hourly fuel rate does not necessarily mean a trip uses less fuel.

A speed–fuel relationship was fitted using Excel and incorporated into a Python routing framework. This connected the initial modelling work with route planning, operating-speed selection and model-based fuel comparisons.

## Features

- **Custom distance-based A*** with a Haversine distance heuristic, path reconstruction, runtime measurement and node-expansion tracking.
- **GPS-to-graph matching** using SciPy `cKDTree` indexing on spherical coordinates.
- **Implementation comparison** against NetworkX's built-in A* using the same graph, edge weights and distance heuristic.
- **Synthetic ocean currents** with direction-dependent effects on travel speed and estimated fuel use.
- **Fuel-aware A*** using estimated fuel consumption as the path cost.
- **Operating-speed search** across 29 speeds, from 6 to 20 knots in 0.5-knot increments.
- **Route comparison** at the same selected boat speed and under the same current field.
- **Matplotlib visualisation** of the waterway graph and both routes.

## How it works

1. Load a preprocessed Singapore waterway graph.
2. Add a synthetic current field to the graph nodes.
3. Map the origin and destination coordinates to their nearest graph nodes.
4. Calculate the shortest-distance route using custom A* and compare its distance with NetworkX A*.
5. Find a fuel-minimising route for each candidate boat speed.
6. Keep the candidate results that meet the maximum travel time, then select the one with the lowest estimated fuel consumption.
7. Evaluate the shortest-distance route at the selected boat speed and plot both routes.

Boat speed is held constant through the water along each candidate route. Ground speed varies as the current assists or opposes travel.

## Fuel and current model

The fitted relationship implemented in `astar.py` is:

```text
fuel_per_nm(v) = 0.0028 × v² − 0.0121 × v + 0.0925
```

Here, `v` is boat speed through the water in knots, and `fuel_per_nm` is estimated fuel consumption in litres per nautical mile.

For each edge, the program averages the current vectors at its endpoints and projects the result onto the direction of travel. It then estimates:

```text
fuel_rate_lph = fuel_per_nm(v) × v
ground_speed_knots = v + current_along_edge_knots
travel_time_hours = edge_distance_nm / ground_speed_knots
edge_fuel_litres = fuel_rate_lph × travel_time_hours
```

Traversals with non-positive ground speed are excluded from fuel-aware routing. The current field varies by location and stays fixed during each run.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Runs the routing, speed search, comparison and visualisation |
| `graph_loader.py` | Loads the pickled NetworkX waterway graph |
| `spatial.py` | Provides Haversine distance calculations and nearest-node indexing |
| `astar.py` | Implements distance and fuel-aware A*, route metrics and speed selection |
| `fake_current.py` | Generates the synthetic current field |
| `visualize.py` | Plots the shortest-distance and fuel-aware routes |
| `data/sg_cell_123323_water.pkl` | Required preprocessed waterway graph |

## Setup

Use a Python 3 environment with the following packages:

```bash
python -m pip install networkx numpy scipy matplotlib
```

The commands above list the third-party packages imported by the source files. Dependency versions are not pinned here.

Place the graph file at:

```text
data/sg_cell_123323_water.pkl
```

The loader resolves this path relative to `graph_loader.py`. If the dataset is stored elsewhere, update `GRAPH_PATH` in that file.

The routing code expects a NetworkX `Graph` or `DiGraph` with:

| Attribute | Meaning | Unit |
| --- | --- | --- |
| Node `x` | Longitude | Decimal degrees |
| Node `y` | Latitude | Decimal degrees |
| Edge `weight` | Travel distance | Metres |

The edge-access logic assumes a simple graph rather than a multigraph. The graph must be available locally for the program to run.

## Run

From the directory containing `main.py`, run:

```bash
python main.py
```

Enter a maximum travel time in hours when prompted. For example, `2.0` sets a two-hour limit. Whether a candidate meets that limit depends on the selected endpoints and graph.

### Change the route

The current `get_coordinates()` function in `main.py` uses these example coordinates:

```python
start_lon = 103.5
start_lat = 1.1
end_lon = 103.9
end_lat = 1.3
```

Edit these values to change the route. Alternatively, uncomment the four `input()` lines and remove or comment out the hardcoded assignments to enter coordinates interactively.

Coordinates use **longitude first, latitude second**. The program reports the distance between each requested GPS position and its matched graph node.

### Change the speed range

Edit the constants in `main.py`:

```python
MIN_SPEED = 6.0
MAX_SPEED = 20.0
SPEED_STEP = 0.5
```

Changing the speed range should also account for the range over which the fitted fuel relationship is appropriate.

## Output

The program prints:

- Graph size and endpoint snap distances.
- Shortest route distance and the NetworkX distance-comparison result.
- Selected boat speed, fuel-aware route distance, travel time and estimated fuel use.
- Minimum and maximum ground speed along the selected route.
- Estimated fuel use for both routes at the same selected boat speed.

A Matplotlib window displays both routes on the nearby waterway network. The program reports an error if none of the generated route–speed candidates meets the travel-time limit.

## Documented validation

The internship report records the following result for an earlier shortest-distance routing example:

| Measure | Reported result |
| --- | --- |
| Graph nodes | 206,562 |
| Graph edges | 604,707 |
| Route nodes | 74 |
| Route distance | 43.783 km |
| Nodes expanded by custom A* | 2,505 |
| Comparison with NetworkX A* | Same path and route distance |

These figures describe that documented test, rather than a benchmark for every route or the current fuel-aware extension. The current program checks whether the custom and NetworkX shortest-path distances match. It does not independently validate the physical fuel model.

## Assumptions and limitations

- **Simulated conditions:** Currents are generated for testing and do not represent measured Singapore ocean conditions. Wind, waves, tides over time and vessel interactions are not modelled.
- **Simplified fuel estimates:** Fuel use comes from a fitted speed-based equation. It does not explicitly account for vessel loading, hull condition or changes in propulsion efficiency. Estimated differences are not measured operational fuel savings.
- **Discrete speed selection:** The program evaluates the configured speed grid with one constant boat speed per route. It does not optimise a continuous or segment-by-segment speed profile.
- **Travel-time filtering:** At each speed, the algorithm finds a fuel-minimising route first and checks its travel time afterwards. It can miss another route at that speed that uses more fuel but meets the deadline. It therefore does not guarantee a globally optimal solution to the time-constrained routing problem. A failure to find a candidate also does not prove that no feasible route exists.
- **Graph resolution:** Routes depend on the supplied graph and the nearest-node matching. The off-graph distance from a requested coordinate to its matched node is reported but excluded from route distance, travel time and fuel estimates.
- **Comparison scope:** The shortest-distance baseline is evaluated at the same boat speed, but its travel time is not checked against the deadline in the printed comparison.

The prototype is intended for research and experimentation. Its results have not been validated for operational navigation.

## Possible extensions

- Integrate measured or forecast current data with timestamps.
- Calibrate the fuel model against vessel-specific observations.
- Incorporate travel time directly into constrained route search.
- Evaluate multiple origin–destination pairs and compare runtime, feasibility and estimated fuel use.
- Add automated checks for graph attributes, route costs and model behaviour.
