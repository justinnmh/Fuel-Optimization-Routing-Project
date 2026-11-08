# Maritime Route and Speed Optimisation

A Python research prototype that compares shortest-distance and fuel-aware routes for harbour craft in Singapore waters, then selects an operating speed from candidates that meet a travel-time limit.

Developed by **Nguyen Minh Hieu** during a research internship at **A*STAR**, with launch boats as the main application.

## Overview

The project investigates how vessel speed and route choice affect trip fuel consumption. I researched vessel and engine behaviour, analysed the relationship between speed and fuel consumption using Excel, and fitted an equation for estimating fuel use. I then integrated the model with a Python routing framework.

The implementation combines:

- **Custom A\* search** for shortest-distance and fuel-aware routing.
- **Geospatial indexing** with SciPy KD-Trees to match GPS coordinates to waterway nodes.
- **Synthetic ocean currents** to explore how travel direction affects ground speed and estimated fuel use.
- **Speed selection** across 29 candidates, from 6 to 20 knots in 0.5-knot increments.
- **Validation and visualisation** through comparison with NetworkX A* and route plots.

## Documented result

An earlier shortest-distance test recorded in the internship report used a graph with **206,562 nodes and 604,707 edges**.

| Measure | Result |
| --- | --- |
| Route distance | 43.783 km |
| Nodes in route | 74 |
| Nodes expanded by custom A* | 2,505 |
| Comparison with NetworkX A* | Same path and distance |

This validates the custom implementation against NetworkX for that example. It is separate from the current fuel-aware extension and does not establish operational fuel savings.

## Quick start

### 1. Download the project

```bash
git clone https://github.com/justinnmh/Fuel-Optimization-Routing-Project.git
cd Fuel-Optimization-Routing-Project
```

### 2. Install dependencies

Use Python 3 with NetworkX, NumPy, SciPy and Matplotlib:

```bash
python -m pip install networkx numpy scipy matplotlib
```

### 3. Run

The waterway graph is stored at `data/sg_cell_123323_water.pkl`.

```bash
python main.py
```

Enter the maximum travel time in hours when prompted. The program reports the selected speed, route distance, travel time and estimated fuel consumption. It also compares both routes at the selected boat speed and opens a route plot.

If no generated candidate meets the deadline, the program reports an error.

### Configuration

Edit `get_coordinates()` in `main.py` to change the default endpoints:

```python
start_lon = 103.5
start_lat = 1.1
end_lon = 103.9
end_lat = 1.3
```

Coordinates use **longitude, latitude**. Interactive coordinate inputs are included in the function but currently commented out.

The speed range is controlled by `MIN_SPEED`, `MAX_SPEED` and `SPEED_STEP` in the same file.

## How the model works

1. Load the waterway graph and add a synthetic current field.
2. Match the origin and destination to their nearest graph nodes.
3. Calculate the shortest-distance route and compare its distance with NetworkX A*.
4. Find a fuel-minimising route at each candidate boat speed.
5. Select the lowest-fuel candidate among those meeting the travel-time limit.

The fitted fuel relationship in `astar.py` estimates litres per nautical mile from boat speed `v` in knots:

```text
fuel_per_nm(v) = 0.0028 × v² − 0.0121 × v + 0.0925
```

The model converts this to an hourly fuel rate. For each edge, it estimates travel time using boat speed plus the current component along the direction of travel, then multiplies travel time by the fuel rate.

## Project files

| File | Purpose |
| --- | --- |
| [main.py](main.py) | Runs the workflow and defines route and speed settings |
| [astar.py](astar.py) | Distance and fuel-aware search, fuel calculations and speed selection |
| [spatial.py](spatial.py) | Geographic distance calculations and nearest-node indexing |
| [graph_loader.py](graph_loader.py) | Loads the NetworkX waterway graph |
| [fake_current.py](fake_current.py) | Generates the synthetic current field |
| [visualize.py](visualize.py) | Plots both routes on the waterway network |
| `data/sg_cell_123323_water.pkl` | Preprocessed waterway graph |

## Scope and limitations

- Currents are synthetic and fixed during each run. Fuel figures are model estimates rather than measured vessel performance.
- Each route uses one constant boat speed through the water. The model searches a discrete speed grid.
- The deadline is checked **after** finding a fuel-minimising route at each speed. The search can miss another route at that speed that meets the deadline, so it does not guarantee the globally optimal time-constrained solution.
- Routes start and end at matched graph nodes. Off-graph travel is excluded, and the shortest-distance comparison route is not separately checked against the deadline.

Future work includes vessel-specific fuel calibration, measured current data and routing that incorporates the time constraint directly.
