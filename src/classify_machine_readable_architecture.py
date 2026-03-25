from pathlib import Path
from lxml import etree
import json
import re
import html

DRAWIO_DIR = Path("input/diagrams")
OUTPUT_FILE = Path("output/architecture_manifest.json")


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


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_event_name(event: str) -> str:
    event = event.strip()
    event = re.sub(r"^[\-\*\u2022\[\]() ]+", "", event)
    event = re.sub(r"[\[\]]", "", event)
    event = re.sub(r"\s+", " ", event).strip()
    return event


def normalize_block(block: str) -> str:
    # Fix common formatting issues found in the diagram
    block = re.sub(r"([A-Za-z])Description\s*:", r"\1\nDescription: ", block)
    block = re.sub(r"([A-Za-z])Desciption\s*:", r"\1\nDesciption: ", block)
    block = re.sub(r"\bEmits\b(?!\s*:)", "Emits:", block)
    block = re.sub(r"\bConsumes\b(?!\s*:)", "Consumes:", block)
    block = re.sub(r"\bDesciption\b", "Description", block)
    block = re.sub(r"\n+", "\n", block)
    return block.strip()


def classify_block(block: str) -> str:
    block_norm = normalize_block(block)
    block_lower = block_norm.lower()

    if block_lower.startswith("edge layer") or block_lower.startswith("edge layer".lower()) or block_lower.startswith("edge layer".upper().lower()):
        return "edge_layer"

    if block_lower.startswith("edge layer") or block_lower.startswith("edge layer"):
        return "edge_layer"

    if block_lower.startswith("event backbone"):
        return "event_backbone"

    if "role:" in block_lower and "purpose:" in block_lower:
        return "ui_page"

    lines = [l.strip() for l in block_norm.splitlines() if l.strip()]
    if len(lines) == 1 and "service" not in block_lower and len(lines[0].split()) <= 4:
        return "actor"

    first_line = lines[0] if lines else ""
    if "service" in first_line.lower() or re.search(r"\bservice\b", block_lower):
        return "service"

    return "unknown"


def extract_single_field(block: str, field_name: str) -> str:
    pattern = rf"{field_name}\s*:\s*(.+?)(?=\n[A-Za-z ]+\s*:|\Z)"
    match = re.search(pattern, block, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def extract_section(block: str, section_name: str) -> list[str]:
    pattern = rf"{section_name}\s*:\s*(.+?)(?=\n(?:Description|Emits|Consumes|Role|Purpose|Technology)\s*:|\Z)"
    match = re.search(pattern, block, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    raw = match.group(1).strip()
    if not raw:
        return []

    lines = [normalize_event_name(line) for line in raw.splitlines()]
    lines = [line for line in lines if line and line.lower() not in {"none", "no events emitted"}]
    return lines


def extract_service_name(block: str) -> str:
    block_norm = normalize_block(block)
    lines = [l.strip() for l in block_norm.splitlines() if l.strip()]
    if not lines:
        return ""

    first_line = lines[0]

    # Most common and preferred case
    if "service" in first_line.lower():
        return first_line

    # Fallback: recover something like "SubmissionQueryService"
    match = re.search(r"^(.+?\bService\b)", block_norm, flags=re.IGNORECASE)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()

    return ""


def parse_ui_page(block: str) -> dict:
    block_norm = normalize_block(block)
    lines = [l.strip() for l in block_norm.splitlines() if l.strip()]
    name = lines[0] if lines else ""
    return {
        "name": name,
        "role": extract_single_field(block_norm, "Role"),
        "purpose": extract_single_field(block_norm, "Purpose"),
    }


def parse_service(block: str) -> dict:
    block_norm = normalize_block(block)
    return {
        "name": extract_service_name(block_norm),
        "description": extract_single_field(block_norm, "Description"),
        "emits": extract_section(block_norm, "Emits"),
        "consumes": extract_section(block_norm, "Consumes"),
        "raw_block": block,
        "normalized_block": block_norm,
    }


def parse_edge_layer(block: str) -> dict:
    lines = [l.strip() for l in normalize_block(block).splitlines() if l.strip()]
    name = lines[0] if lines else "EDGE LAYER"
    components = lines[1:] if len(lines) > 1 else []
    return {
        "name": name,
        "components": components,
    }


def parse_event_backbone(block: str) -> dict:
    block_norm = normalize_block(block)
    lines = [l.strip() for l in block_norm.splitlines() if l.strip()]
    name = lines[0] if lines else "Event Backbone"
    return {
        "name": name,
        "description": extract_single_field(block_norm, "Description"),
        "technology": extract_single_field(block_norm, "Technology"),
    }


def main():
    drawio_file = find_first_drawio_file()
    print(f"Using diagram file: {drawio_file}")

    tree = etree.parse(str(drawio_file))
    root = tree.getroot()

    raw_blocks = extract_labels(root)

    actors = []
    ui_pages = []
    services = []
    edge_layers = []
    event_backbones = []
    unknown = []

    for block in raw_blocks:
        category = classify_block(block)

        if category == "actor":
            actors.append(block)
        elif category == "ui_page":
            ui_pages.append(parse_ui_page(block))
        elif category == "service":
            services.append(parse_service(block))
        elif category == "edge_layer":
            edge_layers.append(parse_edge_layer(block))
        elif category == "event_backbone":
            event_backbones.append(parse_event_backbone(block))
        else:
            unknown.append(block)

    all_emits = []
    all_consumes = []

    for service in services:
        all_emits.extend(service["emits"])
        all_consumes.extend(service["consumes"])

    messaging = dedupe_preserve_order(all_emits + all_consumes)

    manifest = {
        "source_file": drawio_file.name,
        "actors": dedupe_preserve_order(actors),
        "ui_pages": ui_pages,
        "edge_layers": edge_layers,
        "event_backbones": event_backbones,
        "services": services,
        "messaging": messaging,
        "summary": {
            "actors_count": len(dedupe_preserve_order(actors)),
            "ui_pages_count": len(ui_pages),
            "services_count": len(services),
            "messaging_count": len(messaging),
            "edge_layers_count": len(edge_layers),
            "event_backbones_count": len(event_backbones),
            "unknown_count": len(unknown),
        },
        "unknown_blocks": unknown,
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved manifest to: {OUTPUT_FILE}")
    print(json.dumps(manifest["summary"], indent=2, ensure_ascii=False))

    print("\nDetected services:")
    for s in services:
        print(f"- {s['name']}")

    print("\nDetected messaging events:")
    for e in messaging:
        print(f"- {e}")


if __name__ == "__main__":
    main()