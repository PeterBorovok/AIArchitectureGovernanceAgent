from __future__ import annotations

import json
from pathlib import Path

from src.agent_state import AgentState
from src.config import SERVICES_INDEX_FILE, EVENTS_CATALOG_FILE


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def run(state: AgentState) -> AgentState:
    if not state.last_decision or state.last_decision["action"] != "approve":
        if state.last_decision and state.last_decision["action"] == "reject" and state.current_service:
            state.rejected_services.append(state.current_service)
        return state

    proposal = state.current_proposal or {}
    service_name = proposal["service_name"]
    service_slug = service_name.lower().replace(" ", "-").replace("/", "-")

    _ensure_parent(SERVICES_INDEX_FILE)
    _ensure_parent(EVENTS_CATALOG_FILE)

    services_index = _load_json(SERVICES_INDEX_FILE, {"services": []})
    events_catalog = _load_json(EVENTS_CATALOG_FILE, {"events": []})

    # Update services index
    if not any(s["name"] == service_name for s in services_index["services"]):
        services_index["services"].append({
            "name": service_name,
            "status": "approved",
            "path": f"portfolio/services/{service_slug}/service.json"
        })

    # Update event catalog
    for event_name in proposal.get("emitted_events", []):
        existing = next((e for e in events_catalog["events"] if e["event_name"] == event_name), None)
        if existing:
            if service_name not in existing["emitted_by"]:
                existing["emitted_by"].append(service_name)
        else:
            events_catalog["events"].append({
                "event_name": event_name,
                "emitted_by": [service_name],
                "consumed_by": []
            })

    for event_name in proposal.get("consumed_events", []):
        existing = next((e for e in events_catalog["events"] if e["event_name"] == event_name), None)
        if existing:
            if service_name not in existing["consumed_by"]:
                existing["consumed_by"].append(service_name)
        else:
            events_catalog["events"].append({
                "event_name": event_name,
                "emitted_by": [],
                "consumed_by": [service_name]
            })

    SERVICES_INDEX_FILE.write_text(json.dumps(services_index, indent=2), encoding="utf-8")
    EVENTS_CATALOG_FILE.write_text(json.dumps(events_catalog, indent=2), encoding="utf-8")

    state.service_portfolio = services_index
    state.event_catalog = events_catalog
    return state