from __future__ import annotations

import json
from pathlib import Path

from src.agent_state import AgentState
from src.config import PORTFOLIO_DIR
from src.prompt_loader import load_prompt_template


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

    (service_dir / "service.json").write_text(
        json.dumps(normalized_proposal, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    events_doc = {
        "service_name": service_name,
        "consumed_events": normalized_proposal.get("consumed_events", []),
        "emitted_events": normalized_proposal.get("emitted_events", []),
    }
    (service_dir / "events.json").write_text(
        json.dumps(events_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    design_md = _build_design_markdown(normalized_proposal)
    (service_dir / "design.md").write_text(design_md, encoding="utf-8")

    if service_name not in state.approved_services:
        state.approved_services.append(service_name)

    return state


def _build_design_markdown(proposal: dict) -> str:
    template = _load_design_doc_template()

    return template.format(
        service_name=proposal.get("service_name", ""),
        service_purpose=proposal.get("service_purpose", ""),
        bounded_context=proposal.get("bounded_context", ""),
        service_type=proposal.get("service_type", ""),
        internal_components=_format_internal_components(proposal.get("internal_components", [])),
        data_owned=_format_bullet_list(proposal.get("data_owned", [])),
        consumed_events=_format_bullet_list(proposal.get("consumed_events", [])),
        emitted_events=_format_bullet_list(proposal.get("emitted_events", [])),
        external_integrations=_format_bullet_list(proposal.get("external_integrations", [])),
        security_controls=_format_bullet_list(proposal.get("security_controls", [])),
        observability=_format_bullet_list(proposal.get("observability", [])),
        open_questions=_format_bullet_list(proposal.get("open_questions", []), empty_text="- None"),
        confidence=proposal.get("confidence", ""),
    )


def _load_design_doc_template() -> str:
    try:
        return load_prompt_template("service_design_doc_template.md")
    except FileNotFoundError:
        return _default_design_doc_template()


def _default_design_doc_template() -> str:
    return """# {service_name}

## Purpose
{service_purpose}

## Bounded Context
{bounded_context}

## Service Type
{service_type}

## Internal Components
{internal_components}

## Data Owned
{data_owned}

## Consumed Events
{consumed_events}

## Emitted Events
{emitted_events}

## External Integrations
{external_integrations}

## Security Controls
{security_controls}

## Observability
{observability}

## Open Questions
{open_questions}

## Confidence
{confidence}
"""


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


def _format_internal_components(components: list[dict]) -> str:
    if not components:
        return "- None"

    lines = []
    for component in components:
        lines.append(
            f"- **{component.get('name', '')}** "
            f"({component.get('type', '')}): "
            f"{component.get('responsibility', '')}"
        )
    return "\n".join(lines)


def _format_bullet_list(values: list[str], empty_text: str = "- None") -> str:
    if not values:
        return empty_text
    return "\n".join(f"- {value}" for value in values)


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