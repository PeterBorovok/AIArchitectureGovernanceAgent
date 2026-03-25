from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


MOCKS_DIR = Path(__file__).resolve().parent / "mocks"


def load_mock_response(service_name: str) -> Dict[str, Any]:
    path = MOCKS_DIR / f"{service_name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    return _generic_service_mock(service_name)


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
                "responsibility": f"Exposes {base_name.lower()} commands and queries"
            },
            {
                "name": f"{base_name} Application Service",
                "type": "application",
                "responsibility": f"Coordinates {base_name.lower()} use cases"
            },
            {
                "name": f"{base_name} Domain Service",
                "type": "domain",
                "responsibility": f"Applies business rules for {base_name.lower()}"
            },
            {
                "name": f"{base_name} Repository",
                "type": "persistence",
                "responsibility": f"Persists {base_name.lower()} data"
            },
            {
                "name": f"{base_name} Event Publisher",
                "type": "messaging",
                "responsibility": f"Publishes {base_name.lower()} lifecycle events"
            }
        ],
        "data_owned": [
            f"{base_name} records"
        ],
        "consumed_events": [],
        "emitted_events": [],
        "external_integrations": [],
        "security_controls": [
            "Authorization checks",
            "Audit trail"
        ],
        "observability": [
            "Structured logs",
            "Metrics",
            "Tracing"
        ],
        "open_questions": [],
        "confidence": "medium"
    }