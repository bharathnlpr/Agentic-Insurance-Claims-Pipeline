import os
import sqlite3

# Get the absolute path to the Tools folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the Project Root
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Build the unbreakable path to the database
# (Make sure the db name matches exactly what is in your Data folder!)
BUDGET_DB_PATH = os.path.join(PROJECT_ROOT, "Data", "budget_databases", "budget_data.db")

def calculate_repair_budget(damaged_areas: list, severity: str) -> dict:
    """
    Budget Calculator Tool: Fetches exact contractor prices from SQL
    and computes the total claim cost using mathematical severity scales.
    """
    # 1. Establish standard structural severity multipliers
    severity_multipliers = {
        "Low": 0.5,
        "Medium": 1.0,
        "High": 1.5,
        "Catastrophic": 2.5
    }
    multiplier = severity_multipliers.get(severity, 1.0) # Fallback to 1.0 if unknown

    # 2. Open connection to read unit prices
    conn = sqlite3.connect(BUDGET_DB_PATH)
    cursor = conn.cursor()
    
    total_estimated_cost = 0.0
    area_breakdown = {}

    try:
        for area in damaged_areas:
            # Standardize string format to look up lower-case item names safely
            sanitized_area = str(area).lower().strip().replace(" ", "_")
            
            cursor.execute(
                "SELECT unit_price FROM budget_data_DB WHERE item_name = ?;", 
                (sanitized_area,)
            )
            result = cursor.fetchone()
            
            if result:
                base_unit_price = result[0]
            else:
                # Standard fallback cost if the reader extracts an item not explicitly in our database
                base_unit_price = 2000.00 
                
            # Mathematical calculation logic
            final_calculated_item_cost = base_unit_price * multiplier
            total_estimated_cost += final_calculated_item_cost
            area_breakdown[area] = final_calculated_item_cost

        return {
            "total_estimated_budget": total_estimated_cost,
            "currency": "USD",
            "severity_applied": severity,
            "severity_multiplier": multiplier,
            "calculated_area_breakdown": area_breakdown,
            "calculation_status": "SUCCESS"
        }

    except sqlite3.Error as e:
        return {
            "total_estimated_budget": 0.0,
            "calculation_status": f"ERROR: Database computation failure: {e}"
        }
    finally:
        conn.close()

