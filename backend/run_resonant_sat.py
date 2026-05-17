"""Minimal runner for the resonant SAT pipeline."""

from __future__ import annotations

import argparse
import json
import time

from resonant_core import ResonantPipeline
from sat_domain import SatAssignmentCollapse, SatAssignmentVerifier, SatEncoder, SatResonanceFieldBuilder, SatWalkSatRefiner, summarize_sat_run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cnf_file")
    parser.add_argument("--harmonic_weight", type=float, default=0.15)
    parser.add_argument("--max_flips", type=int, default=10000)
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    problem = SatEncoder().encode(args.cnf_file)
    pipeline = ResonantPipeline(
        field_builder=SatResonanceFieldBuilder(args.harmonic_weight),
        collapse_strategy=SatAssignmentCollapse(),
        verifier=SatAssignmentVerifier(),
        refiner=SatWalkSatRefiner(args.max_flips, args.noise, args.seed),
    )

    start = time.perf_counter()
    result = pipeline.run(problem)
    output = summarize_sat_run(result)
    output["elapsed_seconds"] = time.perf_counter() - start
    output["parameters"] = vars(args)
    output["problem"] = dict(problem.metadata)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
