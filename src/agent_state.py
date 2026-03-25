from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ReviewDecision:
    action: str  # approve | reject | edit
    comment: str = ""


@dataclass
class AgentState:
    project_name: str = "MOIN"
    run_id: str = "default-run"
    
    # New canonical inputs
    baseline_services: List[Dict[str, Any]] = field(default_factory=list)
    extracted_top_level_architecture: Dict[str, Any] = field(default_factory=dict)

    # Context
    adr_summaries: List[Dict[str, Any]] = field(default_factory=list)
    guidance: Dict[str, Any] = field(default_factory=dict)
    service_template: Dict[str, Any] = field(default_factory=dict)

    # Discovery
    existing_services: List[Dict[str, Any]] = field(default_factory=list)
    missing_services: List[Dict[str, Any]] = field(default_factory=list)
    services_needing_internal_design: List[Dict[str, Any]] = field(default_factory=list)
    services_with_contract_mismatch: List[Dict[str, Any]] = field(default_factory=list)
    candidate_services: List[Dict[str, Any]] = field(default_factory=list)
    design_queue: List[str] = field(default_factory=list)

    # Current work item
    current_service: Optional[str] = None
    current_baseline_service: Optional[Dict[str, Any]] = None
    current_extracted_service: Optional[Dict[str, Any]] = None
    current_proposal: Optional[Dict[str, Any]] = None
    current_validation: Optional[Dict[str, Any]] = None

    # Results
    approved_services: List[str] = field(default_factory=list)
    rejected_services: List[str] = field(default_factory=list)
    service_portfolio: Dict[str, Any] = field(default_factory=dict)
    event_catalog: Dict[str, Any] = field(default_factory=lambda: {"events": []})

    # Review / audit
    review_history: List[Dict[str, Any]] = field(default_factory=list)
    last_decision: Optional[Dict[str, Any]] = None

    # Flow control
    finished: bool = False
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)