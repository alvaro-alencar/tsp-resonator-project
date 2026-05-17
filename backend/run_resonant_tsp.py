"""Minimal runner for the resonant TSP pipeline."""

from __future__ import annotations

import argparse
import json
import time

from refiners import PureResonanceRefiner
from resonant_core import ResonantPipeline
from tsp_domain import (
    GeometricRouteCollapse,
    GeometricTspFieldBuilder,
    HarmonicRouteCollapse,
    HarmonicTspFieldBuilder,
    TspEncoder,
    TspIlsRefiner,
    TspRouteVerifier,
    summarize_tsp_run,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tsp_file")
    parser.add_argument("--field", choices=["harmonic", "geometric"], default="geometric")
    parser.add_argument("--mode", choices=["pure", "refined"], default="pure")
    parser.add_argument("--N", type=int, default=7)
    parser.add_argument("--A", type=float, default=1.0)
    parser.add_argument("--shift", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--two_opt_iter", type=int, default=2000)
    parser.add_argument("--ils_iter", type=int, default=50)
    args = parser.parse_args()

    if args.field == "harmonic":
        field_builder = HarmonicTspFieldBuilder(args.N, args.A, args.shift)
        collapse = HarmonicRouteCollapse()
    else:
        field_builder = GeometricTspFieldBuilder()
        collapse = GeometricRouteCollapse()

    if args.mode == "pure":
        refiner = PureResonanceRefiner()
    else:
        refiner = TspIlsRefiner(args.two_opt_iter, args.ils_iter, args.seed)

    problem = TspEncoder().encode(args.tsp_file)
    pipeline = ResonantPipeline(
        field_builder=field_builder,
        collapse_strategy=collapse,
        verifier=TspRouteVerifier(),
        refiner=refiner,
    )

    start = time.perf_counter()
    result = pipeline.run(problem)
    output = summarize_tsp_run(result)
    output["elapsed_seconds"] = time.perf_counter() - start
    output["parameters"] = vars(args)
    output["problem"] = dict(problem.metadata)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
