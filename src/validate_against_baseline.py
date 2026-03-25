from pathlib import Path
import json
import re

BASELINE_FILE = Path("output/baseline_manifest.json")
DETAILED_FILE = Path("output/architecture_manifest.json")
OUTPUT_FILE = Path("output/baseline_validation_report.json")


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def service_index(services: list[dict]) -> dict:
    index = {}
    for service in services:
        name = service.get("name", "").strip()
        if not name:
            continue
        index[normalize_name(name)] = service
    return index


def compare_events(expected: list[str], actual: list[str]) -> dict:
    expected_norm = {normalize_name(x): x for x in expected}
    actual_norm = {normalize_name(x): x for x in actual}

    missing = [expected_norm[k] for k in expected_norm.keys() if k not in actual_norm]
    extra = [actual_norm[k] for k in actual_norm.keys() if k not in expected_norm]

    return {
        "missing": missing,
        "extra": extra,
    }


def main():
    baseline = load_json(BASELINE_FILE)
    detailed = load_json(DETAILED_FILE)

    baseline_services = baseline.get("services", [])
    detailed_services = detailed.get("services", [])

    baseline_index = service_index(baseline_services)
    detailed_index = service_index(detailed_services)

    expected_service_names = set(baseline_index.keys())
    actual_service_names = set(detailed_index.keys())

    found_services = []
    missing_services = []
    extra_services = []

    for service_name in sorted(expected_service_names):
        if service_name in actual_service_names:
            baseline_service = baseline_index[service_name]
            detailed_service = detailed_index[service_name]

            emits_comparison = compare_events(
                baseline_service.get("emits", []),
                detailed_service.get("emits", [])
            )

            consumes_comparison = compare_events(
                baseline_service.get("consumes", []),
                detailed_service.get("consumes", [])
            )

            found_services.append({
                "service_name": baseline_service.get("name"),
                "status": "found",
                "emits": emits_comparison,
                "consumes": consumes_comparison,
            })
        else:
            missing_services.append(baseline_index[service_name].get("name"))

    for service_name in sorted(actual_service_names):
        if service_name not in expected_service_names:
            extra_services.append(detailed_index[service_name].get("name"))

    summary = {
        "expected_services_count": len(expected_service_names),
        "actual_services_count": len(actual_service_names),
        "found_services_count": len(found_services),
        "missing_services_count": len(missing_services),
        "extra_services_count": len(extra_services),
    }

    report = {
        "summary": summary,
        "found_services": found_services,
        "missing_services": missing_services,
        "extra_services": extra_services,
    }

    OUTPUT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved validation report to: {OUTPUT_FILE}")
    print("\nSummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\nMissing services:")
    for service in missing_services:
        print(f"- {service}")

    print("\nExtra services:")
    for service in extra_services:
        print(f"- {service}")

    print("\nFound services:")
    for item in found_services:
        print(f"- {item['service_name']}")


if __name__ == "__main__":
    main()