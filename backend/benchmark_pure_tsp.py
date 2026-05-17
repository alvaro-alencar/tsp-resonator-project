"""Benchmark pure resonance TSP fields without classical refinement."""

from __future__ import annotations

import argparse
import statistics

from refiners import PureResonanceRefiner
from resonant_core import ResonantPipeline
from tsp_domain import (
    GeometricRouteCollapse,
    GeometricTspFieldBuilder,
    HarmonicRouteCollapse,
    HarmonicTspFieldBuilder,
    TspEncoder,
    TspRouteVerifier,
)


def evaluate(problem_file: str, field_name: str) -> int:
    if field_name == "harmonic":
        field_builder = HarmonicTspFieldBuilder()
        collapse = HarmonicRouteCollapse()
    else:
        field_builder = GeometricTspFieldBuilder()
        collapse = GeometricRouteCollapse()

    pipeline = ResonantPipeline(
        field_builder=field_builder,
        collapse_strategy=collapse,
        verifier=TspRouteVerifier(),
        refiner=PureResonanceRefiner(),
    )

    problem = TspEncoder().encode(problem_file)
    result = pipeline.run(problem)
    return result.final_verification.score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tsp_file")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    harmonic_scores = []
    geometric_scores = []

    for _ in range(args.runs):
        harmonic_scores.append(evaluate(args.tsp_file, "harmonic"))
        geometric_scores.append(evaluate(args.tsp_file, "geometric"))

    print("=== Pure Resonance Benchmark ===")
    print(f"harmonic_mean: {statistics.mean(harmonic_scores):.2f}")
    print(f"geometric_mean: {statistics.mean(geometric_scores):.2f}")
    print(f"harmonic_best: {min(harmonic_scores)}")
    print(f"geometric_best: {min(geometric_scores)}")


if __name__ == "__main__":
    main()
