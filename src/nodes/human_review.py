from __future__ import annotations

import json
from src.agent_state import AgentState


def run(state: AgentState) -> AgentState:
    print("\n" + "=" * 80)
    print(f"REVIEW SERVICE: {state.current_service}")
    print("=" * 80)

    print("\nProposal:")
    print(json.dumps(state.current_proposal, indent=2))

    print("\nValidation:")
    print(json.dumps(state.current_validation, indent=2))

    while True:
        action = input("\nChoose action [approve/reject/edit]: ").strip().lower()
        if action in {"approve", "reject", "edit"}:
            break
        print("Invalid action.")

    comment = ""
    if action in {"reject", "edit"}:
        comment = input("Enter review comment/instructions: ").strip()

    state.last_decision = {"action": action, "comment": comment}
    state.review_history.append({
        "service": state.current_service,
        "proposal": state.current_proposal,
        "validation": state.current_validation,
        "decision": state.last_decision
    })

    return state