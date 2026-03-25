from __future__ import annotations

from src.agent_state import AgentState


def run(state: AgentState) -> AgentState:
    baseline_services = state.baseline_services
    extracted_services = state.extracted_top_level_architecture.get("services", [])

    extracted_by_name = {
        svc["name"]: svc for svc in extracted_services if "name" in svc
    }

    state.existing_services = extracted_services
    state.missing_services = []
    state.services_needing_internal_design = []
    state.services_with_contract_mismatch = []
    state.candidate_services = []
    state.design_queue = []

    for baseline in baseline_services:
        name = baseline["name"]
        extracted = extracted_by_name.get(name)

        if extracted is None:
            state.missing_services.append(
                {
                    "name": name,
                    "reason": "Defined in baseline but missing from extracted top-level architecture",
                    "baseline": baseline,
                }
            )
            state.candidate_services.append(
                {
                    "name": name,
                    "reason": "missing_from_top_level",
                    "baseline": baseline,
                }
            )
            state.design_queue.append(name)
            continue

        if baseline.get("expected_internal_design", False) and not extracted.get("internal_defined", False):
            state.services_needing_internal_design.append(
                {
                    "name": name,
                    "reason": "Service exists in extracted architecture but internal design is not defined",
                    "baseline": baseline,
                    "extracted": extracted,
                }
            )
            if name not in state.design_queue:
                state.design_queue.append(name)

        mismatch = _detect_contract_mismatch(baseline, extracted)
        if mismatch:
            state.services_with_contract_mismatch.append(
                {
                    "name": name,
                    "reason": "Baseline and extracted service contract do not fully match",
                    "baseline": baseline,
                    "extracted": extracted,
                    "mismatches": mismatch,
                }
            )
            state.candidate_services.append(
                {
                    "name": name,
                    "reason": "contract_mismatch",
                    "baseline": baseline,
                    "extracted": extracted,
                    "mismatches": mismatch,
                }
            )
            if name not in state.design_queue:
                state.design_queue.append(name)
        else:
            state.candidate_services.append(
                {
                    "name": name,
                    "reason": "missing_internal_design" if not extracted.get("internal_defined", False) else "aligned",
                    "baseline": baseline,
                    "extracted": extracted,
                }
            )

    return state


def _detect_contract_mismatch(baseline: dict, extracted: dict) -> dict:
    mismatches = {}

    baseline_emits = set(_normalize_list(baseline.get("emits", [])))
    extracted_emits = set(_normalize_list(extracted.get("emits", [])))
    missing_emits_in_extracted = baseline_emits - extracted_emits
    extra_emits_in_extracted = extracted_emits - baseline_emits

    if missing_emits_in_extracted:
        mismatches["missing_emits_in_extracted"] = sorted(missing_emits_in_extracted)
    if extra_emits_in_extracted:
        mismatches["extra_emits_in_extracted"] = sorted(extra_emits_in_extracted)

    baseline_consumes = set(_normalize_list(baseline.get("consumes", [])))
    extracted_consumes = set(_normalize_list(extracted.get("consumes", [])))
    missing_consumes_in_extracted = baseline_consumes - extracted_consumes
    extra_consumes_in_extracted = extracted_consumes - baseline_consumes

    if missing_consumes_in_extracted:
        mismatches["missing_consumes_in_extracted"] = sorted(missing_consumes_in_extracted)
    if extra_consumes_in_extracted:
        mismatches["extra_consumes_in_extracted"] = sorted(extra_consumes_in_extracted)

    baseline_desc = (baseline.get("description") or "").strip()
    extracted_desc = (extracted.get("description") or "").strip()
    if baseline_desc and extracted_desc and baseline_desc != extracted_desc:
        mismatches["description_drift"] = {
            "baseline": baseline_desc,
            "extracted": extracted_desc,
        }

    return mismatches


def _normalize_list(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                result.append(stripped)
    return result