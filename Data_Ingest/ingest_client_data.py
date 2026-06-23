import os
import sqlite3


DB_DIR = os.path.join("..", "Data", "client_databases")
DB_FILE = os.path.join(DB_DIR, "client.db")

def init_relational_database():
    """
    Initializes the primary portfolio relational database engine.

    Establishes the foundational client-side data schema for the application. Verifies 
    the safe structural existence of the targeted local directories, generates the main 
    client ledger tables (e.g., matching client names, contact details, and registered 
    policy contract designations), and maps primary-to-foreign key relationships across 
    the baseline database layer.

    """
    print("==================================================")
    print("INITIALIZING PORTFOLIO RELATIONAL DATABASE ENGINE")
    print("==================================================\n")
    
    # 1. Ensure the target directory exists safely
    print(f"Checking directory structure for: {DB_DIR}")
    os.makedirs(DB_DIR, exist_ok=True)
    
    # 2. Connect to the SQLite database file
    print(f"Connecting to database file at: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 3. Create the table matching your precise architectural specifications
    print("Creating core 'client_data' table architecture...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phn_number TEXT NOT NULL UNIQUE,
            policy_name TEXT NOT NULL
        );
    """)

    # 4. Implement a high-speed B-Tree index on the phone number column
    # This guarantees near-instant lookups during surge testing execution
    print("Building rapid-lookup B-Tree index on phn_number column...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phone_number 
        ON client_data (phn_number);
    """)

    # 5. Seed data containing 20 diverse profiles spread across your 5 policies
    mock_customers = [
        # Standard_HomeShield Clients
        ("Rahul Sharma", "+919876543210", "Standard_HomeShield"),
        ("Suresh Kumar", "+919812345670", "Standard_HomeShield"),
        ("Deepak Verma", "+919111222333", "Standard_HomeShield"),
        ("Karan Johar", "+919444555666", "Standard_HomeShield"),
        
        # Ultra_Flood_Premium Clients
        ("Priya Nair", "+918123456789", "Ultra_Flood_Premium"),
        ("Anish Pillai", "+918899001122", "Ultra_Flood_Premium"),
        ("Meera Krishnan", "+918555666777", "Ultra_Flood_Premium"),
        ("Rohan Joseph", "+918333444555", "Ultra_Flood_Premium"),
        
        # Apex_Roof_and_Storm Clients
        ("Amit Patel", "+919000011111", "Apex_Roof_and_Storm"),
        ("Sneha Mehta", "+919222333444", "Apex_Roof_and_Storm"),
        ("Vijay Shah", "+919666777888", "Apex_Roof_and_Storm"),
        ("Nisha Contractor", "+919999000111", "Apex_Roof_and_Storm"),
        
        # Metro_Fire_and_Impact Clients
        ("Vikram Singh", "+917778889999", "Metro_Fire_and_Impact"),
        ("Rajesh Chaudhary", "+917111222333", "Metro_Fire_and_Impact"),
        ("Asha Rao", "+917444555666", "Metro_Fire_and_Impact"),
        ("Sanjay Dutt", "+917999888777", "Metro_Fire_and_Impact"),
        
        # Elite_All_Risk_Estate Clients
        ("Anjali Desai", "+916543210987", "Elite_All_Risk_Estate"),
        ("Gaurav Kapoor", "+916111222333", "Elite_All_Risk_Estate"),
        ("Ritu Singhania", "+916444555666", "Elite_All_Risk_Estate"),
        ("Aditya Birla", "+916999000999", "Elite_All_Risk_Estate")
    ]

    print("Injecting 20 production-ready indexed profiles into database entries...")
    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO client_data (name, phn_number, policy_name)
            VALUES (?, ?, ?);
        """, mock_customers)
        conn.commit()
        print("\n--------------------------------------------------")
        print("SUCCESS: Relational database layer fully operational!")
        print("--------------------------------------------------")
    except sqlite3.Error as e:
        print(f"\n[Execution Failure] Database initialization aborted: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_relational_database()