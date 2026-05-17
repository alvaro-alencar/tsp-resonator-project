# Resonant Intelligence Engine

This document defines the first technical bridge from the TSP Resonator to a broader problem-solving engine.

The central idea is simple:

> Do not search the raw space. Encode the problem, extract its internal field, collapse candidates, verify them, refine them, and only then narrate the answer.

## Pipeline

```text
raw input
  -> problem encoding
  -> resonance field
  -> candidate collapse
  -> verification
  -> refinement
  -> final answer
```

## Current implementation

This PR adds a small generic core in `backend/resonant_core.py` plus two domain adapters:

- `backend/tsp_domain.py` for TSP;
- `backend/sat_domain.py` for SAT/CNF.

The original `backend/resonator_tsp.py` is preserved. The new files do not replace the existing solver; they turn its logic into a reusable architecture.

## TSP Resonator

The current TSP domain uses:

- a TSPLIB/coordinate encoder;
- a finite harmonic field;
- route collapse by harmonic ordering;
- route verification by closed-tour cost;
- refinement with 2-Opt and Iterated Local Search.

Runner:

```bash
cd backend
python run_resonant_tsp.py ../berlin52.tsp --N 7 --A 1.0 --shift 0.0 --seed 0
```

## SAT Resonator

The first SAT domain uses:

- a DIMACS CNF encoder;
- a polarity/frequency/harmonic variable field;
- assignment collapse by resonance sign, inverse sign and frequency bias;
- verification by unsatisfied clause count;
- refinement with a WalkSAT-style local search.

Runner:

```bash
cd backend
python run_resonant_sat.py path/to/problem.cnf --max_flips 10000 --noise 0.1 --seed 0
```

Initial benchmark targets:

- compare resonance-seeded assignments against random assignment;
- compare resonance-seeded WalkSAT against plain WalkSAT;
- measure unsatisfied clauses before refinement;
- measure flips until solution.

## Why this matters

The TSP solver already shows the desired gesture: a hard combinatorial problem is not attacked by exhaustive enumeration. It is transformed into a structured field that emits a strong initial candidate before local refinement.

The SAT adapter is the next step: the same architecture is now applied to a canonical NP-complete domain.

## Next domain: Code Resonator

Input: repository plus failing test or issue.

Planned stages:

- encode files, functions, imports, call relations and error traces;
- build a repository tension field;
- collapse suspicious files or regions;
- ask an LLM for patches only after the search space has been reduced;
- verify through tests.

This makes the LLM a narrator and patch proposer, not the whole intelligence.

## Development principle

Never call a language model before extracting structure.

The model should receive a problem that has already been compressed, ranked and partially solved by the engine.
