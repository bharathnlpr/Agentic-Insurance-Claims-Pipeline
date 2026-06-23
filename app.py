import streamlit as st
import time
import sys
import os

# 🎯 THE FIX: Tell Python to explicitly look inside the "Agents" folder for internal imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(CURRENT_DIR, "Agents")
if AGENTS_DIR not in sys.path:
    sys.path.append(AGENTS_DIR)

# Now Python can safely import your compiled LangGraph orchestrator
from Agents.main_stategraph import app as langgraph_app

# Set up the page appearance (Constraint 4: A little bit attractive)
st.set_page_config(page_title="Express Claims Portal", page_icon="🛡️", layout="centered")

# ... [Keep the rest of your app.py exactly the same below this] ...

st.title("🛡️ Express Claims Portal")
st.markdown("Submit your property damage details for instant AI-assisted review.")
st.divider()

# Constraint 2: Two fields only
phone_number = st.text_input("Registered Phone Number", value="+919000011111")
claim_request = st.text_area(
    "Detailed Incident Description", 
    height=120, 
    value="The recent flooding in our basement due to heavy rainfall in recent days, damaging the flooring and drywall extensively."
)

# Trigger Button
if st.button("Submit Claim for Review", type="primary", use_container_width=True):
    
    if phone_number and claim_request:
        
        # Constraint 3: Output comes ONLY after the loop finishes
        with st.spinner("Agents Processing Claim... Extracting data, analyzing policy, evaluating quality, and calculating estimates."):
            
            payload = {
                "client_phone_number": phone_number,
                "raw_user_input": claim_request
            }
            
            try:
                # 🚀 Run the LangGraph Engine
                # Explicitly tell VS Code this returns a dictionary
                final_state: dict = langgraph_app.invoke(payload)
                
                # Explicitly tell VS Code these are dictionaries
                drafted_offer: dict = final_state.get("drafted_offer", {})
                calculated_budget: dict = final_state.get("calculated_budget", {})
                
                # Now VS Code KNOWS these are dictionaries, and .get() will turn yellow!
                letter_text = drafted_offer.get("resolution_letter_text", "No letter could be generated.")
                budget_breakdown: dict = calculated_budget.get("calculated_area_breakdown", {})
                total_cost = calculated_budget.get("total_estimated_budget", 0.0)
                currency = calculated_budget.get("currency", "USD")
                status = drafted_offer.get("final_settlement_status", "UNKNOWN")
                
                st.success("✅ Claim Processed Successfully!")
                st.divider()
                
                # Display the Resolution Letter
                st.subheader("📝 Official Resolution Letter")
                st.info(letter_text)
                
                # Display the Detailed Budget Calculation (Only if approved and budget exists)
                if budget_breakdown and status != "DENIED":
                    st.subheader("💰 Approved Repair Estimate")
                    
                    # Separate box for detailed calculation
                    with st.container(border=True):
                        st.markdown("**Detailed Area Breakdown:**")
                        
                        for area, cost in budget_breakdown.items():
                            col1, col2 = st.columns([3, 1])
                            col1.write(f"- {str(area).capitalize()}")
                            col2.write(f"**${cost:,.2f}**")
                        
                        st.divider()
                        
                        col3, col4 = st.columns([3, 1])
                        col3.write("#### Total Approved Payout:")
                        col4.markdown(f"#### ${total_cost:,.2f} {currency}")
                        
            except Exception as e:
                st.error(f"System Error: {e}")
                
    else:
        st.warning("Please provide both a phone number and a claim description.")
