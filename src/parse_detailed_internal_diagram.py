from pathlib import Path
from lxml import etree
import json
import re
import html

DRAWIO_DIR = Path("input/diagrams")
OUTPUT_FILE = Path("output/detailed_internal_manifest.json")


def find_first_drawio_file() -> Path:
    files = list(DRAWIO_DIR.glob("*.drawio")) + list(DRAWIO_DIR.glob("*.xml"))
    if not files:
        raise FileNotFoundError(
            f"No .drawio or .xml files found in {DRAWIO_DIR.resolve()}"
        )
    return files[0]


def clean_html_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def extract_labels(root) -> list[str]:
    items = []
    for elem in root.iter():
        value = elem.attrib.get("value")
        if value and value.strip():
            cleaned = clean_html_text(value)
            if cleaned:
                items.append(cleaned)
    return items


def normalize_component_type(name: str) -> str:
    lowered = name.lower()

    if "api" in lowered:
        return "api"
    if "application" in lowered:
        return "application"
    if "domain" in lowered:
        return "domain"
    if "persist" in lowered or "repository" in lowered or "db" in lowered:
        return "persistence"
    if "event" in lowered or "publisher" in lowered or "consumer" in lowered:
        return "messaging"
    if "audit" in lowered or "log" in lowered:
        return "audit"
    if "observability" in lowered or "monitor" in lowered or "trace" in lowered:
        return "observability"
    if "adapter" in lowered or "integration" in lowered or "retriever" in lowered:
        return "integration"
    if "worker" in lowered:
        return "worker"

    return "other"


def looks_like_service_name(text: str) -> bool:
    return "service" in text.lower() and len(text.splitlines()) == 1


def looks_like_internal_component(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "layer",
        "publisher",
        "consumer",
        "adapter",
        "retriever",
        "module",
        "worker",
        "orchestrator",
        "manager",
        "engine",
        "logging",
        "observability",
        "api",
        "domain",
        "application",
        "persistence",
        "repository",
    ]
    return any(k in lowered for k in keywords) and "service" not in lowered


def main():
    drawio_file = find_first_drawio_file()
    print(f"Using diagram file: {drawio_file}")

    tree = etree.parse(str(drawio_file))
    root = tree.getroot()

    labels = extract_labels(root)

    services = []
    current_service = None

    for label in labels:
        if looks_like_service_name(label):
            current_service = {
                "service_name": label.strip(),
                "internal_components": []
            }
            services.append(current_service)
            continue

        if current_service and looks_like_internal_component(label):
            current_service["internal_components"].append({
                "name": label.strip(),
                "type": normalize_component_type(label),
            })

    output = {
        "source_file": drawio_file.name,
        "services": services,
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved detailed internal manifest to: {OUTPUT_FILE}")
    print(f"Services parsed: {len(services)}")
    for service in services:
        print(f"- {service['service_name']}: {len(service['internal_components'])} components")


if __name__ == "__main__":
    main()