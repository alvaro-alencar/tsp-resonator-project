"""Core abstractions for the Resonant Intelligence Engine.

The goal of this module is not to solve one specific problem. It defines a
small, explicit pipeline that can later host TSP, SAT, code-repair and other
formal domains:

    raw input -> problem encoding -> resonance field -> candidate collapse
    -> verification -> refinement -> final result

This is the first step toward turning the TSP Resonator from a single solver
into a reusable research framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Mapping, Protocol, TypeVar


EncodedT = TypeVar("EncodedT")
FieldT = TypeVar("FieldT")
CandidateT = TypeVar("CandidateT")
ScoreT = TypeVar("ScoreT")


@dataclass(frozen=True)
class ProblemInstance(Generic[EncodedT]):
    """A formalized problem instance.

    The engine should never operate directly on unstructured user input. Every
    domain must first convert its raw data into an explicit structure with
    metadata that can be inspected, logged and compared.
    """

    domain: str
    encoded: EncodedT
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResonanceField(Generic[FieldT]):
    """A mathematical field extracted from a problem instance.

    This object is the heart of the approach: it stores the compact signature
    that guides candidate generation before any brute-force style search begins.
    """

    values: FieldT
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Candidate(Generic[CandidateT]):
    """A possible answer emitted by a collapse strategy."""

    value: CandidateT
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult(Generic[ScoreT]):
    """Objective evaluation of a candidate answer."""

    score: ScoreT
    valid: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResonantRunResult(Generic[CandidateT, ScoreT]):
    """Final result produced by one resonant pipeline run."""

    initial_candidate: Candidate[CandidateT]
    initial_verification: VerificationResult[ScoreT]
    final_candidate: Candidate[CandidateT]
    final_verification: VerificationResult[ScoreT]
    trace: List[Mapping[str, Any]] = field(default_factory=list)


class Encoder(Protocol[EncodedT]):
    """Convert raw input into a formal problem instance."""

    def encode(self, raw_input: Any) -> ProblemInstance[EncodedT]:
        ...


class FieldBuilder(Protocol[EncodedT, FieldT]):
    """Extract a resonance field from a formal problem instance."""

    def build(self, problem: ProblemInstance[EncodedT]) -> ResonanceField[FieldT]:
        ...


class CollapseStrategy(Protocol[EncodedT, FieldT, CandidateT]):
    """Generate one or more answer candidates from the field."""

    def collapse(
        self,
        problem: ProblemInstance[EncodedT],
        field: ResonanceField[FieldT],
    ) -> List[Candidate[CandidateT]]:
        ...


class Verifier(Protocol[EncodedT, CandidateT, ScoreT]):
    """Measure whether a candidate satisfies the problem constraints."""

    def verify(
        self,
        problem: ProblemInstance[EncodedT],
        candidate: Candidate[CandidateT],
    ) -> VerificationResult[ScoreT]:
        ...


class Refiner(Protocol[EncodedT, CandidateT, ScoreT]):
    """Improve a candidate using domain-specific local transformations."""

    def refine(
        self,
        problem: ProblemInstance[EncodedT],
        candidate: Candidate[CandidateT],
        verifier: Verifier[EncodedT, CandidateT, ScoreT],
    ) -> ResonantRunResult[CandidateT, ScoreT]:
        ...


class ResonantPipeline(Generic[EncodedT, FieldT, CandidateT, ScoreT]):
    """Composable resonant problem-solving pipeline."""

    def __init__(
        self,
        field_builder: FieldBuilder[EncodedT, FieldT],
        collapse_strategy: CollapseStrategy[EncodedT, FieldT, CandidateT],
        verifier: Verifier[EncodedT, CandidateT, ScoreT],
        refiner: Refiner[EncodedT, CandidateT, ScoreT],
    ) -> None:
        self.field_builder = field_builder
        self.collapse_strategy = collapse_strategy
        self.verifier = verifier
        self.refiner = refiner

    def run(self, problem: ProblemInstance[EncodedT]) -> ResonantRunResult[CandidateT, ScoreT]:
        field = self.field_builder.build(problem)
        candidates = self.collapse_strategy.collapse(problem, field)
        if not candidates:
            raise ValueError("Collapse strategy did not emit any candidates.")

        scored = [(candidate, self.verifier.verify(problem, candidate)) for candidate in candidates]
        initial_candidate, initial_verification = min(scored, key=lambda pair: pair[1].score)

        refined = self.refiner.refine(problem, initial_candidate, self.verifier)
        trace: List[Dict[str, Any]] = [
            {
                "stage": "field",
                "metadata": dict(field.metadata),
            },
            {
                "stage": "collapse",
                "candidate_count": len(candidates),
                "selected_initial_score": initial_verification.score,
            },
        ]
        trace.extend(refined.trace)

        return ResonantRunResult(
            initial_candidate=initial_candidate,
            initial_verification=initial_verification,
            final_candidate=refined.final_candidate,
            final_verification=refined.final_verification,
            trace=trace,
        )
