from pathlib import Path
import json

INVENTORY_FILE = Path("output/inventory.json")
OUTPUT_FILE = Path("output/review_inventory.txt")


def main():
    inventory = json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))
    detailed_items = inventory.get("detailed_items", [])

    lines = []
    for item in detailed_items:
        category = item.get("category", "unknown")
        label = item.get("label", "")
        lines.append(f"[{category}] {label}")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved review file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()