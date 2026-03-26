from __future__ import annotations

from src.agent_state import AgentState


DEFAULT_REQUIRED_COMPONENT_TYPES = {"api", "application", "domain", "persistence", "messaging"}


def run(state: AgentState) -> AgentState:
    proposal = _normalize_proposal(state.current_proposal or {})
    baseline = state.current_baseline_service or {}
    extracted = state.current_extracted_service or {}

    issues: list[str] = []
    warnings: list[str] = []

    service_name = proposal.get("service_name", "").strip()
    baseline_name = str(baseline.get("name", "")).strip()

    if service_name != baseline_name:
        issues.append("Proposal service_name does not match baseline service name")

    components = proposal.get("internal_components", [])
    component_types = {c.get("type") for c in components if c.get("type")}

    required_types = _get_required_component_types(state)
    missing_types = required_types - component_types
    if missing_types:
        issues.append(f"Missing required component types: {sorted(missing_types)}")

    for idx, component in enumerate(components):
        if not component.get("name", "").strip():
            issues.append(f"internal_components[{idx}] is missing 'name'")
        if not component.get("type", "").strip():
            issues.append(f"internal_components[{idx}] is missing 'type'")
        if not component.get("responsibility", "").strip():
            issues.append(f"internal_components[{idx}] is missing 'responsibility'")

    baseline_emits = set(_normalize_string_list(baseline.get("emits", [])))
    extracted_emits = set(_normalize_string_list(extracted.get("emits", [])))
    proposal_emits = set(_normalize_string_list(proposal.get("emitted_events", [])))

    missing_baseline_emits = baseline_emits - proposal_emits
    if missing_baseline_emits:
        issues.append(f"Missing baseline emitted events: {sorted(missing_baseline_emits)}")

    missing_extracted_emits = extracted_emits - proposal_emits
    if missing_extracted_emits:
        warnings.append(f"Proposal is missing extracted emitted events: {sorted(missing_extracted_emits)}")

    baseline_consumes = set(_normalize_string_list(baseline.get("consumes", [])))
    extracted_consumes = set(_normalize_string_list(extracted.get("consumes", [])))
    proposal_consumes = set(_normalize_string_list(proposal.get("consumed_events", [])))

    missing_baseline_consumes = baseline_consumes - proposal_consumes
    if missing_baseline_consumes:
        warnings.append(f"Missing baseline consumed events: {sorted(missing_baseline_consumes)}")

    missing_extracted_consumes = extracted_consumes - proposal_consumes
    if missing_extracted_consumes:
        warnings.append(f"Proposal is missing extracted consumed events: {sorted(missing_extracted_consumes)}")

    service_purpose = proposal.get("service_purpose", "").strip()
    if not service_purpose:
        issues.append("Proposal service_purpose is empty")

    baseline_desc = str(baseline.get("description", "")).strip()
    extracted_desc = str(extracted.get("description", "")).strip()

    if baseline_desc and not _looks_semantically_present(baseline_desc, service_purpose):
        warnings.append("Proposal service_purpose may not reflect baseline description closely enough")

    if extracted_desc and not _looks_semantically_present(extracted_desc, service_purpose):
        warnings.append("Proposal service_purpose may not reflect extracted description closely enough")

    bounded_context = proposal.get("bounded_context", "").strip()
    component_names = " | ".join(c.get("name", "") for c in components).lower()
    data_owned_text = " | ".join(
        item.get("entity_name", "") for item in proposal.get("data_owned", [])
    ).lower()
    purpose_text = service_purpose.lower()

    if service_name == "Process Definition Service":
        forbidden_doc_markers = ["document", "documents", "attachment", "attachments"]
        if any(marker in purpose_text for marker in forbidden_doc_markers):
            issues.append("Process Definition Service proposal contains document-oriented purpose text")
        if any(marker in bounded_context.lower() for marker in forbidden_doc_markers):
            issues.append("Process Definition Service proposal has document-oriented bounded context")
        if any(marker in component_names for marker in forbidden_doc_markers):
            issues.append("Process Definition Service proposal contains document-oriented internal component names")
        if any(marker in data_owned_text for marker in forbidden_doc_markers):
            issues.append("Process Definition Service proposal contains document-oriented owned data")

    if service_name == "RequestSubmission Service":
        forbidden_doc_markers = ["document", "documents"]
        if any(marker in purpose_text for marker in forbidden_doc_markers):
            issues.append("RequestSubmission Service proposal contains document-oriented purpose text")
        if any(marker in bounded_context.lower() for marker in forbidden_doc_markers):
            issues.append("RequestSubmission Service proposal has document-oriented bounded context")
        if any(marker in component_names for marker in forbidden_doc_markers):
            issues.append("RequestSubmission Service proposal contains document-oriented internal component names")
        if any(marker in data_owned_text for marker in forbidden_doc_markers):
            issues.append("RequestSubmission Service proposal contains document-oriented owned data")

    _validate_data_owned(proposal, issues, warnings)

    if not proposal.get("emitted_events") and not proposal.get("consumed_events"):
        warnings.append("Proposal has no emitted or consumed events")

    state.current_proposal = proposal
    state.current_validation = {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }
    return state


def _normalize_proposal(proposal: dict) -> dict:
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


def _normalize_data_owned(values) -> list[dict]:
    if not isinstance(values, list):
        return []

    normalized: list[dict] = []
    for item in values:
        if isinstance(item, dict):
            entity_name = str(item.get("entity_name") or item.get("name") or "").strip()
            description = str(item.get("description") or "").strip()
            storage_type = str(item.get("storage_type") or item.get("storage") or "").strip()

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


def _validate_data_owned(proposal: dict, issues: list[str], warnings: list[str]) -> None:
    data_owned = proposal.get("data_owned", [])

    if not data_owned:
        issues.append("Service must declare owned data entities")
        return

    for idx, item in enumerate(data_owned):
        entity_name = item.get("entity_name", "").strip()
        description = item.get("description", "").strip()
        storage_type = item.get("storage_type", "").strip()

        if not entity_name:
            issues.append(f"data_owned[{idx}] is missing 'entity_name'")
        if not description:
            issues.append(f"data_owned[{idx}] is missing 'description'")
        if not storage_type:
            issues.append(f"data_owned[{idx}] is missing 'storage_type'")

    if len(data_owned) == 1:
        warnings.append("Proposal declares only one owned data entity")


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


def _get_required_component_types(state: AgentState) -> set[str]:
    template_required = state.service_template.get("required_component_types", [])
    if template_required:
        return {
            item.strip()
            for item in template_required
            if isinstance(item, str) and item.strip()
        }
    return DEFAULT_REQUIRED_COMPONENT_TYPES


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


def _looks_semantically_present(reference_text: str, proposal_text: str) -> bool:
    reference_tokens = {
        token.lower()
        for token in reference_text.replace(",", " ").replace(".", " ").split()
        if len(token.strip()) > 4
    }
    proposal_tokens = {
        token.lower()
        for token in proposal_text.replace(",", " ").replace(".", " ").split()
        if len(token.strip()) > 4
    }

    if not reference_tokens:
        return True

    overlap = reference_tokens.intersection(proposal_tokens)
    return len(overlap) >= min(3, len(reference_tokens))