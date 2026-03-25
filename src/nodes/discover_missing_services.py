from __future__ import annotations

import json
from pathlib import Path

from src.agent_state import AgentState


DISCOVERY_RULES_FILE = Path(__file__).resolve().parent.parent / "prompts" / "discovery_rules.json"


def run(state: AgentState) -> AgentState:
    rules = _load_discovery_rules()

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

    include_contract_mismatch = rules.get("include_contract_mismatch", True)
    include_missing_internal_design = rules.get("include_missing_internal_design", True)
    include_missing_from_top_level = rules.get("include_missing_from_top_level", True)
    queue_order = rules.get(
        "queue_order",
        ["missing_from_top_level", "missing_internal_design", "contract_mismatch"],
    )

    categorized_candidates: dict[str, list[dict]] = {
        "missing_from_top_level": [],
        "missing_internal_design": [],
        "contract_mismatch": [],
        "aligned": [],
    }

    for baseline in baseline_services:
        name = baseline["name"]
        extracted = extracted_by_name.get(name)

        if extracted is None:
            if include_missing_from_top_level:
                item = {
                    "name": name,
                    "reason": "Defined in baseline but missing from extracted top-level architecture",
                    "baseline": baseline,
                    "category": "missing_from_top_level",
                }
                state.missing_services.append(item)
                state.candidate_services.append(item)
                categorized_candidates["missing_from_top_level"].append(item)
            continue

        if baseline.get("expected_internal_design", False) and not extracted.get("internal_defined", False):
            item = {
                "name": name,
                "reason": "Service exists in extracted architecture but internal design is not defined",
                "baseline": baseline,
                "extracted": extracted,
                "category": "missing_internal_design",
            }
            state.services_needing_internal_design.append(item)
            if include_missing_internal_design:
                state.candidate_services.append(item)
                categorized_candidates["missing_internal_design"].append(item)

        mismatch = _detect_contract_mismatch(baseline, extracted)
        if mismatch:
            item = {
                "name": name,
                "reason": "Baseline and extracted service contract do not fully match",
                "baseline": baseline,
                "extracted": extracted,
                "mismatches": mismatch,
                "category": "contract_mismatch",
            }
            state.services_with_contract_mismatch.append(item)
            if include_contract_mismatch:
                state.candidate_services.append(item)
                categorized_candidates["contract_mismatch"].append(item)
        else:
            categorized_candidates["aligned"].append(
                {
                    "name": name,
                    "reason": "Baseline and extracted service are aligned",
                    "baseline": baseline,
                    "extracted": extracted,
                    "category": "aligned",
                }
            )

    queue: list[str] = []
    seen: set[str] = set()

    for category in queue_order:
        for item in categorized_candidates.get(category, []):
            name = item["name"]
            if name not in seen:
                queue.append(name)
                seen.add(name)

    state.design_queue = queue
    return state


def _load_discovery_rules() -> dict:
    if not DISCOVERY_RULES_FILE.exists():
        return {
            "include_contract_mismatch": True,
            "include_missing_internal_design": True,
            "include_missing_from_top_level": True,
            "queue_order": [
                "missing_from_top_level",
                "missing_internal_design",
                "contract_mismatch",
            ],
        }

    try:
        return json.loads(DISCOVERY_RULES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "include_contract_mismatch": True,
            "include_missing_internal_design": True,
            "include_missing_from_top_level": True,
            "queue_order": [
                "missing_from_top_level",
                "missing_internal_design",
                "contract_mismatch",
            ],
        }


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