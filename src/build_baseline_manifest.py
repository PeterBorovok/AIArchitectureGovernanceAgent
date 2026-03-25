from pathlib import Path
import json

ARCHITECTURE_MANIFEST_FILE = Path("output/architecture_manifest.json")
BASELINE_MANIFEST_FILE = Path("output/baseline_manifest.json")
BASELINE_SUMMARY_FILE = Path("output/baseline_summary.json")
BASELINE_SERVICES_FILE = Path("output/baseline_services.json")


def load_architecture_manifest() -> dict:
    if not ARCHITECTURE_MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Missing file: {ARCHITECTURE_MANIFEST_FILE}")
    return json.loads(ARCHITECTURE_MANIFEST_FILE.read_text(encoding="utf-8"))


def main():
    manifest = load_architecture_manifest()

    services = [
        {
            "name": service.get("name", ""),
            "description": service.get("description", ""),
            "emits": service.get("emits", []),
            "consumes": service.get("consumes", []),
            "expected_internal_design": True,
        }
        for service in manifest.get("services", [])
    ]

    summary = {
        "platform_name": "Moin Platform",
        "source_file": manifest.get("source_file"),
        "actors_count": len(manifest.get("actors", [])),
        "ui_pages_count": len(manifest.get("ui_pages", [])),
        "services_count": len(manifest.get("services", [])),
        "messaging_count": len(manifest.get("messaging", [])),
        "edge_layers_count": len(manifest.get("edge_layers", [])),
        "event_backbones_count": len(manifest.get("event_backbones", [])),
    }

    baseline = {
        "platform_name": "Moin Platform",
        "source_file": manifest.get("source_file"),
        "actors": manifest.get("actors", []),
        "ui_pages": [
            {
                "name": page.get("name", ""),
                "role": page.get("role", ""),
                "purpose": page.get("purpose", ""),
            }
            for page in manifest.get("ui_pages", [])
        ],
        "edge_layers": [
            {
                "name": edge.get("name", ""),
                "components": edge.get("components", []),
            }
            for edge in manifest.get("edge_layers", [])
        ],
        "event_backbones": [
            {
                "name": eb.get("name", ""),
                "description": eb.get("description", ""),
                "technology": eb.get("technology", ""),
            }
            for eb in manifest.get("event_backbones", [])
        ],
        "services": services,
        "messaging_catalog": manifest.get("messaging", []),
        "summary": summary,
    }

    BASELINE_MANIFEST_FILE.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    BASELINE_SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    BASELINE_SERVICES_FILE.write_text(
        json.dumps(services, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved baseline manifest to: {BASELINE_MANIFEST_FILE}")
    print(f"Saved baseline summary to: {BASELINE_SUMMARY_FILE}")
    print(f"Saved baseline services to: {BASELINE_SERVICES_FILE}")
    print("\nSummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nService names:")
    for service in services:
        print(f"- {service['name']}")


if __name__ == "__main__":
    main()