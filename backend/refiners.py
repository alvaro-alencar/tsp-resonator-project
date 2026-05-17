"""Generic refinement strategies for the Resonant Intelligence Engine.

The PureResonanceRefiner intentionally performs no local search. It exists to
isolate the quality of the field + collapse stages from any classical heuristic
such as 2-Opt, ILS or WalkSAT.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from resonant_core import Candidate, ProblemInstance, ResonantRunResult, VerificationResult, Verifier

EncodedT = TypeVar("EncodedT")
CandidateT = TypeVar("CandidateT")
ScoreT = TypeVar("ScoreT")


class PureResonanceRefiner(Generic[EncodedT, CandidateT, ScoreT]):
    """Return the collapsed candidate unchanged.

    This refiner is deliberately boring. Its scientific value is that it prevents
    downstream heuristics from hiding whether the resonant field actually emitted
    a useful candidate.
    """

    def refine(
        self,
        problem: ProblemInstance[EncodedT],
        candidate: Candidate[CandidateT],
        verifier: Verifier[EncodedT, CandidateT, ScoreT],
    ) -> ResonantRunResult[CandidateT, ScoreT]:
        verification: VerificationResult[ScoreT] = verifier.verify(problem, candidate)
        return ResonantRunResult(
            initial_candidate=candidate,
            initial_verification=verification,
            final_candidate=candidate,
            final_verification=verification,
            trace=[
                {
                    "stage": "refine",
                    "method": "pure_resonance_no_local_search",
                    "changed_candidate": False,
                }
            ],
        )
