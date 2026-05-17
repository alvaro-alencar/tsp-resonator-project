"""Smoke tests for the Resonant Intelligence Engine.

These tests intentionally use only Python's standard library so the project can
be validated on a modest machine without installing pytest or extra packages.
"""

from __future__ import annotations

import os
import unittest

from resonant_core import ResonantPipeline
from sat_domain import (
    SatAssignmentCollapse,
    SatAssignmentVerifier,
    SatEncoder,
    SatResonanceFieldBuilder,
    SatWalkSatRefiner,
)
from tsp_domain import (
    HarmonicRouteCollapse,
    HarmonicTspFieldBuilder,
    TspEncoder,
    TspIlsRefiner,
    TspRouteVerifier,
)

BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(BASE_DIR)


class ResonantEngineSmokeTests(unittest.TestCase):
    def test_tsp_pipeline_returns_valid_route(self) -> None:
        problem = TspEncoder().encode(os.path.join(ROOT_DIR, "berlin52.tsp"))
        pipeline = ResonantPipeline(
            field_builder=HarmonicTspFieldBuilder(harmonics=2, amplitude=1.0, shift=0.0),
            collapse_strategy=HarmonicRouteCollapse(),
            verifier=TspRouteVerifier(),
            refiner=TspIlsRefiner(two_opt_iterations=500, ils_iterations=5, seed=2),
        )

        result = pipeline.run(problem)
        route = result.final_candidate.value

        self.assertTrue(result.final_verification.valid)
        self.assertEqual(len(route), problem.metadata["city_count"])
        self.assertEqual(set(route), set(range(problem.metadata["city_count"])))
        self.assertLessEqual(result.final_verification.score, result.initial_verification.score)

    def test_sat_pipeline_solves_simple_fixture(self) -> None:
        problem = SatEncoder().encode(os.path.join(BASE_DIR, "fixtures", "simple_sat.cnf"))
        pipeline = ResonantPipeline(
            field_builder=SatResonanceFieldBuilder(harmonic_weight=0.15),
            collapse_strategy=SatAssignmentCollapse(),
            verifier=SatAssignmentVerifier(),
            refiner=SatWalkSatRefiner(max_flips=200, noise=0.1, seed=0),
        )

        result = pipeline.run(problem)

        self.assertTrue(result.final_verification.valid)
        self.assertEqual(result.final_verification.score, 0)

    def test_sat_pipeline_does_not_false_positive_unsat_fixture(self) -> None:
        problem = SatEncoder().encode(os.path.join(BASE_DIR, "fixtures", "unsat_tiny.cnf"))
        pipeline = ResonantPipeline(
            field_builder=SatResonanceFieldBuilder(harmonic_weight=0.15),
            collapse_strategy=SatAssignmentCollapse(),
            verifier=SatAssignmentVerifier(),
            refiner=SatWalkSatRefiner(max_flips=200, noise=0.1, seed=0),
        )

        result = pipeline.run(problem)

        self.assertFalse(result.final_verification.valid)
        self.assertGreater(result.final_verification.score, 0)


if __name__ == "__main__":
    unittest.main()
