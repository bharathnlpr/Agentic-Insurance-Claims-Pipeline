import os
import sqlite3

# Target the exact same database file used by your client identity layer
DB_FILE = os.path.join("..", "Data", "budget_databases", "budget_data.db")

def init_budget_database():
    """
    Initializes the relational structural repair cost database.

    Creates the local SQLite storage tables for contractor line-item pricing 
    if they do not exist, and populates them with standard baseline unit costs 
    for construction materials and labor areas (e.g., drywall, roofing, flooring).
    
    Args:
        None

    Returns:
        None
    """
    print("==================================================")
    print("INITIALIZING STRUCTURAL REPAIR COST DATABASE")
    print("==================================================\n")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Create the budget database table matching your diagram schema
    print("Creating 'budget_data_DB' table rows...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_data_DB (
            line_no INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL UNIQUE,
            unit_price REAL NOT NULL
        );
    """)

    # 2. Seed data with standard contractor base repair costs (in USD/Local benchmark equivalents)
    cost_benchmarks = [
        ("basement", 4000.00),
        ("roof", 8000.00),
        ("drywall", 1500.00),
        ("kitchen", 6000.00),
        ("flooring", 2500.00),
        ("electrical_grid", 3500.00),
        ("plumbing_network", 3000.00)
    ]

    print("Injecting standardized local contractor unit prices...")
    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO budget_data_DB (item_name, unit_price)
            VALUES (?, ?);
        """, cost_benchmarks)
        conn.commit()
        print("\n--------------------------------------------------")
        print("SUCCESS: Budget relational cost layer initialized!")
        print("--------------------------------------------------")
    except sqlite3.Error as e:
        print(f"\n[Execution Failure] Budget storage initialization aborted: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_budget_database()