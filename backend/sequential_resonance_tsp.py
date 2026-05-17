"""Pure sequential resonance collapse for TSP.

This module intentionally avoids 2-Opt, ILS, edge swaps or post-processing.
It builds a route once by propagating a resonant decision front through the
geometric field.
"""

from __future__ import annotations

import math
from typing import Dict, List

from resonant_core import Candidate, ProblemInstance, ResonanceField
from tsp_domain import GeometricSignal, TspEncoding

Route = List[int]


class SequentialResonantRouteCollapse:
    """Construct a TSP route through one resonant forward collapse."""

    def __init__(
        self,
        distance_weight: float = 3.786666351072808,
        angular_weight: float = 0.21665604232304894,
        radial_weight: float = 0.4947429668231735,
        density_weight: float = -0.4300906788099721,
        harmonic_weight: float = 0.05463656427707979,
        momentum_weight: float = -0.06817403046939301,
        phase: float = 1.127885708864822,
        radius_target: float = 0.7885399799896772,
        closure_weight: float = -4.5,
        closure_power: float = 2.0,
        all_starts: bool = True,
    ) -> None:
        self.distance_weight = distance_weight
        self.angular_weight = angular_weight
        self.radial_weight = radial_weight
        self.density_weight = density_weight
        self.harmonic_weight = harmonic_weight
        self.momentum_weight = momentum_weight
        self.phase = phase
        self.radius_target = radius_target
        self.closure_weight = closure_weight
        self.closure_power = closure_power
        self.all_starts = all_starts

    def collapse(
        self,
        problem: ProblemInstance[TspEncoding],
        field: ResonanceField[List[GeometricSignal]],
    ) -> List[Candidate[Route]]:
        signals_by_city = {signal.city_index: signal for signal in field.values}
        starts = range(len(problem.encoded.coords)) if self.all_starts else [0]
        max_distance = max(max(row) for row in problem.encoded.dist_matrix) or 1
        max_radius = max(signal.radius for signal in field.values) or 1.0
        max_density = max(signal.local_density for signal in field.values) or 1.0

        candidates: List[Candidate[Route]] = []
        for start in starts:
            route = self._collapse_from_start(
                problem,
                signals_by_city,
                start,
                max_distance,
                max_radius,
                max_density,
            )
            candidates.append(
                Candidate(
                    route,
                    {
                        "collapse": "pure_sequential_resonant_front",
                        "start_city": start,
                        "post_refinement": False,
                        "closure_weight": self.closure_weight,
                        "closure_power": self.closure_power,
                    },
                )
            )
        return candidates

    def _collapse_from_start(
        self,
        problem: ProblemInstance[TspEncoding],
        signals_by_city: Dict[int, GeometricSignal],
        start: int,
        max_distance: int,
        max_radius: float,
        max_density: float,
    ) -> Route:
        n = len(problem.encoded.coords)
        unvisited = set(range(n))
        unvisited.remove(start)
        route = [start]
        previous_previous_angle = signals_by_city[start].angle

        while unvisited:
            current = route[-1]
            current_angle = signals_by_city[current].angle
            momentum = angular_delta(current_angle, previous_previous_angle)
            progress = len(route) / n
            next_city = min(
                unvisited,
                key=lambda city: self._transition_score(
                    problem,
                    signals_by_city,
                    current,
                    city,
                    start,
                    progress,
                    momentum,
                    max_distance,
                    max_radius,
                    max_density,
                ),
            )
            previous_previous_angle = current_angle
            route.append(next_city)
            unvisited.remove(next_city)
        return route

    def _transition_score(
        self,
        problem: ProblemInstance[TspEncoding],
        signals_by_city: Dict[int, GeometricSignal],
        current: int,
        candidate: int,
        start: int,
        progress: float,
        momentum: float,
        max_distance: int,
        max_radius: float,
        max_density: float,
    ) -> float:
        current_signal = signals_by_city[current]
        candidate_signal = signals_by_city[candidate]
        distance_term = problem.encoded.dist_matrix[current][candidate] / max_distance
        angular_step = angular_delta(candidate_signal.angle, current_signal.angle)
        angular_term = abs(angular_step)
        momentum_term = abs(angular_delta(angular_step, momentum))
        radial_term = abs((candidate_signal.radius / max_radius) - self.radius_target)
        density_term = candidate_signal.local_density / max_density
        harmonic_term = math.sin(candidate_signal.angle + self.phase) + 0.5 * math.sin(
            2.0 * candidate_signal.angle + self.phase
        )
        closure_term = (problem.encoded.dist_matrix[candidate][start] / max_distance) * (
            progress ** self.closure_power
        )

        return (
            self.distance_weight * distance_term
            + self.angular_weight * angular_term
            + self.momentum_weight * momentum_term
            + self.radial_weight * radial_term
            + self.density_weight * density_term
            + self.harmonic_weight * harmonic_term
            + self.closure_weight * closure_term
        )


def angular_delta(angle_a: float, angle_b: float) -> float:
    return (angle_a - angle_b + math.pi) % (2.0 * math.pi) - math.pi
