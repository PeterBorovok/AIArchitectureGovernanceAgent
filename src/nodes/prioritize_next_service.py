from __future__ import annotations

from src.agent_state import AgentState


def run(state: AgentState) -> AgentState:
    remaining = [
        name
        for name in state.design_queue
        if name not in state.approved_services and name not in state.rejected_services
    ]

    if not remaining:
        state.current_service = None
        state.current_baseline_service = None
        state.current_extracted_service = None
        state.finished = True
        return state

    next_name = remaining[0]
    state.current_service = next_name

    state.current_baseline_service = next(
        (svc for svc in state.baseline_services if svc.get("name") == next_name),
        None,
    )

    state.current_extracted_service = next(
        (
            svc
            for svc in state.extracted_top_level_architecture.get("services", [])
            if svc.get("name") == next_name
        ),
        None,
    )

    return state