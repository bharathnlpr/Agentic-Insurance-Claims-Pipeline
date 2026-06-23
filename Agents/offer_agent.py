import os
import sys
import json
from typing import Dict
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 🚀 DYNAMIC PATH RESOLUTION: Inject root project path for cross-directory imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from state_schema import ClaimsState

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def offer_agent(state: ClaimsState) -> Dict:
    """
    Offer Agent: Evaluates compliance status, cross-references total contractor 
    budgets against hard corporate tier caps, and drafts the final resolution letter.
    """
    print("\n==================================================")
    print("EXECUTING RESOLUTION & OFFER SETTLEMENT AGENT")
    print("==================================================")

    # 1. Gather upstream states
    policy_analysis = state.get("policy_analysis", {})
    policy_name = policy_analysis.get("policy_name", "Standard_HomeShield")
    compliance_status = policy_analysis.get("status", "VIOLATE")
    compliance_reason = policy_analysis.get("reason", "")
    
    calculated_budget = state.get("calculated_budget", {})
    raw_contractor_total = calculated_budget.get("total_estimated_budget", 0.0)
    itemized_breakdown = calculated_budget.get("breakdown", {})

    # 2. Hard Enforce Policy Coverage Limits (Enterprise Business Logic)
    policy_caps = {
        "Standard_HomeShield": 50000.00,
        "Apex_Roof_and_Storm": 75000.00,
        "Metro_Fire_and_Impact": 120000.00,
        "Ultra_Flood_Premium": 150000.00,
        "Elite_All_Risk_Estate": 300000.00
    }
    
    tier_ceiling = policy_caps.get(policy_name, 50000.00)
    limit_extended_violation = False
    final_approved_payout = raw_contractor_total

    if compliance_status == "OK" and raw_contractor_total > tier_ceiling:
        limit_extended_violation = True
        final_approved_payout = tier_ceiling
        print(f" ⚠️  [LIMIT EXCEEDED] Budget ${raw_contractor_total:,.2f} exceeds tier limit for {policy_name}. Payout restricted to ${tier_ceiling:,.2f}.")

    # 3. Token-Optimized System Instructions
    resolver_instruction = """
        You are an expert insurance settlement officer. Your job is to draft a formal, 
        definitive resolution or settlement letter to the policyholder. 
        You must remain professional, empathetic, yet strictly compliant with corporate guidelines.
        Never mention internal system variables, code details, or node names in the letter text.
    """

    prompt_template = f"""
        Resolution Guidelines Context:
        - Customer Policy Tier: {policy_name}
        - Compliance Clearance: {compliance_status}
        - Compliance Auditor Note: {compliance_reason}
        - Raw Repair Estimates: ${raw_contractor_total:,.2f}
        - Tier Maximum Policy Cap: ${tier_ceiling:,.2f}
        - Hard Capped Payout Balance: ${final_approved_payout:,.2f}
        - Policy Cap Exceeded Flag: {limit_extended_violation}
        - Itemized Structural Damage Details: {json.dumps(itemized_breakdown)}

        Task:
        Generate a valid JSON dictionary output summarizing this definitive case conclusion. 
        The final layout text must speak directly to the customer. 
        If cap exceeded flag is True, explain professionally that the policy tier caps out at that exact maximum threshold,
          and any remaining repair balance represents out-of-pocket client liability.
        
        Your response must match this JSON structure:
        {{
            "final_settlement_status": "APPROVED" or "DENIED" or "CAP_ENFORCED_APPROVAL",
            "approved_total_payout": {final_approved_payout},
            "resolution_letter_text": "Your formal letter body string goes here..."
        }}
    """

    # 4. Generate final resolution text using Gemini
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_template,
        config=types.GenerateContentConfig(
            system_instruction=resolver_instruction,
            temperature=0.0,
            response_mime_type="application/json"
        ),
    )

    try:
        drafted_payload = json.loads(response.text)
        print(f" -> Offer Generation Complete. Outcome: {drafted_payload.get('final_settlement_status')}")
    except Exception:
        drafted_payload = {
            "final_settlement_status": "ERROR",
            "approved_total_payout": 0.0,
            "resolution_letter_text": "An internal framework exception occurred while compiling your final offer letter layout."
        }

    return {
        "drafted_offer": drafted_payload,
        "eval_score": None,
        "eval_feedback": ""
    }

