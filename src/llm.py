from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def generate_structured_service_design(
    prompt: str,
    schema: Dict[str, Any],
    mock: bool = True,
) -> Dict[str, Any]:

    print(f"Mock indicator is => {mock}")

    if mock:
        # keep your existing mock logic here
        service_name = _extract_service_name_from_prompt(prompt)
        return _generic_service_mock(service_name)

    # ============================
    # REAL OPENAI CALL
    # ============================

    response = client.responses.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        # response_format={
        #     "type": "json_schema",
        #     "json_schema": {
        #         "name": "service_design",
        #         "schema": schema
        #     }
        # },
        input=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect designing microservices. "
                    "Follow the schema strictly. "
                    "Do not invent unrelated domain concepts. "
                    "Stay consistent with the service name and bounded context."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # Extract structured JSON safely
    try:
        return response.output[0].content[0].parsed
    except Exception:
        # fallback if parsing fails
        raw_text = response.output[0].content[0].text
        return json.loads(raw_text)


def _extract_service_name_from_prompt(prompt: str) -> str:
    marker = "Design exactly one service:"
    if marker not in prompt:
        return "Unknown Service"

    after = prompt.split(marker, 1)[1].strip()
    first_line = after.splitlines()[0].strip()
    return first_line or "Unknown Service"


def _generic_service_mock(service_name: str) -> Dict[str, Any]:
    base_name = service_name.replace(" Service", "").strip()

    return {
        "service_name": service_name,
        "service_purpose": f"Provides {base_name.lower()} capabilities according to the platform baseline.",
        "bounded_context": base_name,
        "service_type": "domain_service",
        "internal_components": [
            {
                "name": f"{base_name} API",
                "type": "api",
                "responsibility": f"Expose {base_name.lower()} commands and queries"
            },
            {
                "name": f"{base_name} Application Service",
                "type": "application",
                "responsibility": f"Coordinate {base_name.lower()} use cases"
            },
            {
                "name": f"{base_name} Domain Service",
                "type": "domain",
                "responsibility": f"Apply business rules"
            },
            {
                "name": f"{base_name} Repository",
                "type": "persistence",
                "responsibility": f"Persist data"
            },
            {
                "name": f"{base_name} Event Publisher",
                "type": "messaging",
                "responsibility": f"Publish events"
            }
        ],
        "data_owned": [f"{base_name} data"],
        "consumed_events": [],
        "emitted_events": [],
        "external_integrations": [],
        "security_controls": ["Authorization"],
        "observability": ["Logs", "Metrics"],
        "open_questions": [],
        "confidence": "medium"
    }