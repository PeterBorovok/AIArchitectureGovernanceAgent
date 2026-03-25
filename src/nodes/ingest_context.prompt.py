from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.agent_state import AgentState
from src.config import TOP_LEVEL_ARCH_FILE, ADR_DIR, GUIDANCE_DIR, TEMPLATE_FILE


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text_files_as_records(folder: Path, kind: str) -> List[Dict[str, Any]]:
    if not folder.exists():
        return []

    records: List[Dict[str, Any]] = []
    for file_path in sorted(folder.glob("*")):
        if file_path.is_file():
            records.append({
                "kind": kind,
                "name": file_path.name,
                "content": file_path.read_text(encoding="utf-8", errors="ignore")
            })
    return records


def run(state: AgentState) -> AgentState:
    state.top_level_inventory = _read_json(TOP_LEVEL_ARCH_FILE, default={})
    state.service_template = _read_json(TEMPLATE_FILE, default={})

    adr_docs = _read_text_files_as_records(ADR_DIR, kind="adr")
    guidance_docs = _read_text_files_as_records(GUIDANCE_DIR, kind="guidance")

    # For now, raw text goes in. Later: summarize them before design calls.
    state.adr_summaries = adr_docs
    state.guidance = {"documents": guidance_docs}

    return state