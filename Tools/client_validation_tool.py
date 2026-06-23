import os
import sqlite3
from typing import Dict, Any

# Dynamic absolute pathing alignment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Force pathing to calculate strictly from the absolute root directory structure
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CLIENT_DB_PATH = os.path.join(PROJECT_ROOT, "Data", "client_databases", "client.db")

def verify_client_registration(phone_number: str) -> Dict[str, Any]:
    """
    Validates if a phone number exists within the corporate client registry.
    Returns policy tracking data or security isolation signatures back to the graph state.
    """
    if not os.path.exists(CLIENT_DB_PATH):
        print(f"❌ [TOOL ERROR] Client database not found at: {CLIENT_DB_PATH}")
        return {"status": "ERROR", "policy_name": "UNREGISTERED_CLIENT", "reason": "Database missing."}

    conn = sqlite3.connect(CLIENT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Match this query against your actual client table and column names
        cursor.execute("SELECT policy_name FROM client_data WHERE phn_number = ?;", (phone_number,))
        row = cursor.fetchone()
        
        if row:
            # Extract string from the single-item tuple returned by fetchone
            policy_name = row[0]
            print(f"🔑 [TOOL SUCCESS] Client verified successfully. Policy: {policy_name}")
            return {
                "status": "PENDING",
                "policy_name": policy_name,
                "reason": "Client verified successfully in registry ledger."
            }
        else:
            print(f"🛑 [TOOL SECURITY ALERT] Phone number {phone_number} not found in client registry.")
            return {
                "status": "VIOLATE",
                "policy_name": "UNREGISTERED_CLIENT",
                "reason": "Tracking signature missing from registration records."
            }
            
    except sqlite3.Error as e:
        print(f"❌ [TOOL ERROR] SQL execution failure: {e}")
        return {"status": "ERROR", "policy_name": "UNREGISTERED_CLIENT", "reason": str(e)}
    finally:
        conn.close()