from pathlib import Path
import pickle
import networkx as nx

GRAPH_PATH = Path(__file__).resolve().parent / "data" / "sg_cell_123323_water.pkl"


def load_graph(path=GRAPH_PATH):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Graph file not found: {path}")

    with path.open("rb") as f:
        graph = pickle.load(f)

    if not isinstance(graph, nx.Graph):
        raise TypeError("The pickle file is not a NetworkX graph.")

    return graph
