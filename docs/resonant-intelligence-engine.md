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

This PR adds a small generic core in `backend/resonant_core.py` and a TSP domain adapter in `backend/tsp_domain.py`.

The current TSP domain uses:

- a TSPLIB/coordinate encoder;
- a finite harmonic field;
- route collapse by harmonic ordering;
- route verification by closed-tour cost;
- refinement with 2-Opt and Iterated Local Search.

The original `backend/resonator_tsp.py` is preserved. The new files do not replace the existing solver; they turn its logic into a reusable architecture.

## Why this matters

The TSP solver already shows the desired gesture: a hard combinatorial problem is not attacked by exhaustive enumeration. It is transformed into a structured field that emits a strong initial candidate before local refinement.

The next research step is to apply this same form to SAT and code repair.

## Next domains

### SAT Resonator

Input: DIMACS CNF.

Planned stages:

- encode variables, clauses, polarity and conflicts;
- build a variable-clause resonance field;
- collapse an initial truth assignment;
- verify by number of satisfied clauses;
- refine with a WalkSAT-style local search guided by resonance scores.

Initial benchmark:

- compare against random assignment;
- compare against plain WalkSAT;
- measure satisfied clauses before refinement;
- measure flips until solution.

### Code Resonator

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
