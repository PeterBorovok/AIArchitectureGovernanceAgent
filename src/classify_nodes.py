from pathlib import Path
import json
import re
from collections import defaultdict

RAW_LABELS_FILE = Path("output/raw_labels.json")
OUTPUT_FILE = Path("output/inventory.json")

SERVICE_RULES_FILE = Path("input/catalog/service_keywords.json")
MESSAGING_RULES_FILE = Path("input/catalog/messaging_keywords.json")


INTERNAL_LAYER_PATTERNS = [
    r"\bAPI Layer\b",
    r"\bRepository Layer\b",
    r"\bPersistency\b",
    r"\bPersistence\b",
    r"\bDomain Layer\b",
    r"\bApplication Layer\b",
    r"\bIntegration Layer\b",
    r"\bModule\b",
    r"\bValidator\b",
    r"\bIdempotency\b",
]

DATASTORE_PATTERNS = [
    r"\bDB\b",
    r"\bDatabase\b",
    r"\bReviewDB\b",
    r"\bAurora\b",
    r"\bDynamo(?:DB)?\b",
    r"\bMongo(?:DB)?\b",
    r"\bRedis\b",
    r"\bPostgres\b",
    r"\bSQL\b",
]

EXTERNAL_PATTERNS = [
    r"\bExternal\b",
    r"\bLegacy\b",
    r"\bVendor\b",
    r"\bOPSWAT\b",
    r"\bSendGrid\b",
]

UI_PATTERNS = [
    r"\bUI\b",
    r"\bFrontend\b",
    r"\bPortal\b",
    r"\bWeb\b",
    r"\bAngular\b",
    r"\bReact\b",
    r"\bBFF\b"
]

INFRA_PATTERNS = [
    r"\bCloudFront\b",
    r"\bWAF\b",
    r"\bAPI Gateway\b",
    r"\bCognito\b",
    r"\bSecret Manager\b",
    r"\bCloud watch\b",
    r"\bCloudWatch\b",
    r"\bKMS\b",
    r"\bAccount\b",
]

HTTP_API_HINTS = [
    r"\bGET\b",
    r"\bPOST\b",
    r"\bPUT\b",
    r"\bDELETE\b",
    r"/[A-Za-z0-9_\-\{\}/]+",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_raw_labels() -> list[dict]:
    if not RAW_LABELS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {RAW_LABELS_FILE}")
    return json.loads(RAW_LABELS_FILE.read_text(encoding="utf-8"))


def clean_label(label: str) -> str:
    label = re.sub(r"<[^>]+>", " ", label)
    label = label.replace("&nbsp;", " ")
    label = label.replace("&amp;", "&")
    label = re.sub(r"\s+", " ", label).strip()
    return label


def contains_any(text: str, values: list[str]) -> bool:
    lowered = text.lower()
    return any(v.lower() in lowered for v in values)


def matches_any_regex(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def looks_like_long_description(label: str) -> bool:
    return len(label) > 120 or label.count(" ") > 12


def classify_service_by_rules(label: str, service_rules: dict) -> bool:
    lowered = label.lower()

    if contains_any(lowered, service_rules.get("service_exclude_contains", [])):
        return False

    if lowered in [v.lower() for v in service_rules.get("service_exact", [])]:
        return True

    if contains_any(lowered, service_rules.get("service_contains", [])):
        return True

    return False


def classify_messaging_by_rules(label: str, messaging_rules: dict) -> bool:
    lowered = label.lower()

    if contains_any(lowered, messaging_rules.get("messaging_exclude_contains", [])):
        return False

    if lowered in [v.lower() for v in messaging_rules.get("messaging_exact", [])]:
        return True

    if contains_any(lowered, messaging_rules.get("messaging_contains", [])):
        return True

    return False


def classify_label(label: str, service_rules: dict, messaging_rules: dict) -> str:
    if looks_like_long_description(label):
        return "descriptions"
    if matches_any_regex(label, HTTP_API_HINTS):
        return "api_endpoints"
    if matches_any_regex(label, INTERNAL_LAYER_PATTERNS):
        return "internal_components"
    if matches_any_regex(label, DATASTORE_PATTERNS):
        return "datastores"
    if classify_messaging_by_rules(label, messaging_rules):
        return "messaging"
    if matches_any_regex(label, EXTERNAL_PATTERNS):
        return "external_systems"
    if matches_any_regex(label, UI_PATTERNS):
        return "ui"
    if matches_any_regex(label, INFRA_PATTERNS):
        return "infrastructure"
    if classify_service_by_rules(label, service_rules):
        return "services"
    return "unknown"


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def main():
    raw_items = load_raw_labels()
    service_rules = load_json(SERVICE_RULES_FILE)
    messaging_rules = load_json(MESSAGING_RULES_FILE)

    grouped = defaultdict(list)
    detailed_items = []

    for item in raw_items:
        raw_label = item.get("label", "")
        label = clean_label(raw_label)

        if not label:
            continue

        category = classify_label(label, service_rules, messaging_rules)
        grouped[category].append(label)

        detailed_items.append(
            {
                "id": item.get("id"),
                "label": label,
                "category": category,
                "tag": item.get("tag"),
                "style": item.get("style", ""),
            }
        )

    inventory = {
        "services": dedupe_preserve_order(grouped["services"]),
        "datastores": dedupe_preserve_order(grouped["datastores"]),
        "messaging": dedupe_preserve_order(grouped["messaging"]),
        "external_systems": dedupe_preserve_order(grouped["external_systems"]),
        "ui": dedupe_preserve_order(grouped["ui"]),
        "infrastructure": dedupe_preserve_order(grouped["infrastructure"]),
        "internal_components": dedupe_preserve_order(grouped["internal_components"]),
        "api_endpoints": dedupe_preserve_order(grouped["api_endpoints"]),
        "descriptions": dedupe_preserve_order(grouped["descriptions"]),
        "unknown": dedupe_preserve_order(grouped["unknown"]),
        "detailed_items": detailed_items,
    }

    OUTPUT_FILE.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved inventory to: {OUTPUT_FILE}")
    for key in [
        "services",
        "datastores",
        "messaging",
        "external_systems",
        "ui",
        "infrastructure",
        "internal_components",
        "api_endpoints",
        "descriptions",
        "unknown",
    ]:
        print(f"{key}: {len(inventory[key])}")


if __name__ == "__main__":
    main()