# Execution-API migration — notebooks left as-is

This migration moved library notebooks from the old execution surface
(`execute()`, nested `ExecutionPreferences`, `ExecutionSession` around single
calls, `.estimate`/`.minimize`, `parsed_counts`/`.dataframe`, `batch_*`) to the
new one (free `sample()` / `observe()`, `variational_minimize`, DataFrame
results, and a flat `ExecutionSession` kept only for genuine multi-call loops).

A minority of notebooks are **deliberately kept as-is**: they either use a
valid, current SDK surface that the new flat API cannot express, or they need a
structural rewrite that is out of scope for an API-only migration. Each is
registered as an exception in
`.internal/conventions/points/point_execution_interface.py`, so the convention
report treats them as conforming. They are grouped below with the reason.

## 1. Statevector post-selection (3) — valid API, not expressible in the flat form

- `algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qsvt.ipynb`
- `algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_gqsp.ipynb`
- `algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qubitization.ipynb`
- `tutorials/workshops/algo_design_QCE_tutorial/algo_design_QCE_tutorial_part_I.ipynb`
  (mostly migrated to free `sample()`; only Exercise/Solution 6A keep a
  `simulator_statevector` run via a `ClassiqBackendPreferences` object)

They run on a **statevector backend** and feed `es.sample()`'s `ExecutionDetails`
into a **shared helper** (`get_projected_state_vector`, in
`hamiltonian_simulation_utils.py`) that reads `.output_qubits_map` and
`.dataframe`. Two blockers: the flat `sample()` / `ExecutionSession(backend=…)`
API **rejects statevector backend names**, and free `sample()` returns a bare
DataFrame the helper cannot consume. The proper fix is a **coordinated
`calculate_state_vector` refactor** of the shared helper plus all three
notebooks together — a follow-up, not part of this PR.

## 2. `BackendPreferences` objects / async job submission (3) — no flat equivalent

- `applications/benchmarking/quantum_volume/quantum_volume.ipynb`
- `applications/benchmarking/randomized_benchmarking/randomized_benchmarking.ipynb`
- `applications/physical_systems/quantum_chaos/quantum_sawtooth_map.ipynb` (its
  simulator run is migrated; only the real-hardware path is kept)
- `tutorials/basic_tutorials/quantumwalk_complex_network/quantumwalk_complex_network.ipynb`
  (live run migrated; only a commented-out credentialed IBM-hardware example kept)

These pass full **`BackendPreferences` objects** (simulator / IBM / Azure / IonQ,
often with credentials) to select or compare backends. Free `sample()` only
accepts a backend **name string** (+ optional `ProviderConfig`); the only current
surface that accepts an arbitrary `BackendPreferences` object is
`ExecutionPreferences(backend_preferences=…)`. They also use APIs with **no
free-function equivalent**: `randomized_benchmarking` consumes the objects in
`RBAnalysis` (`hardware.backend_name`), needs `ExecutionDetails.counts`, and runs
a concurrent `execute_async` batch; `quantum_sawtooth_map`'s hardware path (behind
`RUN_ON_HARDWARE`, default `False`) uses `submit_batch_sample` → `ExecutionJob.from_id`
→ `get_batch_sample_result` (submit-now, retrieve-later). Flattening would drop
backends/credentials or destroy the async workflow — a behavior change — so kept.

## 3. Legacy combinatorial-optimization VQE flow (7) — needs a CombinatorialProblem rewrite

- `applications/cybersecurity/link_monitoring/link_monitoring.ipynb`
- `applications/optimization/qaoa_in_qaoa/qaoa_in_qaoa.ipynb`
- `applications/optimization/rectangles_packing/rectangles_packing_grid.ipynb`
- `applications/optimization/low_autocorrelation_binary_sequences_problem/evidence_scaling_labs.ipynb`
- `applications/logistics/task_scheduling_problem/task_scheduling_problem.ipynb`
- `applications/telecom/radio_access_network/radio_access_network_positioning_antennas.ipynb`
- `tutorials/technology_demonstrations/qaoa/qaoa_demonstration.ipynb`

These use the legacy `construct_combinatorial_optimization_model` flow, where
`execute(qprog).result_value()` runs the **embedded classical VQE loop** and
returns a **`VQESolverResult`** (consumed by `get_optimization_solution_from_pyo`
and `.convergence_graph`) — **not** a measurement DataFrame. Free `sample()`
returns a DataFrame and never runs the VQE, so there is **no mechanical
`execute()` → `sample()` swap**. Making them use the new interface requires a
**structural rewrite to the high-level `CombinatorialProblem` API**
(`combi.optimize()` / `combi.sample()`) — a deliberate refactor that is a
separate follow-up. Note: PR #1643 (the comprehensive R&D migration reference)
also left all seven of these untouched.

## 4. Not the classiq execution API at all (1)

- `applications/telecom/resiliency_planning/resiliency_planning_AMD.ipynb`

Synthesizes with classiq, then extracts QASM and runs on a **Qiskit Aer (AMD GPU)
simulator**. Its `parsed_counts` hits belong to a custom `ClassiqSampleResult`
shim that reshapes Qiskit output to _look_ like classiq — it is not the SDK's
execution surface, so there is nothing to migrate. (Dead `classiq.execution`
imports were removed.)

---

## Not exceptions — kept sessions that ARE the new interface

For completeness: a few migrated notebooks still contain an `ExecutionSession`
**by design** — these are the correct new-interface pattern (a session reused
across a manual optimizer/VQE loop), not old-API leftovers, and are also listed
as exceptions so the report does not flag them: `qaoa`, `gm_qaoa`,
`vehicle_routing_problem`, `adapt_vqe`, `adapt_qaoa`, `vqls_with_lcu`,
`robust_posture_optimization`, `network_traffic_optimization`,
`combinatorial_qmod_workshop_for_maxcut`, `combi_workshop_Inequality_constriants_PO`,
`combi_workshop_equality_constriants_PO`, `algo_design_QCE_tutorial_part_II`.
`execution_tutorial_part2` also keeps a session, but as a **deliberate feature
demo** of the async `submit_sample`/`submit_observe` + `ExecutionJob.from_id`
API (no free-function equivalent).
(`vqls_with_lcu` also keeps a final
`simulator_statevector` measurement whose optional `calculate_state_vector`
refactor is deferred, as with the group-1 notebooks.)
