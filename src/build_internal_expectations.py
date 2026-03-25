from pathlib import Path
import json

BASELINE_FILE = Path("output/baseline_manifest.json")
OUTPUT_FILE = Path("output/internal_expectations.json")


DEFAULT_INTERNAL_TEMPLATE = [
    {"name": "API Layer", "type": "api", "required": True},
    {"name": "Application Layer", "type": "application", "required": True},
    {"name": "Domain Layer", "type": "domain", "required": True},
    {"name": "Persistence Layer", "type": "persistence", "required": True},
    {"name": "Event Publisher", "type": "messaging", "required": True},
    {"name": "Event Consumer", "type": "messaging", "required": True},
    {"name": "Audit / Logging", "type": "audit", "required": True},
    {"name": "Observability", "type": "observability", "required": True},
]


SPECIALIZED_RULES = {
    "Notification Service": [
        {"name": "Notification Dispatcher", "type": "integration", "required": True},
        {"name": "SendGrid Adapter", "type": "integration", "required": True},
    ],
    "Scanning System Service (separate account)": [
        {"name": "Scan Orchestrator", "type": "application", "required": True},
        {"name": "Scanning Worker", "type": "worker", "required": True},
        {"name": "OPSWAT Adapter", "type": "integration", "required": True},
    ],
    "Attachment and Scanning Service": [
        {"name": "Upload URL Generator", "type": "application", "required": True},
        {"name": "Attachment Tracker", "type": "domain", "required": True},
        {"name": "Scan Result Handler", "type": "application", "required": True},
    ],
    "Approval Workflow Service": [
        {"name": "Workflow Orchestrator", "type": "application", "required": True},
        {"name": "Step State Manager", "type": "domain", "required": True},
    ],
    "Airs - AI Reponse Service": [
        {"name": "Prompt Builder", "type": "application", "required": True},
        {"name": "Context Retriever", "type": "integration", "required": True},
        {"name": "Policy / Guardrails Module", "type": "domain", "required": True},
        {"name": "LLM Adapter", "type": "integration", "required": True},
    ],
    "Document Service": [
        {"name": "Document Registry", "type": "domain", "required": True},
        {"name": "Version Manager", "type": "domain", "required": True},
        {"name": "Storage Adapter", "type": "integration", "required": True},
    ],
    "Shared Data Service": [
        {"name": "Reference Data Manager", "type": "domain", "required": True},
    ],
    "Task Service": [
        {"name": "Task Assignment Engine", "type": "domain", "required": True},
        {"name": "Task Query Handler", "type": "application", "required": True},
    ],
}


def load_baseline() -> dict:
    if not BASELINE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {BASELINE_FILE}")
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


def dedupe_components(components: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for component in components:
        key = (component["name"], component["type"])
        if key not in seen:
            seen.add(key)
            result.append(component)
    return result


def build_service_expectation(service: dict) -> dict:
    service_name = service.get("name", "")
    components = list(DEFAULT_INTERNAL_TEMPLATE)

    if service_name in SPECIALIZED_RULES:
        components.extend(SPECIALIZED_RULES[service_name])

    components = dedupe_components(components)

    return {
        "service_name": service_name,
        "description": service.get("description", ""),
        "emits": service.get("emits", []),
        "consumes": service.get("consumes", []),
        "expected_internal_components": components,
    }


def main():
    baseline = load_baseline()
    services = baseline.get("services", [])

    expectations = [build_service_expectation(service) for service in services]

    output = {
        "platform_name": baseline.get("platform_name", "Moin Platform"),
        "source_file": baseline.get("source_file", ""),
        "services_count": len(expectations),
        "service_expectations": expectations,
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved internal expectations to: {OUTPUT_FILE}")
    print(f"\nServices processed: {len(expectations)}")
    print("\nService expectations created for:")
    for item in expectations:
        print(f"- {item['service_name']}")


if __name__ == "__main__":
    main()