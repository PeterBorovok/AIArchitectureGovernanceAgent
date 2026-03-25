from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
PORTFOLIO_DIR = ROOT / "portfolio"
SCHEMAS_DIR = ROOT / "src" / "schemas"

# New input model
BASELINE_SERVICES_FILE = INPUT_DIR / "baseline_services.json"
EXTRACTED_TOP_LEVEL_ARCH_FILE = INPUT_DIR / "extracted_top_level_architecture.json"

ADR_DIR = INPUT_DIR / "adrs"
GUIDANCE_DIR = INPUT_DIR / "guidance"
TEMPLATE_FILE = INPUT_DIR / "templates" / "microservice_template.json"

SERVICES_INDEX_FILE = PORTFOLIO_DIR / "services_index.json"
EVENTS_CATALOG_FILE = PORTFOLIO_DIR / "events_catalog.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-5.4" #os.getenv("OPENAI_MODEL", "gpt-5")