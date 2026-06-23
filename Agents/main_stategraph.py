import json
import os
import sys
from typing import Dict, Literal
from langgraph.graph import StateGraph, END

# 1. Import your unified state schema contract
from state_schema import ClaimsState

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
    
# 2. Import all your individual worker node functions cleanly
from planner_agent import planner_agent
from reader_agent import reader_agent
from policy_agent import policy_agent
from budget_agent import budget_agent
from offer_agent import offer_agent
from Data_Ingest.log_final_claim_to_history import log_final_claim_to_history
from evaluator_agent import evaluator_agent

def parallel_splitter_node(state: ClaimsState):
    """Pass-through hub to safely branch the state into parallel paths."""
    print("\n [PLANNER HUB] Forking execution state into parallel processing lanes...")
    return {} # Returns an empty dict so state remains unchanged

workflow = StateGraph(ClaimsState)

# Step A: Register all physical operational worker components into the graph topology
workflow.add_node("PlannerAgent", planner_agent)
workflow.add_node("ParallelSplitter", parallel_splitter_node)
workflow.add_node("ReaderAgent", reader_agent)
workflow.add_node("PolicyAgent", policy_agent)
workflow.add_node("BudgetAgent", budget_agent)
workflow.add_node("OfferAgent", offer_agent)
workflow.add_node("HistoryLogger", log_final_claim_to_history)
workflow.add_node("EvaluatorAgent", evaluator_agent)

def route_after_planner(state: ClaimsState) -> Literal["goToReader", "goToParallelProcessing", "goToOffer", "goToLogger", "goToEvaluator", "end"]:
    
    policy_analysis = state.get("policy_analysis", {})
    policy_name = policy_analysis.get("policy_name", "")
    policy_status = policy_analysis.get("status", "")
    drafted_offer = state.get("drafted_offer", {})
    
    extracted_data = state.get("extracted_claim_data", {})
    calculated_budget = state.get("calculated_budget", {})
    
    eval_score = state.get("eval_score")
    revision_count = state.get("revision_count", 0)

    print(f" 🎯 [ROUTER DIAGNOSTIC] Current Status: {policy_status} | Policy: {policy_name}")

    # ==============================================================================
    # 🏁 ESCAPE VALVE
    # ==============================================================================
    if policy_name == "UNREGISTERED_CLIENT":
        print("\n🛑 [ROUTER] Unregistered profile verified. Short-circuiting graph cleanly to END.")
        return "end"

    # ==============================================================================
    # 🔀 THE WATERFALL ROUTING PIPELINE
    # ==============================================================================
    
    # Check 1: Extraction Gate
    if not extracted_data:
        return "goToReader"
        
    # Check 2: Analytics Gate (Wait for both parallel nodes to finish)
    if not policy_status or not calculated_budget:
        return "goToParallelProcessing"
        
    # Check 3: Offer Generation Gate (Runs for BOTH Approved and Denied claims)
    if not drafted_offer:
        print("\n📝 [ROUTER] Analytics complete. Routing to Offer Agent to draft the response...")
        return "goToOffer"
        
    # Check 4: The Internal QA Gate (Runs if offer is drafted but has NO grade)
    
    
    if drafted_offer and eval_score is None:
        print("\n⚖️ [ROUTER] Offer drafted. Routing to Evaluator for Quality Assurance...")
        return "goToEvaluator"
      
    # Check 5: The Reflexion Loop (Pass or Fail?)
    if eval_score is not None and not state.get("final_compiled_output"):
        if eval_score < 0.8 and revision_count < 2:
            print(f"\n❌ [ROUTER] QA Failed (Score: {eval_score}). Routing back to OfferAgent for rewrite!")
            return "goToOffer"
        else:
            print(f"\n✅ [ROUTER] QA Passed/Resolved (Score: {eval_score}). Routing directly to database logger...")
            return "goToLogger"

    # Check 6: The Final Exit Gate (Runs only after the Logger finishes)
    if state.get("final_compiled_output"):
        print("\n✅ [ROUTER] Cycle complete and safely logged. Routing to END.")
        return "end"
        
    # Safety Net
    return "end"
        
        
# Set your Central Orchestrator as the Front Gate
workflow.set_entry_point("PlannerAgent")

# Wire up the traffic routes
workflow.add_conditional_edges(
    "PlannerAgent",
    route_after_planner,
    {
        "goToReader": "ReaderAgent",
        "goToParallelProcessing": "ParallelSplitter",
        "goToOffer": "OfferAgent",
        "goToLogger": "HistoryLogger",
        "goToEvaluator": "EvaluatorAgent",
        "end": END
    }
)

# Parallel lane fanning
workflow.add_edge("ParallelSplitter", "PolicyAgent")
workflow.add_edge("ParallelSplitter", "BudgetAgent")

# THE COMPLETELY BALANCED HUB RETURN MATRIX
workflow.add_edge("ReaderAgent", "PlannerAgent")
workflow.add_edge("PolicyAgent", "PlannerAgent")
workflow.add_edge("BudgetAgent", "PlannerAgent")
workflow.add_edge("OfferAgent", "PlannerAgent")
workflow.add_edge("HistoryLogger", "PlannerAgent")
workflow.add_edge("EvaluatorAgent", "PlannerAgent")

app = workflow.compile()


"""
if __name__ == "__main__":
    import time
    print("==================================================")
    print("LAUNCHING ENTERPRISE MULTI-AGENT STATEGRAPH ENGINE")
    print("==================================================\n")
    
    # ⏳ RATE LIMIT SHIELD: Force a 3-second cooldown to let remote API connections settle
    print("⏱️  Stabilizing cloud API connection channels...")
    time.sleep(3)

    # Test Scenario: Valid, approved claim string passing into your system
    test_user_payload = {
        "raw_user_input": "The recent flooding in our basement due to heavy rainfall in recent days, damaging the flooring and drywall extensively.",
        "client_phone_number": "+919000011111"
    }
    
    print("Triggering runtime state thread...")
    final_state = app.invoke(test_user_payload)
    
    print("\n==================================================")
    print("RUN COMPLETE — FINAL STATE SUMMARY PAYLOAD")
    print("==================================================")
    print(json.dumps(final_state, indent=4))
"""