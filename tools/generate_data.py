import warnings
from typing import Union, Tuple, List, Callable, Optional, Any
import os
import shutil

import numpy as np
import networkx as nx
import networkx.algorithms.approximation.traveling_salesman as nx_tsp_app
import pickle
import pythonbasictools as pbt
import psutil

try:
    from tools.tester import PerformanceTestCase
except ImportError:
    try:
        from tester import PerformanceTestCase
    except ImportError:
        from .tester import PerformanceTestCase


def greedy_simulated_annealing_tsp(graph, weight, **kwargs):
    return nx_tsp_app.simulated_annealing_tsp(graph, init_cycle="greedy", weight=weight, **kwargs)


def greedy_threshold_accepting_tsp(graph, weight, **kwargs):
    return nx_tsp_app.threshold_accepting_tsp(graph, init_cycle="greedy", weight=weight, **kwargs)


def gen_complete_random_graph(n_nodes: int, seed: int = 0) -> np.ndarray:
    rn_state = np.random.RandomState(seed)
    adj = rn_state.rand(n_nodes, n_nodes)
    adj = adj + adj.T
    adj[np.diag_indices(n_nodes)] = np.inf
    return adj


def gen_geometric_graph(n_nodes: int, seed: int = 0) -> np.ndarray:
    graph = nx.random_geometric_graph(n_nodes, radius=1.0, seed=seed)
    pos = nx.get_node_attributes(graph, "pos")
    for i in range(len(pos)):
        for j in range(i + 1, len(pos)):
            dist = np.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1])
            graph.add_edge(i, j, weight=dist)
    adj = nx.to_numpy_array(graph, nonedge=np.inf)
    return adj


def gen_random_graph(
        n_nodes: int,
        seed: int = 0,
        method: Union[str, Callable[[int, int], np.ndarray]] = "random"
) -> np.ndarray:
    mth_name_to_func = {
        "random": gen_complete_random_graph,
        "geometric": gen_geometric_graph,
    }
    if isinstance(method, str) and method not in mth_name_to_func:
        raise ValueError(f"Unknown method: {method}")
    func = mth_name_to_func[method] if isinstance(method, str) else method
    adj = func(n_nodes, seed)
    return adj


def gen_best_solution(
        adjacency_matrix: np.ndarray,
        methods: Union[str, List[str]] = None
) -> tuple[Optional[list], float, Union[Optional[str], Any]]:
    if methods is None:
        methods = nx_tsp_app.__all__
    if isinstance(methods, str):
        methods = [methods]
    best_cost = np.inf
    best_path = None
    best_method = None
    for method in methods:
        try:
            func = method
            if isinstance(func, str):
                func = getattr(nx_tsp_app, func)
            assert callable(func), f"The method {method} must be callable."
            cycle = nx_tsp_app.traveling_salesman_problem(
                nx.from_numpy_array(adjacency_matrix), weight="weight", method=func
            )
            cost = PerformanceTestCase.get_path_cost(adjacency_matrix, cycle)
            if cost < best_cost:
                best_cost = cost
                best_path = cycle
                best_method = func
        except Exception as e:
            print(f"Method {method} failed with error: {e}.")
    return best_path, best_cost, best_method


def gen_datum(
        n_nodes: int,
        seed: int = 0,
        graph_init_method: Union[str, Callable[[int, int], np.ndarray]] = "random",
        tsp_method: Union[str, List[str], Tuple[str, ...]] = None,
        save_path: Optional[str] = None
):
    """
    Generate one datum of the data. The datum is a dictionary with the following keys:
    - adjacency_matrix: numpy.ndarray The adjacency matrix of the graph.
    - best_path: Union[Tuple, List[int], np.ndarray] The best path found by the Christofides algorithm.
    - path_cost: float The cost of the best path.
    - seed: int The seed used to generate the graph.
    - graph_init_method: str The method used to generate the graph.
    - tsp_method: str The method used to solve the TSP problem.

    :param n_nodes: The number of nodes in the graph.
    :type n_nodes: int
    :param seed: The seed used to generate the graph.
    :type seed: int
    :param graph_init_method: The method used to generate the graph.
    :type graph_init_method: Union[str, Callable[[int, int], np.ndarray]]
    :param tsp_method: The method used to solve the TSP problem.
    :type tsp_method: Union[str, List[str], Tuple[str, ...]]
    :param save_path: The path to save the datum.
    :type save_path: Optional[str]
    :return: dict of the datum
    :rtype: dict
    """
    adjacency_matrix = gen_random_graph(n_nodes, seed, graph_init_method)
    cycle, cost, mth = gen_best_solution(adjacency_matrix, tsp_method)
    datum = dict(
        adjacency_matrix=adjacency_matrix,
        best_path=cycle,
        path_cost=cost,
        seed=seed,
        graph_init_method=graph_init_method,
        tsp_method=(mth.__name__ if callable(mth) else str(mth)),
    )
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(datum, f)
    return datum


def gather_all_data_from_temp_folder(temp_folder: str, save_path: Optional[str] = None) -> List[Any]:
    os.makedirs(temp_folder, exist_ok=True)
    all_data = [
        pickle.load(open(os.path.join(temp_folder, filename), "rb"))
        for filename in os.listdir(temp_folder)
    ]
    if len(all_data) == 0:
        warnings.warn(f"Empty temp folder: {temp_folder}", UserWarning)
        return all_data
    if save_path is not None:
        with open(save_path, "wb") as f:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            pickle.dump(all_data, f)
    return all_data


def gen_dataset(
        n_data: int,
        filepath: str = "./data/data.pkl",
        n_nodes_range: Tuple[int, int] = (2, 10_000),
        gen_methods: Union[str, List[str], Tuple[str, ...]] = ("random", "geometric"),
        tsp_methods: Union[Any, List[Any], Tuple[Any, ...]] = (
            "christofides",
            "greedy_tsp",
            greedy_simulated_annealing_tsp,
            greedy_threshold_accepting_tsp,
        ),
        seed: int = 0,
        **kwargs
):
    if isinstance(gen_methods, str):
        gen_methods = (gen_methods, )
    if isinstance(tsp_methods, str):
        tsp_methods = (tsp_methods, )

    temp_folder = os.path.join(os.path.dirname(filepath), "temp")
    rm_temp_folder = kwargs.get("rm_temp_folder", False)
    if rm_temp_folder and os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    os.makedirs(temp_folder, exist_ok=True)
    temp_start_idx = len(os.listdir(temp_folder))

    rn_state = np.random.RandomState(seed)
    data = pbt.apply_func_multiprocess(
        func=gen_datum,
        iterable_of_args=[
            (
                rn_state.randint(*n_nodes_range),
                i,
                rn_state.choice(gen_methods),
                tsp_methods,
                os.path.join(temp_folder, f"{i+temp_start_idx}.pkl"),
            )
            for i in range(n_data)
        ],
        nb_workers=kwargs.get("nb_workers", max(1, psutil.cpu_count(logical=False) - 2)),
        desc=f"Generating data to {filepath}"
    )
    return gather_all_data_from_temp_folder(temp_folder, filepath)


if __name__ == '__main__':
    gen_dataset(
        n_data=100,
        filepath="../data/data.pkl",
        n_nodes_range=(10, 1_000),
        gen_methods=("random", "geometric"),
        tsp_methods=(
            "christofides",
            "greedy_tsp",
            greedy_simulated_annealing_tsp,
            greedy_threshold_accepting_tsp,
        ),
        seed=0,
        # nb_workers=0,
        rm_temp_folder=False,
    )
