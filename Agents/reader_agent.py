import os
from typing import Dict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv


# Import your global shared state schema
from state_schema import ClaimsState

# Initialize environment variables and the Gemini client
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ======================================================================
# 1. STRUCTURED OUTPUT SCHEMA (The Pydantic Data Contract)
# ======================================================================
class ExtractedClaimSchema(BaseModel):
    client_name: str = Field(
        default="Unknown", 
        description="Name of the policyholder if mentioned."
    )
    disaster_type: str = Field(
        description="The type of natural disaster (e.g., Flood, Storm, Earthquake, Wildfire)."
    )
    damage_severity: str = Field(
        description="Strictly classify severity based on description into one of these exact words: Low, Medium, High, or Catastrophic."
    )
    # UPDATED DESCRIPTION: We add explicit mapping instructions inside the schema contract
    damaged_items_or_areas: list[str] = Field(
        description=(
            "List of specific damaged structures. You MUST map natural language synonyms directly "
            "to these exact backend database keywords: 'basement', 'roof', 'drywall', 'kitchen', "
            "'flooring', 'electrical_grid', 'plumbing_network'. For example, map 'sheetrock' or "
            "'plasterboard' to 'drywall'; map 'wires' to 'electrical_grid'; map 'pipes' to 'plumbing_network'."
        )
    )
    estimated_impact_description: str = Field(
        description="A concise, 1-sentence technical summary of the structural impact."
    )


# ======================================================================
# 2. THE AGENT NODE FUNCTION
# ======================================================================
def reader_agent(state: ClaimsState) -> Dict:
    """
    Reader Agent: Receives raw unstructured text from the frontend,
    extracts details, and standardizes synonyms into exact database keys.
    """
    # Extract the inputs passed into the pipeline state
    raw_user_input = state.get("raw_user_input", "")

    # UPDATED SYSTEM INSTRUCTION: Explicitly command the model to act as a translator/standardizer
    reader_instruction = """
        You are an expert insurance data extraction and standardization engine. 
        Your job is to analyze unstructured emergency claim text and isolate key structural facts into the requested JSON schema format.

        Exxample JSON Output Format:
        { "client_name": "John Doe", "disaster_type": "Flood", "damage_severity": "High", "damaged_items_or_areas": ["flooring"], 
        "estimated_impact_description": "Significant water damage to the main living areas." }

        CRITICAL MAPPING RULE:
            The backend database only accepts specific keywords for damaged areas. You must translate any natural 
            language variations or synonyms used by the client into these exact terms:
            - 'sheetrock', 'plasterboard', 'wallboard' -> 'drywall'
            - 'pipes', 'leaking lines', 'water mains' -> 'plumbing_network'
            - 'wires', 'breaker box', 'power lines' -> 'electrical_grid'
            - 'ceiling', 'shingles', 'tiles' -> 'roof'
            - 'carpeting', 'hardwood', 'tiles' -> 'flooring'

        If a damaged structure does not fit any of these categories, extract it using its common singular 
        lowercase noun form. Do not guess information not supported by the text.
    """

    prompt_template = f"Analyze the following claim and extract core details:\n\"{raw_user_input}\""

    # Execute Gemini API call with structured schema constraints
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_template,
        config=types.GenerateContentConfig(
            system_instruction=reader_instruction,
            temperature=0.0,  # 0.0 guarantees highly deterministic, non-creative extraction
            response_mime_type="application/json",
            response_schema=ExtractedClaimSchema,
        ),
    )

    # Parse the verified JSON string back into a Python dictionary
    import json
    try:
        structured_payload = json.loads(response.text)
    except Exception:
        # Fallback dictionary if parsing completely fails
        structured_payload = {
            "client_name": "Unknown",
            "disaster_type": "Unknown",
            "damage_severity": "Medium",
            "damaged_items_or_areas": [],
            "estimated_impact_description": "Failed to parse extraction payload natively."
        }

    # Return the dictionary payload to LangGraph to update 'extracted_claim_data'
    return {
        "extracted_claim_data": structured_payload
    }

