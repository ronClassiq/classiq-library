"""Use the new execution interface, not the old one.

This is not a single rule but a *family* of signals — the SDK moved from
`execute(qprog).result_value()` and nested `ExecutionPreferences` to free
`sample()` / `observe()` (and a flat `ExecutionSession` only for deliberate
multi-call reuse), plus a DataFrame-shaped result. The individual signals live
in `_exec_signals.py`; this point unions them and the report shows a per-family
breakdown underneath it.
"""

from . import _exec_signals
from ._model import Notebook, Point


def detect(nb: Notebook) -> list[str]:
    return _exec_signals.detect(nb)


POINT = Point(
    title="execution_interface",
    detail="execute() / ExecutionPreferences / .estimate / batch_*  ->  sample() / observe() / variational_minimize",
    description="Use the new execution interface: free sample()/observe(), no nested "
    "ExecutionPreferences, observe not .estimate, variational_minimize not .minimize, "
    "no batch_*, and a DataFrame-shaped result (no .parsed_counts / .dataframe).",
    static=True,
    detect=detect,
    fix=None,  # migration reshapes cells; handled per-family (script or agent), not one regex
    subsignals=_exec_signals.SIGNALS,
    # Reviewed exceptions: notebooks that correctly use the new interface but keep
    # an ExecutionSession by design (a deliberate multi-call loop driven by a
    # classical optimizer) and/or must keep parsed_counts (a QStruct output that
    # `.dataframe` would flatten). These are conforming, not offenders.
    exceptions=(
        (
            "search_and_optimization/QAOA/qaoa",
            "keeps ExecutionSession for two scipy optimizer loops (es.estimate_cost); "
            "knapsack output is a QStruct, so parsed_counts stays",
        ),
        (
            "search_and_optimization/grover_mixer_qaoa/gm_qaoa",
            "keeps ExecutionSession for both COBYLA optimizer loops (es.estimate_cost)",
        ),
        (
            "logistics/vehicle_routing_problem/vehicle_routing_problem",
            "keeps ExecutionSession for the scipy COBYLA loop (es.estimate_cost) plus a "
            "final es.sample; .dataframe access on the kept session",
        ),
        (
            "quantum_state_preparation/adapt_vqe/adapt_vqe",
            "keeps ExecutionSession for the per-operator gradient loop (~56 executions of "
            "qprog_grads); standalone minimize calls use the free variational_minimize",
        ),
    ),
)
