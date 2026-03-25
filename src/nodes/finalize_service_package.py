from __future__ import annotations

import json
from pathlib import Path

from src.agent_state import AgentState
from src.config import PORTFOLIO_DIR


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


def run(state: AgentState) -> AgentState:
    if not state.last_decision or state.last_decision["action"] != "approve":
        return state

    proposal = state.current_proposal or {}
    service_name = proposal.get("service_name", "").strip()
    if not service_name:
        state.errors.append("Cannot finalize service package: missing service_name in proposal")
        return state

    service_slug = _slugify(service_name)

    service_dir = PORTFOLIO_DIR / "services" / service_slug
    service_dir.mkdir(parents=True, exist_ok=True)

    normalized_proposal = _normalize_proposal_for_output(proposal)

    # service.json
    (service_dir / "service.json").write_text(
        json.dumps(normalized_proposal, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # events.json
    events_doc = {
        "service_name": service_name,
        "consumed_events": normalized_proposal.get("consumed_events", []),
        "emitted_events": normalized_proposal.get("emitted_events", [])
    }
    (service_dir / "events.json").write_text(
        json.dumps(events_doc, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # design.md
    md = f"# {service_name}\n\n"

    md += "## Purpose\n"
    md += f"{normalized_proposal.get('service_purpose', '')}\n\n"

    md += "## Bounded Context\n"
    md += f"{normalized_proposal.get('bounded_context', '')}\n\n"

    md += "## Service Type\n"
    md += f"{normalized_proposal.get('service_type', '')}\n\n"

    md += "## Internal Components\n"
    for component in normalized_proposal.get("internal_components", []):
        md += (
            f"- **{component.get('name', '')}** "
            f"({component.get('type', '')}): "
            f"{component.get('responsibility', '')}\n"
        )

    md += "\n## Data Owned\n"
    for item in normalized_proposal.get("data_owned", []):
        md += f"- {item}\n"

    md += "\n## Consumed Events\n"
    for event in normalized_proposal.get("consumed_events", []):
        md += f"- {event}\n"

    md += "\n## Emitted Events\n"
    for event in normalized_proposal.get("emitted_events", []):
        md += f"- {event}\n"

    md += "\n## External Integrations\n"
    for item in normalized_proposal.get("external_integrations", []):
        md += f"- {item}\n"

    md += "\n## Security Controls\n"
    for item in normalized_proposal.get("security_controls", []):
        md += f"- {item}\n"

    md += "\n## Observability\n"
    for item in normalized_proposal.get("observability", []):
        md += f"- {item}\n"

    md += "\n## Open Questions\n"
    open_questions = normalized_proposal.get("open_questions", [])
    if open_questions:
        for item in open_questions:
            md += f"- {item}\n"
    else:
        md += "- None\n"

    md += "\n## Confidence\n"
    md += f"{normalized_proposal.get('confidence', '')}\n"

    (service_dir / "design.md").write_text(md, encoding="utf-8")

    if service_name not in state.approved_services:
        state.approved_services.append(service_name)

    return state


def _normalize_proposal_for_output(proposal: dict) -> dict:
    normalized = dict(proposal)

    if "service_name" not in normalized and "name" in normalized:
        normalized["service_name"] = str(normalized.get("name", "")).strip()

    if "service_purpose" not in normalized:
        if "purpose" in normalized and isinstance(normalized["purpose"], str):
            normalized["service_purpose"] = normalized["purpose"].strip()
        elif "description" in normalized and isinstance(normalized["description"], str):
            normalized["service_purpose"] = normalized["description"].strip()
        else:
            normalized["service_purpose"] = ""

    if "bounded_context" not in normalized or not isinstance(normalized.get("bounded_context"), str):
        normalized["bounded_context"] = ""

    if "service_type" not in normalized or not isinstance(normalized.get("service_type"), str):
        normalized["service_type"] = ""

    normalized["internal_components"] = _normalize_components(
        normalized.get("internal_components", [])
    )

    for field in [
        "data_owned",
        "consumed_events",
        "emitted_events",
        "external_integrations",
        "security_controls",
        "observability",
        "open_questions",
    ]:
        normalized[field] = _normalize_string_list(normalized.get(field, []))

    if "confidence" not in normalized or not isinstance(normalized.get("confidence"), str):
        normalized["confidence"] = "medium"

    return normalized


def _normalize_components(components: list) -> list[dict]:
    normalized_components: list[dict] = []

    for component in components:
        if not isinstance(component, dict):
            continue

        name = str(component.get("name", "")).strip()
        comp_type = str(component.get("type", "")).strip()
        responsibility = _extract_responsibility(component)

        normalized_components.append(
            {
                "name": name,
                "type": comp_type,
                "responsibility": responsibility,
            }
        )

    return normalized_components


def _extract_responsibility(component: dict) -> str:
    if "responsibility" in component:
        value = component.get("responsibility", "")
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            return "; ".join(
                item.strip() for item in value if isinstance(item, str) and item.strip()
            )

    if "responsibilities" in component:
        value = component.get("responsibilities", [])
        if isinstance(value, list):
            return "; ".join(
                item.strip() for item in value if isinstance(item, str) and item.strip()
            )
        if isinstance(value, str):
            return value.strip()

    if "description" in component and isinstance(component["description"], str):
        return component["description"].strip()

    if "purpose" in component and isinstance(component["purpose"], str):
        return component["purpose"].strip()

    return ""


def _normalize_string_list(values) -> list[str]:
    if not isinstance(values, list):
        return []

    result: list[str] = []
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                result.append(stripped)
    return result