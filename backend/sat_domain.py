"""SAT domain for the Resonant Intelligence Engine.

This module is the first bridge from the TSP Resonator to a canonical NP-complete
problem. It turns a DIMACS CNF instance into a resonance-guided assignment,
verifies it by unsatisfied clause count, and refines it with a WalkSAT-style
local search.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from resonant_core import Candidate, ProblemInstance, ResonanceField, ResonantRunResult, VerificationResult, Verifier

Literal = int
Clause = Tuple[Literal, ...]
Assignment = Dict[int, bool]


@dataclass(frozen=True)
class SatEncoding:
    variable_count: int
    clauses: List[Clause]


@dataclass(frozen=True)
class SatVariableSignal:
    variable: int
    occurrence_count: int
    positive_count: int
    negative_count: int
    polarity_balance: int
    phase: float
    value: float


class SatEncoder:
    def encode(self, raw_input: Any) -> ProblemInstance[SatEncoding]:
        if isinstance(raw_input, str):
            encoding = parse_dimacs(raw_input)
            source = raw_input
        else:
            encoding = raw_input
            source = "in-memory"
        return ProblemInstance(
            domain="sat",
            encoded=encoding,
            metadata={
                "source": source,
                "variable_count": encoding.variable_count,
                "clause_count": len(encoding.clauses),
            },
        )


class SatResonanceFieldBuilder:
    def __init__(self, harmonic_weight: float = 0.15) -> None:
        self.harmonic_weight = harmonic_weight

    def build(self, problem: ProblemInstance[SatEncoding]) -> ResonanceField[List[SatVariableSignal]]:
        n = problem.encoded.variable_count
        positive = [0] * (n + 1)
        negative = [0] * (n + 1)

        for clause in problem.encoded.clauses:
            for literal in clause:
                variable = abs(literal)
                if literal > 0:
                    positive[variable] += 1
                else:
                    negative[variable] += 1

        signals: List[SatVariableSignal] = []
        for variable in range(1, n + 1):
            occurrence_count = positive[variable] + negative[variable]
            polarity_balance = positive[variable] - negative[variable]
            phase = 2.0 * math.pi * (variable / max(n, 1))
            harmonic = self.harmonic_weight * math.cos(phase) * max(1, occurrence_count)
            value = polarity_balance + harmonic
            signals.append(
                SatVariableSignal(
                    variable=variable,
                    occurrence_count=occurrence_count,
                    positive_count=positive[variable],
                    negative_count=negative[variable],
                    polarity_balance=polarity_balance,
                    phase=phase,
                    value=value,
                )
            )

        return ResonanceField(
            values=signals,
            metadata={
                "field_type": "polarity_frequency_harmonic",
                "harmonic_weight": self.harmonic_weight,
            },
        )


class SatAssignmentCollapse:
    def collapse(
        self,
        problem: ProblemInstance[SatEncoding],
        field: ResonanceField[List[SatVariableSignal]],
    ) -> List[Candidate[Assignment]]:
        primary = {signal.variable: signal.value >= 0 for signal in field.values}
        inverse = {variable: not value for variable, value in primary.items()}
        frequency_bias = {
            signal.variable: signal.positive_count >= signal.negative_count
            for signal in sorted(field.values, key=lambda item: item.occurrence_count, reverse=True)
        }
        return [
            Candidate(primary, {"collapse": "resonance_sign"}),
            Candidate(inverse, {"collapse": "inverse_resonance_sign"}),
            Candidate(frequency_bias, {"collapse": "positive_frequency_bias"}),
        ]


class SatAssignmentVerifier:
    def verify(self, problem: ProblemInstance[SatEncoding], candidate: Candidate[Assignment]) -> VerificationResult[int]:
        unsatisfied = unsatisfied_clause_indices(problem.encoded.clauses, candidate.value)
        return VerificationResult(
            score=len(unsatisfied),
            valid=len(unsatisfied) == 0,
            metadata={
                "metric": "unsatisfied_clause_count",
                "satisfied_clauses": len(problem.encoded.clauses) - len(unsatisfied),
                "total_clauses": len(problem.encoded.clauses),
            },
        )


class SatWalkSatRefiner:
    def __init__(self, max_flips: int = 10000, noise: float = 0.1, seed: int = 0) -> None:
        self.max_flips = max_flips
        self.noise = noise
        self.seed = seed

    def refine(
        self,
        problem: ProblemInstance[SatEncoding],
        candidate: Candidate[Assignment],
        verifier: Verifier[SatEncoding, Assignment, int],
    ) -> ResonantRunResult[Assignment, int]:
        random.seed(self.seed)
        current = dict(candidate.value)
        initial_verification = verifier.verify(problem, candidate)
        best = dict(current)
        best_score = initial_verification.score
        flips_used = 0

        for flip_index in range(self.max_flips):
            unsatisfied = unsatisfied_clause_indices(problem.encoded.clauses, current)
            current_score = len(unsatisfied)
            if current_score < best_score:
                best = dict(current)
                best_score = current_score
            if current_score == 0:
                flips_used = flip_index
                break

            clause = problem.encoded.clauses[random.choice(unsatisfied)]
            if random.random() < self.noise:
                variable_to_flip = abs(random.choice(clause))
            else:
                variable_to_flip = best_flip_in_clause(problem.encoded.clauses, current, clause)
            current[variable_to_flip] = not current.get(variable_to_flip, False)
            flips_used = flip_index + 1

        best_candidate = Candidate(best, {"refiner": "walksat_resonance_seed", "flips_used": flips_used})
        return ResonantRunResult(
            initial_candidate=candidate,
            initial_verification=initial_verification,
            final_candidate=best_candidate,
            final_verification=verifier.verify(problem, best_candidate),
            trace=[
                {
                    "stage": "refine",
                    "method": "walksat_resonance_seed",
                    "max_flips": self.max_flips,
                    "noise": self.noise,
                    "seed": self.seed,
                    "flips_used": flips_used,
                }
            ],
        )


def parse_dimacs(filename: str) -> SatEncoding:
    clauses: List[Clause] = []
    variable_count = 0
    current_clause: List[int] = []
    with open(filename, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("c"):
                continue
            if line.startswith("p"):
                parts = line.split()
                if len(parts) >= 4:
                    variable_count = int(parts[2])
                continue
            for token in line.split():
                literal = int(token)
                if literal == 0:
                    if current_clause:
                        clauses.append(tuple(current_clause))
                        current_clause = []
                else:
                    variable_count = max(variable_count, abs(literal))
                    current_clause.append(literal)
    if current_clause:
        clauses.append(tuple(current_clause))
    return SatEncoding(variable_count=variable_count, clauses=clauses)


def literal_is_satisfied(literal: Literal, assignment: Assignment) -> bool:
    value = assignment.get(abs(literal), False)
    return value if literal > 0 else not value


def clause_is_satisfied(clause: Clause, assignment: Assignment) -> bool:
    return any(literal_is_satisfied(literal, assignment) for literal in clause)


def unsatisfied_clause_indices(clauses: Sequence[Clause], assignment: Assignment) -> List[int]:
    return [index for index, clause in enumerate(clauses) if not clause_is_satisfied(clause, assignment)]


def best_flip_in_clause(clauses: Sequence[Clause], assignment: Assignment, clause: Clause) -> int:
    best_variable = abs(clause[0])
    best_score = math.inf
    for literal in clause:
        variable = abs(literal)
        trial = dict(assignment)
        trial[variable] = not trial.get(variable, False)
        score = len(unsatisfied_clause_indices(clauses, trial))
        if score < best_score:
            best_variable = variable
            best_score = score
    return best_variable


def summarize_sat_run(result: ResonantRunResult[Assignment, int]) -> Dict[str, Any]:
    return {
        "initial_unsatisfied": result.initial_verification.score,
        "final_unsatisfied": result.final_verification.score,
        "valid_solution": result.final_verification.valid,
        "assignment": result.final_candidate.value,
        "trace": [dict(item) for item in result.trace],
    }
