from __future__ import annotations

import json

from src.agent_state import AgentState
from src.graph import run_agent
from src.config import OUTPUT_DIR


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    state = AgentState(project_name="MOIN", run_id="run-001")
    final_state = run_agent(state)

    (OUTPUT_DIR / "final_state.json").write_text(
        json.dumps(final_state.to_dict(), indent=2),
        encoding="utf-8"
    )

    print("\nAgent finished.")
    print(f"Approved services: {final_state.approved_services}")
    print(f"Rejected services: {final_state.rejected_services}")
    print(f"Missing services discovered: {[x['name'] for x in final_state.missing_services]}")
    print(
        "Services needing internal design: "
        f"{[x['name'] for x in final_state.services_needing_internal_design]}"
    )


if __name__ == "__main__":
    main()