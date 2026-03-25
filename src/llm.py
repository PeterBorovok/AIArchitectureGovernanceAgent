from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.mock_loader import load_mock_response

client = OpenAI(api_key=OPENAI_API_KEY)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def generate_structured_service_design(
    input_data,
    system_prompt,
    user_prompt,
    mock=False,
    feedback=None,
    previous_proposal=None,
) -> Dict[str, Any]:
    print(
        "DEBUG llm input_data keys:",
        list(input_data.keys()) if isinstance(input_data, dict) else type(input_data),
    )
    print("DEBUG llm feedback:", feedback or "")
    print("DEBUG llm previous_proposal exists:", bool(previous_proposal))
    print("DEBUG llm user_prompt length:", len(user_prompt))
    print("DEBUG llm system_prompt length:", len(system_prompt))

    if mock:
        service_name = _extract_service_name_from_input(input_data)
        mock_response = load_mock_response(service_name)
        if mock_response:
            return mock_response
        return _generic_service_mock(service_name)

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    raw_text = _extract_text_response(response)
    return _parse_json_response(raw_text)


def _extract_text_response(response: Any) -> str:
    try:
        parts = []
        for item in response.output:
            for content in item.content:
                if getattr(content, "type", None) == "output_text":
                    parts.append(content.text)
        if parts:
            return "\n".join(parts).strip()
    except Exception:
        pass

    try:
        return response.output[0].content[0].text.strip()
    except Exception as exc:
        raise ValueError(f"Could not extract text from OpenAI response: {exc}") from exc


def _parse_json_response(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if len(lines) >= 3:
            raw_text = "\n".join(lines[1:-1]).strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Model response is not valid JSON. "
            f"Raw response was:\n{raw_text}"
        ) from exc


def _extract_service_name_from_input(input_data: Any) -> str:
    if isinstance(input_data, dict):
        service_name = input_data.get("service_name")
        if isinstance(service_name, str) and service_name.strip():
            return service_name.strip()
    return "Unknown Service"


def _generic_service_mock(service_name: str) -> Dict[str, Any]:
    base_name = service_name.replace(" Service", "").strip()

    return {
        "service_name": service_name,
        "service_purpose": f"Provides {base_name.lower()} capabilities according to the platform baseline and service template.",
        "bounded_context": base_name,
        "service_type": "domain_service",
        "internal_components": [
            {
                "name": f"{base_name} API",
                "type": "api",
                "responsibility": f"Exposes {base_name.lower()} commands and queries",
            },
            {
                "name": f"{base_name} Application Service",
                "type": "application",
                "responsibility": f"Coordinates {base_name.lower()} use cases",
            },
            {
                "name": f"{base_name} Domain Service",
                "type": "domain",
                "responsibility": f"Applies business rules for {base_name.lower()}",
            },
            {
                "name": f"{base_name} Repository",
                "type": "persistence",
                "responsibility": f"Persists {base_name.lower()} data",
            },
            {
                "name": f"{base_name} Event Publisher",
                "type": "messaging",
                "responsibility": f"Publishes {base_name.lower()} lifecycle events",
            },
        ],
        "data_owned": [
            {
                "entity_name": base_name,
                "description": f"Primary {base_name.lower()} records owned by the service",
                "storage_type": "Aurora",
            }
        ],
        "consumed_events": [],
        "emitted_events": [],
        "external_integrations": [],
        "security_controls": [
            "Authorization checks",
            "Audit trail",
        ],
        "observability": [
            "Structured logs",
            "Metrics",
            "Tracing",
        ],
        "open_questions": [],
        "confidence": "medium",
    }