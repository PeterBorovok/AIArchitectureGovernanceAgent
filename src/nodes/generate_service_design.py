from __future__ import annotations

import json
from typing import Any

from src.agent_state import AgentState
from src.llm import generate_structured_service_design
from src.prompt_loader import load_prompt_template


def build_prompt(state: AgentState) -> str:
    current_service = state.current_service or "UNKNOWN SERVICE"
    baseline_service = state.current_baseline_service or {}
    extracted_service = state.current_extracted_service or {}

    adr_summary = _compact_adr_summary(state.adr_summaries)
    guidance_summary = _compact_guidance_summary(state.guidance)
    template_summary = _compact_template_summary(state.service_template)
    approved_service_names = state.approved_services[:20]

    edit_comment = ""
    is_edit = False
    if state.last_decision and state.last_decision.get("action") == "edit":
        edit_comment = state.last_decision.get("comment", "").strip()
        is_edit = bool(edit_comment)

    previous_proposal = state.previous_proposal or state.current_proposal

    template_name = "service_design_edit_prompt.txt" if is_edit else "service_design_prompt.txt"
    template = load_prompt_template(template_name)

    print("DEBUG build_prompt template length:", len(template))
    print("DEBUG build_prompt template name:", template_name)

    formatted_prompt = template.format(
        current_service=current_service,
        baseline_service=json.dumps(baseline_service, indent=2, ensure_ascii=False),
        extracted_service=json.dumps(extracted_service, indent=2, ensure_ascii=False),
        adr_summary=json.dumps(adr_summary, indent=2, ensure_ascii=False),
        guidance_summary=json.dumps(guidance_summary, indent=2, ensure_ascii=False),
        template_summary=json.dumps(template_summary, indent=2, ensure_ascii=False),
        approved_services=json.dumps(approved_service_names, indent=2, ensure_ascii=False),
        edit_comment=edit_comment,
        previous_proposal=json.dumps(previous_proposal, indent=2, ensure_ascii=False)
        if previous_proposal
        else "None",
    )

    print("DEBUG formatted prompt length:", len(formatted_prompt))
    return formatted_prompt


def run(state: AgentState) -> AgentState:
    system_prompt = load_prompt_template("service_design_system_prompt.txt")
    prompt = build_prompt(state)

    print("DEBUG prompt length:", len(prompt))
    if state.last_decision and state.last_decision.get("action") == "edit":
        print("DEBUG edit feedback applied:", state.last_decision.get("comment", ""))

    review_comment = ""
    if state.last_decision and state.last_decision.get("action") == "edit":
        review_comment = state.last_decision.get("comment", "").strip()

    previous_proposal = state.previous_proposal or state.current_proposal

    input_data = {
        "project_name": state.project_name,
        "service_name": state.current_service,
        "baseline_service": state.current_baseline_service or {},
        "extracted_service": state.current_extracted_service or {},
        "adr_summaries": _compact_adr_summary(state.adr_summaries),
        "guidance_summary": _compact_guidance_summary(state.guidance),
        "template_summary": _compact_template_summary(state.service_template),
        "approved_services": state.approved_services[:20],
    }

    proposal = generate_structured_service_design(
        input_data=input_data,
        system_prompt=system_prompt,
        user_prompt=prompt,
        mock=False,
        feedback=review_comment,
        previous_proposal=previous_proposal,
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

    proposal["data_owned"] = _ensure_data_owned(
        proposal=proposal,
        service_name=state.current_service or "",
        baseline_service=baseline,
        extracted_service=extracted,
    )

    print("DEBUG final data_owned:", json.dumps(proposal.get("data_owned", []), indent=2, ensure_ascii=False))

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

    normalized["data_owned"] = _normalize_data_owned(normalized.get("data_owned", []))

    for field in [
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


def _normalize_components(components: list[Any]) -> list[dict]:
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


def _normalize_data_owned(values: Any) -> list[dict]:
    if not isinstance(values, list):
        return []

    normalized: list[dict] = []

    for item in values:
        if isinstance(item, dict):
            entity_name = str(
                item.get("entity_name")
                or item.get("name")
                or item.get("entity")
                or ""
            ).strip()
            description = str(
                item.get("description")
                or item.get("purpose")
                or ""
            ).strip()
            storage_type = str(
                item.get("storage_type")
                or item.get("storage")
                or item.get("db_technology")
                or ""
            ).strip()

            if entity_name or description or storage_type:
                normalized.append(
                    {
                        "entity_name": entity_name,
                        "description": description,
                        "storage_type": storage_type,
                    }
                )

        elif isinstance(item, str):
            value = item.strip()
            if value:
                normalized.append(
                    {
                        "entity_name": value,
                        "description": "",
                        "storage_type": "",
                    }
                )

    return normalized


def _ensure_data_owned(
    proposal: dict,
    service_name: str,
    baseline_service: dict,
    extracted_service: dict,
) -> list[dict]:
    current = _normalize_data_owned(proposal.get("data_owned", []))
    if current:
        return _fill_missing_data_owned_fields(current, service_name)

    candidates = []

    # 1. Strong candidates from known keys
    for source in [baseline_service, extracted_service]:
        for key in ["data_owned", "entities", "domain_entities", "owned_entities", "records"]:
            value = source.get(key, [])
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        candidates.append(item.strip())
                    elif isinstance(item, dict):
                        name = str(
                            item.get("entity_name")
                            or item.get("name")
                            or item.get("entity")
                            or ""
                        ).strip()
                        if name:
                            candidates.append(name)

    # 2. Derive from service name
    if not candidates:
        derived = _derive_entities_from_service_name(service_name)
        candidates.extend(derived)

    # 3. Last-resort default
    if not candidates:
        base_name = (service_name or "Domain").replace(" Service", "").strip() or "Domain"
        candidates = [base_name]

    unique_candidates = []
    seen = set()
    for item in candidates:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique_candidates.append(item)

    result = []
    for entity_name in unique_candidates[:3]:
        result.append(
            {
                "entity_name": entity_name,
                "description": _default_entity_description(entity_name, service_name),
                "storage_type": _suggest_storage_type(service_name, entity_name),
            }
        )

    return result


def _fill_missing_data_owned_fields(data_owned: list[dict], service_name: str) -> list[dict]:
    result = []
    for item in data_owned:
        entity_name = str(item.get("entity_name", "")).strip()
        description = str(item.get("description", "")).strip()
        storage_type = str(item.get("storage_type", "")).strip()

        if not entity_name:
            continue

        if not description:
            description = _default_entity_description(entity_name, service_name)

        if not storage_type:
            storage_type = _suggest_storage_type(service_name, entity_name)

        result.append(
            {
                "entity_name": entity_name,
                "description": description,
                "storage_type": storage_type,
            }
        )

    return result


def _derive_entities_from_service_name(service_name: str) -> list[str]:
    base = (service_name or "").replace(" Service", "").strip()
    if not base:
        return []

    known = {
        "Process Definition": [
            "ProcessDefinition",
            "ProcessSchema",
            "ValidationRuleSet",
        ],
        "Submission": [
            "Submission",
            "SubmissionAttachment",
            "SubmissionStatus",
        ],
        "Request Submission": [
            "RequestSubmission",
            "SubmissionAttachment",
            "SubmissionStatus",
        ],
        "Document": [
            "Document",
            "DocumentVersion",
            "DocumentMetadata",
        ],
        "User Profile": [
            "UserProfile",
            "UserPreference",
        ],
        "Notification": [
            "NotificationTemplate",
            "NotificationDelivery",
        ],
    }

    for key, values in known.items():
        if key.lower() in base.lower():
            return values

    token = "".join(ch for ch in base.title() if ch.isalnum())
    if not token:
        token = "Domain"

    return [token, f"{token}Record"]


def _default_entity_description(entity_name: str, service_name: str) -> str:
    base = (service_name or "the service").replace(" Service", "").strip()
    return f"Primary {entity_name} data owned and managed by the {base} service."


def _suggest_storage_type(service_name: str, entity_name: str) -> str:
    name = f"{service_name} {entity_name}".lower()

    if any(word in name for word in ["event", "log", "audit", "trace"]):
        return "DynamoDB"
    if any(word in name for word in ["schema", "definition", "submission", "document", "profile", "rule"]):
        return "Aurora"
    return "Aurora"


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
        compact.append(
            {
                "name": adr.get("name", ""),
                "content": _truncate_text(adr.get("content", ""), 600),
            }
        )
    return compact


def _compact_guidance_summary(guidance: dict) -> list[dict]:
    docs = guidance.get("documents", [])
    compact = []
    for doc in docs[:8]:
        compact.append(
            {
                "name": doc.get("name", ""),
                "content": _truncate_text(doc.get("content", ""), 600),
            }
        )
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


def _merge_unique_strings(*lists: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for values in lists:
        if not isinstance(values, list):
            continue
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


def _normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            item = value.strip()
            if item:
                normalized.append(item)
    return normalized