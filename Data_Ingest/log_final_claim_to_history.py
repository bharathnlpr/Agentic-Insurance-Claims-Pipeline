import os
import sys
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
from Agents.state_schema import ClaimsState

# 1. Setup absolute paths so directories are created reliably
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(PARENT_DIR, "Data", "claims_history_databases")
HISTORY_DB_PATH = os.path.join(DB_DIR, "claims_history.db")

def log_final_claim_to_history(state: ClaimsState):
    """
    Saves the entire completed Multi-Agent state payload into the 
    historical database to track client behavior and establish an audit trail.
    """
    # Extract every piece of the puzzle out of the final state memory
    phone = state.get("client_phone_number", "")
    raw_text = state.get("raw_user_input", "")
    
    extracted_data = state.get("extracted_claim_data", {})
    disaster = extracted_data.get("disaster_type", "Unknown")
    severity = extracted_data.get("damage_severity", "Medium")
    
    policy_analysis = state.get("policy_analysis", {})
    compliance = policy_analysis.get("status", "UNKNOWN")
    
    # 🎯 NEW: Extract the exact policy reasoning used by the Policy Agent
    real_context = policy_analysis.get("reason", "No context retrieved")
    
    # 🎯 NEW: Extract the exact letter written by the Offer Agent
    drafted_offer = state.get("drafted_offer", {})
    real_letter = drafted_offer.get("resolution_letter_text", "No letter generated")

    calculated_budget = state.get("calculated_budget", {})
    total_cost = calculated_budget.get("total_estimated_budget", 0.0)
    


    conn = sqlite3.connect(HISTORY_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 🎯 FIX: Removed the floating 'f' and matched exactly 8 columns to 8 question marks
        cursor.execute("""
            INSERT INTO historical_logs_DB (
                client_phone_number, raw_problem_description, extracted_disaster_type, 
                extracted_severity, policy_compliance_status, calculated_total_budget, 
                retrieved_policy_context, drafted_resolution_letter
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (phone, raw_text, disaster, severity, compliance, total_cost, real_context, real_letter))
        
        conn.commit()
        print(f"\n[System Log] State metrics for user {phone} successfully saved to Claims History Database.")
        return {
            "final_compiled_output": "SUCCESS_LOGGED"
        }
    except sqlite3.Error as e:
        print(f"[System Log Error] Failed to write historical audit row: {e}")
        return {
            "final_compiled_output": "ERROR_LOGGED"
        }
    
    
    
    
    
    
    
  
