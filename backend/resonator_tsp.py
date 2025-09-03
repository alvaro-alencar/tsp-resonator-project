"""A simple implementation of the SAT Resonator heuristic for the
Travelling Salesman Problem (TSP).

This module provides utilities to parse TSPLIB files, generate an
initial tour using a harmonic resonance heuristic and refine that
tour with a 2‑Opt local search.  The intention is to serve as a
compact, reproducible reference implementation that demonstrates
how a symbolic "resonance" can guide a combinatorial solver without
an exhaustive search.

The core idea is to assign each city a scalar value derived from
a finite harmonic series.  Sorting the cities by this value yields
an initial tour that tends to place nearby cities adjacent in the
route.  A subsequent 2‑Opt optimisation step eliminates obvious
crossings and further reduces the total distance.

Usage example:

    from backend import resonator_tsp as rt

    coords = rt.parse_tsp("berlin52.tsp")
    dist_matrix = rt.compute_distance_matrix(coords)
    route = rt.generate_resonator_route(len(coords), N=9, amplitude=0.003, shift=0.29)
    initial_cost = rt.compute_route_cost(route, dist_matrix)
    improved_route, improved_cost = rt.two_opt(route, dist_matrix, max_iterations=1000)
    print(f"Initial: {initial_cost}, Improved: {improved_cost}")

You can also perform a small grid search over a set of harmonic
parameters and record the results to a CSV file for later analysis:

    results = rt.grid_search(coords,
                             N_values=[7, 8, 9, 10],
                             amplitude_values=[0.003, 0.005],
                             shift_values=[0.25, 0.29],
                             seeds=3,
                             two_opt_iterations=200)
    rt.save_results_csv(results, "berlin52_results.csv")

Notes
-----
* Distances are computed using the EUC_2D metric as defined in
  TSPLIB: the Euclidean distance between points is rounded to the
  nearest integer for each edge.  This allows direct comparison
  with published optimal values for classic instances such as
  ``berlin52``.
* The 2‑Opt implementation here is deliberately simple.  It checks
  every non‑adjacent edge pair and performs the first improving
  swap found in each iteration.  The optional ``max_iterations``
  parameter caps the number of passes to prevent excessive runtime
  on large instances.
* The harmonic parameters ``N`` (number of harmonics), ``amplitude``
  and ``shift`` can be adjusted to explore different resonant
  initialisations.  Higher ``N`` values incorporate finer
  oscillations; ``amplitude`` controls the magnitude of the
  contribution of the harmonics; ``shift`` acts as a phase offset.

This software is released under the MIT licence.
"""

import csv
import math
import random
import time
from typing import List, Tuple, Dict, Any


def parse_tsp(filename: str) -> List[Tuple[float, float]]:
    """Parse a TSPLIB file and return a list of city coordinates.

    Parameters
    ----------
    filename : str
        Path to a TSPLIB file with an optional ``NODE_COORD_SECTION``.

    Returns
    -------
    List[Tuple[float, float]]
        A list of (x, y) coordinates extracted from the file.

    The parser looks for the line ``NODE_COORD_SECTION`` and reads
    subsequent lines as node index and coordinates until it reaches
    ``EOF`` or an empty line.  Only the coordinates are retained.
    """
    coords: List[Tuple[float, float]] = []
    reading = False
    with open(filename, "r") as f:
        for line in f:
            stripped = line.strip()
            # Start reading after the section marker
            if stripped == "NODE_COORD_SECTION":
                reading = True
                continue
            # Stop at EOF or blank line
            if reading:
                if stripped == "" or stripped == "EOF":
                    break
                parts = stripped.split()
                if len(parts) >= 3:
                    # TSPLIB format: index x y
                    try:
                        x = float(parts[1])
                        y = float(parts[2])
                        coords.append((x, y))
                    except ValueError:
                        # Skip malformed lines
                        continue
    return coords


def compute_distance_matrix(coords: List[Tuple[float, float]]) -> List[List[int]]:
    """Compute a symmetric matrix of rounded Euclidean distances.

    The distance between each pair of cities is computed using the
    Euclidean metric and then rounded to the nearest integer, as
    required by the TSPLIB ``EUC_2D`` specification.  Diagonal
    entries are zero.

    Parameters
    ----------
    coords : List[Tuple[float, float]]
        A list of (x, y) coordinates.

    Returns
    -------
    List[List[int]]
        A 2D list where element ``dist[i][j]`` gives the distance
        between city ``i`` and city ``j``.
    """
    n = len(coords)
    dist: List[List[int]] = [[0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = coords[i]
        for j in range(i + 1, n):
            xj, yj = coords[j]
            dij = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
            dist_ij = int(round(dij))
            dist[i][j] = dist_ij
            dist[j][i] = dist_ij
    return dist


def compute_route_cost(route: List[int], dist_matrix: List[List[int]]) -> int:
    """Compute the total cost of a Hamiltonian tour.

    The tour is assumed to be a cycle, so the distance from the last
    city back to the first is included.

    Parameters
    ----------
    route : List[int]
        A permutation of city indices representing the tour.
    dist_matrix : List[List[int]]
        A precomputed distance matrix.

    Returns
    -------
    int
        The sum of distances along the tour.
    """
    total = 0
    n = len(route)
    for idx in range(n):
        total += dist_matrix[route[idx]][route[(idx + 1) % n]]
    return total


def harmonic_values(n: int, N: int, amplitude: float, shift: float) -> List[float]:
    """Compute harmonic values for each position in a list.

    Each position ``i`` in ``0 <= i < n`` is associated with an angle
    ``theta = 2π * ((i + shift) / n)``.  The harmonic value is the
    sum of ``amplitude / k * cos(k * theta)`` for ``k = 1`` to ``N``.

    Parameters
    ----------
    n : int
        Number of positions (e.g., number of cities).
    N : int
        Number of harmonics to include in the sum.  Larger values
        produce finer oscillations.
    amplitude : float
        Scaling factor applied to each harmonic term.
    shift : float
        A phase offset applied to the position index before computing
        the angle.

    Returns
    -------
    List[float]
        A list of harmonic values of length ``n``.
    """
    values: List[float] = []
    for i in range(n):
        theta = 2.0 * math.pi * ((i + shift) / n)
        s = 0.0
        for k in range(1, N + 1):
            s += (amplitude / float(k)) * math.cos(k * theta)
        values.append(s)
    return values


def generate_resonator_route(n: int, N: int = 7, amplitude: float = 1.0, shift: float = 0.0) -> List[int]:
    """Generate an initial TSP tour using the resonance heuristic.

    The route is obtained by computing harmonic values for each
    position (see ``harmonic_values``) and then sorting the indices
    of the cities by these values in ascending order.  The sorted
    indices form a permutation which is returned as the initial tour.

    Parameters
    ----------
    n : int
        Number of cities.
    N : int, optional
        Number of harmonics.  Default is 7.
    amplitude : float, optional
        Harmonic amplitude.  Default is 1.0.
    shift : float, optional
        Phase shift.  Default is 0.0.

    Returns
    -------
    List[int]
        A permutation of ``n`` indices representing the initial tour.
    """
    values = harmonic_values(n, N, amplitude, shift)
    # Sort city indices by the corresponding harmonic value
    sorted_indices = sorted(range(n), key=lambda idx: values[idx])
    return sorted_indices


def two_opt(route: List[int], dist_matrix: List[List[int]], max_iterations: int = 5000) -> Tuple[List[int], int]:
    """Perform a 2-Opt local search (Best Improvement) to improve a TSP tour.

    This implementation scans all possible 2-Opt swaps in each iteration and
    applies the one that yields the largest cost reduction (best improvement).
    The process continues until no improvement is possible or the iteration
    limit is reached.

    Parameters
    ----------
    route : List[int]
        A permutation of city indices representing the current tour.
    dist_matrix : List[List[int]]
        Precomputed distance matrix.
    max_iterations : int, optional
        Maximum number of swap passes to perform. Defaults to 5000.

    Returns
    -------
    Tuple[List[int], int]
        A tuple containing the improved route and its cost.
    """
    n = len(route)
    best_route = route[:]
    best_cost = compute_route_cost(best_route, dist_matrix)
    iteration = 0
    improved = True
    while improved and iteration < max_iterations:
        improved = False
        best_delta = 0
        best_swap = None

        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if j - i == 1:
                    continue
                
                a, b = best_route[i - 1], best_route[i]
                c, d = best_route[j - 1], best_route[j % n]

                current_edges_cost = dist_matrix[a][b] + dist_matrix[c][d]
                proposed_edges_cost = dist_matrix[a][c] + dist_matrix[b][d]
                
                delta = proposed_edges_cost - current_edges_cost
                
                if delta < best_delta:
                    best_delta = delta
                    best_swap = (i, j)
        
        if best_swap:
            i, j = best_swap
            best_route[i:j] = reversed(best_route[i:j])
            best_cost += best_delta
            improved = True
        
        iteration += 1
        
    return best_route, best_cost


def run_trial(coords: List[Tuple[float, float]],
              dist_matrix: List[List[int]],
              N: int,
              amplitude: float,
              shift: float,
              two_opt_iterations: int = 2000) -> Tuple[int, int]:
    """Execute a single resonator trial and return initial and final costs.

    Parameters
    ----------
    coords : List[Tuple[float, float]]
        List of city coordinates (unused here but kept for consistency).
    dist_matrix : List[List[int]]
        Precomputed distance matrix.
    N : int
        Number of harmonics in the resonance.
    amplitude : float
        Harmonic amplitude.
    shift : float
        Phase shift.
    two_opt_iterations : int, optional
        Maximum number of 2‑Opt iterations.  Default is 2000.

    Returns
    -------
    Tuple[int, int]
        A tuple ``(initial_cost, improved_cost)``.
    """
    n = len(coords)
    route = generate_resonator_route(n, N=N, amplitude=amplitude, shift=shift)
    initial_cost = compute_route_cost(route, dist_matrix)
    improved_route, improved_cost = two_opt(route, dist_matrix, max_iterations=two_opt_iterations)
    return initial_cost, improved_cost


def grid_search(coords: List[Tuple[float, float]],
                N_values: List[int],
                amplitude_values: List[float],
                shift_values: List[float],
                seeds: int = 1,
                two_opt_iterations: int = 2000) -> List[Dict[str, Any]]:
    """Perform a parameter sweep and collect results.

    This helper function iterates over all combinations of the given
    ``N_values``, ``amplitude_values`` and ``shift_values`` and, for
    each combination, optionally runs multiple trials with different
    random seeds.  The random seed is applied via ``random.seed``
    before each trial, so that any stochastic components in your
    own extensions (e.g. randomised shift) can be reproducible.

    Parameters
    ----------
    coords : List[Tuple[float, float]]
        City coordinates.
    N_values : List[int]
        List of harmonic counts to test.
    amplitude_values : List[float]
        List of amplitudes to test.
    shift_values : List[float]
        List of phase shifts to test.
    seeds : int, optional
        Number of seeds per parameter combination.  Default is 1.
    two_opt_iterations : int, optional
        Maximum number of 2‑Opt iterations per trial.  Default is 2000.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each containing the parameters and
        results of a single trial.
    """
    dist_matrix = compute_distance_matrix(coords)
    results: List[Dict[str, Any]] = []
    for N in N_values:
        for amplitude in amplitude_values:
            for shift in shift_values:
                for seed in range(seeds):
                    random.seed(seed)
                    start_time = time.perf_counter()
                    initial_cost, improved_cost = run_trial(coords,
                                                            dist_matrix,
                                                            N,
                                                            amplitude,
                                                            shift,
                                                            two_opt_iterations=two_opt_iterations)
                    elapsed = time.perf_counter() - start_time
                    results.append({
                        'N': N,
                        'amplitude': amplitude,
                        'shift': shift,
                        'seed': seed,
                        'initial_cost': initial_cost,
                        'final_cost': improved_cost,
                        'time_seconds': elapsed
                    })
    return results


def save_results_csv(results: List[Dict[str, Any]], filename: str) -> None:
    """Write grid search results to a CSV file.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of result dictionaries as returned by ``grid_search``.
    filename : str
        Path of the CSV file to create.
    """
    if not results:
        return
    keys = list(results[0].keys())
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def main() -> None:
    """Entry point for command‑line execution.

    This function allows the module to be used as a standalone script.
    It accepts a TSPLIB file and optional parameters for the harmonic
    sweep via command‑line arguments.  The results are saved to a CSV
    file in the current directory.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run SAT Resonator sweep on a TSPLIB instance")
    parser.add_argument('tsp_file', help='Path to a TSPLIB instance file')
    parser.add_argument('--output', default='results.csv', help='Output CSV filename (default: results.csv)')
    parser.add_argument('--N', type=int, nargs='+', default=[7, 8, 9, 10], help='List of harmonic counts to test')
    parser.add_argument('--A', type=float, nargs='+', default=[0.003, 0.005], help='List of amplitudes to test')
    parser.add_argument('--shift', type=float, nargs='+', default=[0.25, 0.29], help='List of shifts to test')
    parser.add_argument('--seeds', type=int, default=3, help='Number of seeds per combination (default: 3)')
    parser.add_argument('--two_opt_iter', type=int, default=1000, help='Maximum 2‑Opt iterations (default: 1000)')
    args = parser.parse_args()
    coords = parse_tsp(args.tsp_file)
    results = grid_search(coords,
                          N_values=args.N,
                          amplitude_values=args.A,
                          shift_values=args.shift,
                          seeds=args.seeds,
                          two_opt_iterations=args.two_opt_iter)
    save_results_csv(results, args.output)
    print(f"Saved {len(results)} records to {args.output}")


if __name__ == '__main__':
    main()