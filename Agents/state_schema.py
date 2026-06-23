from typing import TypedDict, Dict, Any, List

class ClaimsState(TypedDict):
    # Core Telemetry Inputs
    raw_user_input: str
    client_phone_number: str
    
    # Processed Semantic Data Layer
    extracted_claim_data: Dict[str, Any]
    policy_analysis: Dict[str, Any]
    calculated_budget: Dict[str, Any]
    
    # Combined Resolution Outbox
    drafted_offer: Dict[str, Any]
    
    # System Lifecycle Trackers
    final_compiled_output: str
    executive_summary: str

    # Evaluation & Reflexion Telemetry
    eval_score: float
    eval_feedback: str
    revision_count: int