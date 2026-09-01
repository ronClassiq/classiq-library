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

They run on a **statevector backend** and feed `es.sample()`'s `ExecutionDetails`
into a **shared helper** (`get_projected_state_vector`, in
`hamiltonian_simulation_utils.py`) that reads `.output_qubits_map` and
`.dataframe`. Two blockers: the flat `sample()` / `ExecutionSession(backend=…)`
API **rejects statevector backend names**, and free `sample()` returns a bare
DataFrame the helper cannot consume. The proper fix is a **coordinated
`calculate_state_vector` refactor** of the shared helper plus all three
notebooks together — a follow-up, not part of this PR.

## 2. Multi-backend comparison via `BackendPreferences` objects (2) — no flat equivalent

- `applications/benchmarking/quantum_volume/quantum_volume.ipynb`
- `applications/benchmarking/randomized_benchmarking/randomized_benchmarking.ipynb`

These pass full **`BackendPreferences` objects** (simulator / IBM / Azure, with
credentials) to compare backends. Free `sample()` only accepts a backend **name
string** (+ optional `ProviderConfig`); the only current surface that accepts an
arbitrary `BackendPreferences` object is `ExecutionPreferences(backend_preferences=…)`.
`randomized_benchmarking` additionally consumes those objects downstream
(`RBAnalysis` reads `hardware.backend_name`), needs `ExecutionDetails.counts`
(free `sample()` returns a DataFrame with no `.counts`), and runs a **concurrent
`execute_async` batch** for which there is no free-function equivalent
(`batch_*` are removed stubs). Flattening either would drop backends/credentials
or serialize the batch — a behavior/performance change — so both are kept.

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

---

## Not exceptions — kept sessions that ARE the new interface

For completeness: a few migrated notebooks still contain an `ExecutionSession`
**by design** — these are the correct new-interface pattern (a session reused
across a manual optimizer/VQE loop), not old-API leftovers, and are also listed
as exceptions so the report does not flag them: `qaoa`, `gm_qaoa`,
`vehicle_routing_problem`, `adapt_vqe`, `vqls_with_lcu`. (`vqls_with_lcu` also
keeps a final `simulator_statevector` measurement whose optional
`calculate_state_vector` refactor is deferred, as with the group-1 notebooks.)
