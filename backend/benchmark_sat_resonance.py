"""Benchmark SAT resonance seeding against random seeding.

This script generates planted satisfiable 3-SAT instances and compares:

1. resonance-seeded initial assignment;
2. best of three random initial assignments;
3. resonance-seeded WalkSAT refinement;
4. random-seeded WalkSAT refinement.

It is intentionally dependency-free so it can run on modest machines.
"""

from __future__ import annotations

import argparse
import random
import statistics
from typing import Dict, List

from resonant_core import Candidate, ResonantPipeline
from sat_domain import (
    Assignment,
    SatAssignmentCollapse,
    SatAssignmentVerifier,
    SatEncoder,
    SatEncoding,
    SatResonanceFieldBuilder,
    SatWalkSatRefiner,
)


def random_assignment(variable_count: int, rng: random.Random) -> Assignment:
    return {variable: rng.choice([False, True]) for variable in range(1, variable_count + 1)}


def make_planted_3sat(
    variable_count: int,
    clause_count: int,
    clause_size: int,
    seed: int,
) -> SatEncoding:
    rng = random.Random(seed)
    planted = random_assignment(variable_count, rng)
    clauses = []

    for _ in range(clause_count):
        variables = rng.sample(range(1, variable_count + 1), clause_size)
        literals = [variable if rng.choice([False, True]) else -variable for variable in variables]

        if not any((planted[abs(literal)] if literal > 0 else not planted[abs(literal)]) for literal in literals):
            variable = variables[0]
            literals[0] = variable if planted[variable] else -variable

        clauses.append(tuple(literals))

    return SatEncoding(variable_count=variable_count, clauses=clauses)


def run_benchmark(args: argparse.Namespace) -> Dict[str, object]:
    verifier = SatAssignmentVerifier()
    resonance_initial: List[int] = []
    random_initial: List[int] = []
    resonance_final: List[int] = []
    random_final: List[int] = []
    resonance_solved = 0
    random_solved = 0

    for seed in range(args.instances):
        encoding = make_planted_3sat(args.variables, args.clauses, args.clause_size, seed)
        problem = SatEncoder().encode(encoding)

        resonance_pipeline = ResonantPipeline(
            field_builder=SatResonanceFieldBuilder(args.harmonic_weight),
            collapse_strategy=SatAssignmentCollapse(),
            verifier=verifier,
            refiner=SatWalkSatRefiner(args.max_flips, args.noise, seed),
        )
        resonance_result = resonance_pipeline.run(problem)
        resonance_initial.append(resonance_result.initial_verification.score)
        resonance_final.append(resonance_result.final_verification.score)
        resonance_solved += int(resonance_result.final_verification.valid)

        rng = random.Random(args.random_seed_offset + seed)
        random_candidates = [
            Candidate(random_assignment(args.variables, rng), {"collapse": "random"})
            for _ in range(args.random_candidates)
        ]
        best_random = min(random_candidates, key=lambda candidate: verifier.verify(problem, candidate).score)
        random_initial.append(verifier.verify(problem, best_random).score)

        random_result = SatWalkSatRefiner(args.max_flips, args.noise, seed).refine(problem, best_random, verifier)
        random_final.append(random_result.final_verification.score)
        random_solved += int(random_result.final_verification.valid)

    return {
        "instances": args.instances,
        "variables": args.variables,
        "clauses": args.clauses,
        "clause_size": args.clause_size,
        "resonance_initial_mean": statistics.mean(resonance_initial),
        "random_initial_mean": statistics.mean(random_initial),
        "resonance_final_mean": statistics.mean(resonance_final),
        "random_final_mean": statistics.mean(random_final),
        "resonance_solved": resonance_solved,
        "random_solved": random_solved,
        "initial_resonance_wins": sum(a < b for a, b in zip(resonance_initial, random_initial)),
        "initial_ties": sum(a == b for a, b in zip(resonance_initial, random_initial)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=int, default=30)
    parser.add_argument("--variables", type=int, default=40)
    parser.add_argument("--clauses", type=int, default=170)
    parser.add_argument("--clause_size", type=int, default=3)
    parser.add_argument("--harmonic_weight", type=float, default=0.15)
    parser.add_argument("--max_flips", type=int, default=2000)
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument("--random_candidates", type=int, default=3)
    parser.add_argument("--random_seed_offset", type=int, default=100000)
    args = parser.parse_args()

    result = run_benchmark(args)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
