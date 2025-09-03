"""A simple implementation of the SAT Resonator heuristic for the
Travelling Salesman Problem (TSP), enhanced with Iterated Local Search (ILS).

This module provides utilities to parse TSPLIB files, generate an
initial tour using a harmonic resonance heuristic and refine that
tour with a high-quality 2-Opt local search. The ILS framework
is used to escape local optima and find superior solutions.

This software is released under the MIT licence.
"""

import csv
import math
import random
import time
from typing import List, Tuple, Dict, Any


def parse_tsp(filename: str) -> List[Tuple[float, float]]:
    """Parse a TSPLIB file and return a list of city coordinates."""
    coords: List[Tuple[float, float]] = []
    reading = False
    with open(filename, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "NODE_COORD_SECTION":
                reading = True
                continue
            if reading:
                if stripped == "" or stripped == "EOF":
                    break
                parts = stripped.split()
                if len(parts) >= 3:
                    try:
                        x = float(parts[1])
                        y = float(parts[2])
                        coords.append((x, y))
                    except ValueError:
                        continue
    return coords


def compute_distance_matrix(coords: List[Tuple[float, float]]) -> List[List[int]]:
    """Compute a symmetric matrix of rounded Euclidean distances (EUC_2D)."""
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
    """Compute the total cost of a Hamiltonian tour."""
    total = 0
    n = len(route)
    for idx in range(n):
        total += dist_matrix[route[idx]][route[(idx + 1) % n]]
    return total


def harmonic_values(n: int, N: int, amplitude: float, shift: float) -> List[float]:
    """Compute harmonic values for each position in a list."""
    values: List[float] = []
    for i in range(n):
        theta = 2.0 * math.pi * ((i + shift) / n)
        s = 0.0
        for k in range(1, N + 1):
            s += (amplitude / float(k)) * math.cos(k * theta)
        values.append(s)
    return values


def generate_resonator_route(n: int, N: int = 7, amplitude: float = 1.0, shift: float = 0.0) -> List[int]:
    """Generate an initial TSP tour using the resonance heuristic."""
    values = harmonic_values(n, N, amplitude, shift)
    sorted_indices = sorted(range(n), key=lambda idx: values[idx])
    return sorted_indices


def two_opt(route: List[int], dist_matrix: List[List[int]], max_iterations: int = 5000) -> Tuple[List[int], int]:
    """Perform a 2-Opt local search (Best Improvement) to improve a TSP tour."""
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


def perturb_route(route: List[int], strength: int = 4) -> List[int]:
    """Perturb a route using a double-bridge move (4-opt).
    
    This move breaks four edges and reconnects them in a different valid way,
    effectively "kicking" the solution to a new neighborhood.
    """
    n = len(route)
    pos = sorted([random.randint(0, n - 1) for _ in range(4)])
    p1, p2, p3, p4 = pos
    
    return route[0:p1] + route[p3:p4] + route[p2:p3] + route[p1:p2] + route[p4:n]


def run_trial(coords: List[Tuple[float, float]],
              dist_matrix: List[List[int]],
              N: int,
              amplitude: float,
              shift: float,
              two_opt_iterations: int = 2000,
              ils_iterations: int = 50) -> Tuple[int, int]:
    """Execute a single trial with Iterated Local Search (ILS)."""
    n = len(coords)
    
    # 1. Initial Solution
    initial_route = generate_resonator_route(n, N=N, amplitude=amplitude, shift=shift)
    initial_cost = compute_route_cost(initial_route, dist_matrix)

    # 2. Initial Optimization
    current_best_route, current_best_cost = two_opt(initial_route, dist_matrix, max_iterations=two_opt_iterations)
    
    # 3. Iterated Local Search Loop
    for _ in range(ils_iterations):
        # 3a. Perturbation
        perturbed_route = perturb_route(current_best_route)
        
        # 3b. Local Search on perturbed route
        new_route, new_cost = two_opt(perturbed_route, dist_matrix, max_iterations=two_opt_iterations)
        
        # 3c. Acceptance Criterion
        if new_cost < current_best_cost:
            current_best_route = new_route
            current_best_cost = new_cost
            
    return initial_cost, current_best_cost


def grid_search(coords: List[Tuple[float, float]],
                N_values: List[int],
                amplitude_values: List[float],
                shift_values: List[float],
                seeds: int = 1,
                two_opt_iterations: int = 2000,
                ils_iterations: int = 50) -> List[Dict[str, Any]]:
    """Perform a parameter sweep and collect results using ILS."""
    dist_matrix = compute_distance_matrix(coords)
    results: List[Dict[str, Any]] = []
    
    total_runs = len(N_values) * len(amplitude_values) * len(shift_values) * seeds
    run_count = 0

    print(f"Starting grid search with {total_runs} total runs...")

    for N in N_values:
        for amplitude in amplitude_values:
            for shift in shift_values:
                for seed in range(seeds):
                    run_count += 1
                    random.seed(seed)
                    start_time = time.perf_counter()
                    
                    initial_cost, final_cost = run_trial(coords,
                                                         dist_matrix,
                                                         N,
                                                         amplitude,
                                                         shift,
                                                         two_opt_iterations=two_opt_iterations,
                                                         ils_iterations=ils_iterations)
                    
                    elapsed = time.perf_counter() - start_time
                    results.append({
                        'N': N,
                        'amplitude': amplitude,
                        'shift': shift,
                        'seed': seed,
                        'initial_cost': initial_cost,
                        'final_cost': final_cost,
                        'time_seconds': elapsed
                    })
                    print(f"({run_count}/{total_runs}) N={N}, A={amplitude}, s={shift}, seed={seed} -> Final Cost: {final_cost} ({elapsed:.2f}s)")

    return results


def save_results_csv(results: List[Dict[str, Any]], filename: str) -> None:
    """Write grid search results to a CSV file."""
    if not results:
        return
    keys = list(results[0].keys())
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def main() -> None:
    """Entry point for command‑line execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Run SAT Resonator sweep with ILS on a TSPLIB instance")
    parser.add_argument('tsp_file', help='Path to a TSPLIB instance file')
    parser.add_argument('--output', default='results.csv', help='Output CSV filename (default: results.csv)')
    parser.add_argument('--N', type=int, nargs='+', default=[10], help='List of harmonic counts to test')
    parser.add_argument('--A', type=float, nargs='+', default=[0.003], help='List of amplitudes to test')
    parser.add_argument('--shift', type=float, nargs='+', default=[0.33], help='List of shifts to test')
    parser.add_argument('--seeds', type=int, default=5, help='Number of seeds per combination (default: 5)')
    parser.add_argument('--two_opt_iter', type=int, default=1000, help='Maximum 2‑Opt iterations per step (default: 1000)')
    parser.add_argument('--ils_iter', type=int, default=100, help='Number of ILS iterations (perturbations) (default: 100)')
    args = parser.parse_args()
    
    coords = parse_tsp(args.tsp_file)
    results = grid_search(coords,
                          N_values=args.N,
                          amplitude_values=args.A,
                          shift_values=args.shift,
                          seeds=args.seeds,
                          two_opt_iterations=args.two_opt_iter,
                          ils_iterations=args.ils_iter)
                          
    save_results_csv(results, args.output)
    print(f"\nSaved {len(results)} records to {args.output}")

    # Find and print the best result
    if results:
        best_run = min(results, key=lambda x: x['final_cost'])
        print("\n--- Best Result Found ---")
        for key, value in best_run.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")
        gap = ((best_run['final_cost'] - 7542) / 7542) * 100
        print(f"Gap to optimum (7542): {gap:.2f}%")


if __name__ == '__main__':
    main()