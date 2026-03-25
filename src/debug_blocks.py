from pathlib import Path
from lxml import etree
import re
import html
import json

DRAWIO_DIR = Path("input/diagrams")
OUTPUT_FILE = Path("output/debug_blocks.json")


def find_first_drawio_file() -> Path:
    files = list(DRAWIO_DIR.glob("*.drawio")) + list(DRAWIO_DIR.glob("*.xml"))
    if not files:
        raise FileNotFoundError(f"No .drawio or .xml files found in {DRAWIO_DIR.resolve()}")
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


def find_value_elements(root):
    items = []
    for elem in root.iter():
        value = elem.attrib.get("value")
        if value and value.strip():
            items.append({
                "tag": elem.tag,
                "id": elem.attrib.get("id"),
                "parent": elem.attrib.get("parent"),
                "style": elem.attrib.get("style", ""),
                "value_raw": value,
                "value_clean": clean_html_text(value),
            })
    return items


def main():
    drawio_file = find_first_drawio_file()
    tree = etree.parse(str(drawio_file))
    root = tree.getroot()

    items = find_value_elements(root)

    OUTPUT_FILE.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved debug blocks to: {OUTPUT_FILE}")
    print(f"Total labeled elements: {len(items)}")

    print("\nFirst 20 cleaned values:\n")
    for item in items[:20]:
        print("-----")
        print(item["value_clean"])


if __name__ == "__main__":
    main()