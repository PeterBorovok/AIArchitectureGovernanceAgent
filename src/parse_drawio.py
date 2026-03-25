from pathlib import Path
from lxml import etree
import json

DRAWIO_DIR = Path("input/diagrams")


def find_first_drawio_file() -> Path:
    files = list(DRAWIO_DIR.glob("*.drawio")) + list(DRAWIO_DIR.glob("*.xml"))
    if not files:
        raise FileNotFoundError(
            f"No .drawio or .xml files found in {DRAWIO_DIR.resolve()}"
        )
    return files[0]


def extract_labels(root) -> list[dict]:
    items = []

    for elem in root.iter():
        value = elem.attrib.get("value")
        elem_id = elem.attrib.get("id")
        style = elem.attrib.get("style", "")

        if value and value.strip():
            items.append(
                {
                    "id": elem_id,
                    "label": value.strip(),
                    "style": style,
                    "tag": elem.tag,
                }
            )

    return items


def main():
    drawio_file = find_first_drawio_file()
    print(f"Reading file: {drawio_file}")

    tree = etree.parse(str(drawio_file))
    root = tree.getroot()

    labels = extract_labels(root)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "raw_labels.json"
    output_file.write_text(json.dumps(labels, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Found {len(labels)} labeled elements")
    print(f"Saved output to: {output_file}")


if __name__ == "__main__":
    main()