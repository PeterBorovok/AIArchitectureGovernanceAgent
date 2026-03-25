from __future__ import annotations

import json

from src.agent_state import AgentState
from src.llm import generate_structured_service_design, load_schema
from src.config import SCHEMAS_DIR


def build_prompt(state: AgentState) -> str:
    current_service = state.current_service or "UNKNOWN SERVICE"
    baseline_service = state.current_baseline_service or {}
    extracted_service = state.current_extracted_service or {}

    adr_summary = _compact_adr_summary(state.adr_summaries)
    guidance_summary = _compact_guidance_summary(state.guidance)
    template_summary = _compact_template_summary(state.service_template)

    approved_service_names = state.approved_services[:20]

    edit_comment = ""
    if state.last_decision and state.last_decision.get("action") == "edit":
        edit_comment = state.last_decision.get("comment", "").strip()

    edit_block = ""
    if edit_comment:
        edit_block = f"""
Reviewer feedback for this regeneration:
{edit_comment}

You must incorporate this reviewer feedback explicitly.
If the feedback asks to refine service purpose, owned data, responsibilities, versioning, or integrations, update the proposal accordingly.
Do not ignore the reviewer feedback.
""".strip()

    return f"""
You are an enterprise architecture design agent.

Design exactly one service:
{current_service}

Use the baseline service definition as the primary source of truth.
Use the extracted service as current-state context only.

Rules:
- Respect ADR and guidance constraints.
- Follow the microservice template.
- Preserve the service responsibility from the baseline.
- Preserve baseline emitted and consumed events unless there is a strong architectural reason to add candidates as open questions.
- Do not redesign the full platform.
- Return only valid JSON matching the schema.
- bounded_context must not be empty.
- service_type must not be empty.
- data_owned must not be empty unless there is a strong and explicit justification.
- each internal component must include a non-empty responsibility.
- security_controls should include at least basic access control and auditability.
- observability should include logs, metrics, and tracing where relevant.

Baseline service:
{json.dumps(baseline_service, indent=2)}

Extracted current-state service:
{json.dumps(extracted_service, indent=2)}

ADR summary:
{json.dumps(adr_summary, indent=2)}

Guidance summary:
{json.dumps(guidance_summary, indent=2)}

Template summary:
{json.dumps(template_summary, indent=2)}

Already approved services:
{json.dumps(approved_service_names, indent=2)}

{edit_block}
""".strip()


def run(state: AgentState) -> AgentState:
    schema = load_schema(SCHEMAS_DIR / "service_design_schema.json")
    prompt = build_prompt(state)

    print("DEBUG prompt length:", len(prompt))
    if state.last_decision and state.last_decision.get("action") == "edit":
        print("DEBUG edit feedback applied:", state.last_decision.get("comment", ""))

    proposal = generate_structured_service_design(
        prompt=prompt,
        schema=schema,
        mock=False,
    )

    proposal = _normalize_service_design(proposal)

    if state.current_service:
        proposal["service_name"] = state.current_service

    baseline = state.current_baseline_service or {}
    extracted = state.current_extracted_service or {}

    proposal["emitted_events"] = _merge_unique_strings(
        baseline.get("emits", []),
        extracted.get("emits", []),
        proposal.get("emitted_events", []),
    )

    proposal["consumed_events"] = _merge_unique_strings(
        baseline.get("consumes", []),
        extracted.get("consumes", []),
        proposal.get("consumed_events", []),
    )

    if not proposal.get("service_purpose"):
        proposal["service_purpose"] = (
            proposal.get("purpose")
            or baseline.get("description")
            or extracted.get("description")
            or ""
        )

    if not proposal.get("bounded_context"):
        proposal["bounded_context"] = baseline.get("name", "").replace(" Service", "").strip()

    if not proposal.get("service_type"):
        proposal["service_type"] = "domain_service"

    state.current_proposal = proposal
    return state


def _normalize_service_design(proposal: dict) -> dict:
    if not isinstance(proposal, dict):
        return {}

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

    if not isinstance(components, list):
        return normalized_components

    for component in components:
        if not isinstance(component, dict):
            continue

        normalized_components.append(
            {
                "name": str(component.get("name", "")).strip(),
                "type": str(component.get("type", "")).strip(),
                "responsibility": _extract_responsibility(component),
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


def _compact_adr_summary(adr_summaries: list[dict]) -> list[dict]:
    compact = []
    for adr in adr_summaries[:8]:
        compact.append({
            "name": adr.get("name", ""),
            "content": _truncate_text(adr.get("content", ""), 600)
        })
    return compact


def _compact_guidance_summary(guidance: dict) -> list[dict]:
    docs = guidance.get("documents", [])
    compact = []
    for doc in docs[:8]:
        compact.append({
            "name": doc.get("name", ""),
            "content": _truncate_text(doc.get("content", ""), 600)
        })
    return compact


def _compact_template_summary(template: dict) -> dict:
    return {
        "required_component_types": template.get("required_component_types", []),
        "documentation_sections": template.get("documentation_sections", []),
    }


def _truncate_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "...[truncated]"


def _merge_unique_strings(*lists: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for values in lists:
        for item in values:
            if not isinstance(item, str):
                continue
            value = item.strip()
            if not value:
                continue
            if value not in seen:
                seen.add(value)
                result.append(value)

    return result


def _normalize_string_list(values) -> list[str]:
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            item = value.strip()
            if item:
                normalized.append(item)
    return normalized