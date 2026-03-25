from pathlib import Path
import json
import re

EXPECTATIONS_FILE = Path("output/internal_expectations.json")
DETAILED_INTERNAL_FILE = Path("output/detailed_internal_manifest.json")
OUTPUT_FILE = Path("output/internal_validation_report.json")


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def build_expected_index(expectations: list[dict]) -> dict:
    index = {}
    for item in expectations:
        service_name = item.get("service_name", "").strip()
        if service_name:
            index[normalize(service_name)] = item
    return index


def build_actual_index(services: list[dict]) -> dict:
    index = {}
    for item in services:
        service_name = item.get("service_name", "").strip()
        if service_name:
            index[normalize(service_name)] = item
    return index


def compare_components(expected_components: list[dict], actual_components: list[dict]) -> dict:
    expected_required = [
        c for c in expected_components
        if c.get("required", False)
    ]

    expected_names = {normalize(c["name"]): c for c in expected_required if c.get("name")}
    actual_names = {normalize(c["name"]): c for c in actual_components if c.get("name")}

    missing = [expected_names[k]["name"] for k in expected_names if k not in actual_names]
    extra = [actual_names[k]["name"] for k in actual_names if k not in expected_names]

    return {
        "missing_required_components": missing,
        "extra_components": extra,
        "required_count": len(expected_required),
        "actual_count": len(actual_components),
    }


def main():
    expectations_doc = load_json(EXPECTATIONS_FILE)
    detailed_doc = load_json(DETAILED_INTERNAL_FILE)

    expected_services = expectations_doc.get("service_expectations", [])
    actual_services = detailed_doc.get("services", [])

    expected_index = build_expected_index(expected_services)
    actual_index = build_actual_index(actual_services)

    service_reports = []
    missing_service_manifests = []
    extra_service_manifests = []

    for service_key, expected in expected_index.items():
        service_name = expected.get("service_name", "")
        actual = actual_index.get(service_key)

        if not actual:
            missing_service_manifests.append(service_name)
            continue

        comparison = compare_components(
            expected.get("expected_internal_components", []),
            actual.get("internal_components", []),
        )

        service_reports.append({
            "service_name": service_name,
            "status": "validated",
            "missing_required_components": comparison["missing_required_components"],
            "extra_components": comparison["extra_components"],
            "required_count": comparison["required_count"],
            "actual_count": comparison["actual_count"],
        })

    for service_key, actual in actual_index.items():
        if service_key not in expected_index:
            extra_service_manifests.append(actual.get("service_name", ""))

    summary = {
        "expected_service_count": len(expected_index),
        "actual_service_count": len(actual_index),
        "validated_service_count": len(service_reports),
        "missing_service_manifests_count": len(missing_service_manifests),
        "extra_service_manifests_count": len(extra_service_manifests),
    }

    report = {
        "summary": summary,
        "service_reports": service_reports,
        "missing_service_manifests": missing_service_manifests,
        "extra_service_manifests": extra_service_manifests,
    }

    OUTPUT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved internal validation report to: {OUTPUT_FILE}")
    print("\nSummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\nMissing service manifests:")
    for name in missing_service_manifests:
        print(f"- {name}")

    print("\nExtra service manifests:")
    for name in extra_service_manifests:
        print(f"- {name}")

    print("\nValidated services:")
    for item in service_reports:
        print(f"- {item['service_name']}: missing={item['missing_required_components']}")
    

if __name__ == "__main__":
    main()