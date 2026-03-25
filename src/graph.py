from __future__ import annotations

from src.agent_state import AgentState
from src.nodes import (
    ingest_context,
    discover_missing_services,
    prioritize_next_service,
    generate_service_design,
    validate_service_design,
    human_review,
    finalize_service_package,
    update_portfolio,
)


def run_agent(state: AgentState) -> AgentState:
    state = ingest_context.run(state)
    state = discover_missing_services.run(state)

    while not state.finished:
        state = prioritize_next_service.run(state)
        if state.finished or not state.current_service:
            break

        while True:
            state = generate_service_design.run(state)
            state = validate_service_design.run(state)
            state = human_review.run(state)

            if state.last_decision and state.last_decision["action"] == "edit":
                print("\nRegenerating based on edit instructions...\n")
                continue

            break

        state = finalize_service_package.run(state)
        state = update_portfolio.run(state)

    return state