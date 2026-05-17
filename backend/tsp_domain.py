"""TSP domain adapter for the Resonant Intelligence Engine."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from resonant_core import Candidate, ProblemInstance, ResonanceField, ResonantRunResult, VerificationResult, Verifier

Coordinate = Tuple[float, float]
Route = List[int]
DistanceMatrix = List[List[int]]


@dataclass(frozen=True)
class TspEncoding:
    coords: List[Coordinate]
    dist_matrix: DistanceMatrix


class TspEncoder:
    def encode(self, raw_input: Any) -> ProblemInstance[TspEncoding]:
        if isinstance(raw_input, str):
            coords = parse_tsp(raw_input)
            source = raw_input
        else:
            coords = list(raw_input)
            source = "in-memory"
        if len(coords) < 3:
            raise ValueError("A TSP instance needs at least 3 coordinates.")
        return ProblemInstance(
            domain="tsp",
            encoded=TspEncoding(coords=coords, dist_matrix=compute_distance_matrix(coords)),
            metadata={"city_count": len(coords), "source": source},
        )


class HarmonicTspFieldBuilder:
    def __init__(self, harmonics: int = 7, amplitude: float = 1.0, shift: float = 0.0) -> None:
        self.harmonics = harmonics
        self.amplitude = amplitude
        self.shift = shift

    def build(self, problem: ProblemInstance[TspEncoding]) -> ResonanceField[List[float]]:
        n = len(problem.encoded.coords)
        return ResonanceField(
            values=harmonic_values(n, self.harmonics, self.amplitude, self.shift),
            metadata={
                "field_type": "finite_harmonic_series",
                "harmonics": self.harmonics,
                "amplitude": self.amplitude,
                "shift": self.shift,
            },
        )


class HarmonicRouteCollapse:
    def collapse(self, problem: ProblemInstance[TspEncoding], field: ResonanceField[List[float]]) -> List[Candidate[Route]]:
        route = sorted(range(len(problem.encoded.coords)), key=lambda idx: field.values[idx])
        return [
            Candidate(route, {"collapse": "ascending_harmonic_order"}),
            Candidate(list(reversed(route)), {"collapse": "descending_harmonic_order"}),
        ]


class TspRouteVerifier:
    def verify(self, problem: ProblemInstance[TspEncoding], candidate: Candidate[Route]) -> VerificationResult[int]:
        n = len(problem.encoded.coords)
        route = candidate.value
        valid = len(route) == n and set(route) == set(range(n))
        score = compute_route_cost(route, problem.encoded.dist_matrix) if valid else math.inf
        return VerificationResult(score=score, valid=valid, metadata={"metric": "closed_tour_cost"})


class TspIlsRefiner:
    def __init__(self, two_opt_iterations: int = 2000, ils_iterations: int = 50, seed: int = 0) -> None:
        self.two_opt_iterations = two_opt_iterations
        self.ils_iterations = ils_iterations
        self.seed = seed

    def refine(
        self,
        problem: ProblemInstance[TspEncoding],
        candidate: Candidate[Route],
        verifier: Verifier[TspEncoding, Route, int],
    ) -> ResonantRunResult[Route, int]:
        random.seed(self.seed)
        initial_verification = verifier.verify(problem, candidate)
        best_route, best_cost = two_opt(candidate.value, problem.encoded.dist_matrix, self.two_opt_iterations)
        best_candidate = Candidate(best_route, {"refiner": "two_opt_initial_descent"})
        improvements = 0

        for iteration in range(self.ils_iterations):
            perturbed = perturb_route(best_route)
            new_route, new_cost = two_opt(perturbed, problem.encoded.dist_matrix, self.two_opt_iterations)
            if new_cost < best_cost:
                best_route = new_route
                best_cost = new_cost
                best_candidate = Candidate(best_route, {"refiner": "ils", "iteration": iteration})
                improvements += 1

        return ResonantRunResult(
            initial_candidate=candidate,
            initial_verification=initial_verification,
            final_candidate=best_candidate,
            final_verification=verifier.verify(problem, best_candidate),
            trace=[{"stage": "refine", "method": "two_opt_plus_ils", "improvements": improvements, "seed": self.seed}],
        )


def parse_tsp(filename: str) -> List[Coordinate]:
    coords: List[Coordinate] = []
    reading = False
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped == "NODE_COORD_SECTION":
                reading = True
                continue
            if reading:
                if stripped == "" or stripped == "EOF":
                    break
                parts = stripped.split()
                if len(parts) >= 3:
                    coords.append((float(parts[1]), float(parts[2])))
    return coords


def compute_distance_matrix(coords: Sequence[Coordinate]) -> DistanceMatrix:
    n = len(coords)
    dist: DistanceMatrix = [[0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = coords[i]
        for j in range(i + 1, n):
            xj, yj = coords[j]
            value = int(round(math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)))
            dist[i][j] = value
            dist[j][i] = value
    return dist


def compute_route_cost(route: Sequence[int], dist_matrix: DistanceMatrix) -> int:
    return sum(dist_matrix[route[idx]][route[(idx + 1) % len(route)]] for idx in range(len(route)))


def harmonic_values(n: int, harmonics: int, amplitude: float, shift: float) -> List[float]:
    values: List[float] = []
    for i in range(n):
        theta = 2.0 * math.pi * ((i + shift) / n)
        values.append(sum((amplitude / float(k)) * math.cos(k * theta) for k in range(1, harmonics + 1)))
    return values


def two_opt(route: Sequence[int], dist_matrix: DistanceMatrix, max_iterations: int = 5000) -> Tuple[Route, int]:
    n = len(route)
    best_route = list(route)
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
                delta = (dist_matrix[a][c] + dist_matrix[b][d]) - (dist_matrix[a][b] + dist_matrix[c][d])
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


def perturb_route(route: Sequence[int]) -> Route:
    n = len(route)
    positions = sorted(random.randint(0, n - 1) for _ in range(4))
    p1, p2, p3, p4 = positions
    if len(set(positions)) < 4:
        return list(route[n // 2 :]) + list(route[: n // 2])
    return list(route[0:p1]) + list(route[p3:p4]) + list(route[p2:p3]) + list(route[p1:p2]) + list(route[p4:n])


def summarize_tsp_run(result: ResonantRunResult[Route, int]) -> Dict[str, Any]:
    return {
        "initial_cost": result.initial_verification.score,
        "final_cost": result.final_verification.score,
        "improvement": result.initial_verification.score - result.final_verification.score,
        "valid": result.final_verification.valid,
        "route": result.final_candidate.value,
        "trace": [dict(item) for item in result.trace],
    }
