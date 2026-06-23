import os
import sqlite3

# Pointing to an isolated history directory to keep data tiers separate
DB_FILE_PATH = os.path.join("..", "Data", "claims_history_databases", "claims_history.db")

def init_history_database():
    """
    Initializes the historical claims logging audit trail database.

    Constructs a dedicated relational tracking database and schema designed to log 
    every transaction state running through the LangGraph workflow. Automatically 
    applies a high-speed database index on the client phone number column to allow 
    the pipeline to instantly perform real-time velocity and look-back checks for 
    anti-fraud triage.

    """
    print("==================================================")
    print("INITIALIZING HISTORICAL CLAIMS LOGGING DATABASE")
    print("==================================================\n")
    
    # System Safety: Build folders automatically if they don't exist
    os.makedirs(os.path.dirname(DB_FILE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # 1. Create the Historical Audit Trail Table
    print(f"Creating 'historical_logs_DB' table inside {os.path.basename(DB_FILE_PATH)}...")
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_logs_DB (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_phone_number TEXT NOT NULL,
                raw_problem_description TEXT,
                extracted_disaster_type TEXT,
                extracted_severity TEXT,
                policy_compliance_status TEXT,
                calculated_total_budget REAL,
                retrieved_policy_context TEXT,      -- 🎯 NEW: The real RAG context
                drafted_resolution_letter TEXT,     -- 🎯 NEW: The real AI letter
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 2. CREATE A HIGH-SPEED DATABASE INDEX
    # This is the secret keyword that prevents traffic slowdowns. 
    # It allows the Fraud Node to instantly search millions of past phone numbers.
    print("Indexing 'client_phone_number' column for high-speed fraud lookups...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_phone 
        ON historical_logs_DB (client_phone_number);
    """)

    conn.commit()
    conn.close()
    print("\n--------------------------------------------------")
    print("SUCCESS: Historical logging database is live!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    init_history_database()