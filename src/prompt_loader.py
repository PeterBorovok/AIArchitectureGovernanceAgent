from __future__ import annotations

from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt_template(filename: str) -> str:
    path = PROMPTS_DIR / filename
    print("DEBUG prompt_loader path:", path)
    print("DEBUG prompt_loader exists:", path.exists())

    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    content = path.read_text(encoding="utf-8")
    print("DEBUG prompt_loader content length:", len(content))
    return content