import os
import sys
import json
import sqlite3
from typing import Dict
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import your global shared state schema
from state_schema import ClaimsState
# Import the custom embedding engine we built for consistency
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
from Data_Ingest.ingest_vector_data import GeminiEmbeddingFunction

# Initialize environment variables and the Gemini client
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

DB_FILE_PATH = os.path.join(PARENT_DIR, "Data", "client_databases", "client.db")
VECTOR_DB_DIR = os.path.join(PARENT_DIR, "Data", "policy_vector_db")


def policy_agent(state: ClaimsState) -> Dict:
    """
    Policy Agent: Relational lookup finds the policy ID, ChromaDB pulls the 
    isolated rules via RAG filtering, and Gemini conducts the compliance audit.
    """
    # Step 1: Gather raw tracking fields from the pipeline state
    phone = state.get("client_phone_number", "")
    extracted_data = state.get("extracted_claim_data", {})
    raw_text_query = state.get("raw_user_input", "")

    # Step 2: Fetch the exact policy name from SQLite
    policy_analysis = state.get("policy_analysis", {})
    resolved_policy_name = policy_analysis.get("policy_name", "Standard_HomeShield")
    
    print(f" -> Relational Tier Match: Phone {phone} belongs to '{resolved_policy_name}'")

    # Step 3: Connect to your persistent ChromaDB vector store
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    
    # We must link our custom Gemini embedding function when loading the collection
    collection = chroma_client.get_or_create_collection(
        name="client_policies",
        embedding_function=GeminiEmbeddingFunction()
    )

    # Step 4: SEMANTIC RAG SEARCH WITH METADATA FILTERING
    # This fulfills your goal: isolate the search space purely to this file's vectors
    print(f" -> Vector Tier Search: Querying ChromaDB with metadata filter: policy_name = '{resolved_policy_name}'")
    search_results = collection.query(
        query_texts=[raw_text_query],
        n_results=3,
        where={"policy_name": resolved_policy_name}  # <-- METADATA FILTERING AT WORK!
    )

    # Safely extract the matching text block returned by ChromaDB
    if search_results and search_results['documents'] and len(search_results['documents'][0]) > 0:
        retrieved_policy_rules = search_results['documents'][0][0]
        print(" -> RAG Retrieval Success: Relevant policy terms fetched safely.")
    else:
        retrieved_policy_rules = "No matching custom policy exception text located."
        print(" -> RAG Retrieval Warning: No matching documents found. Falling back to default baseline.")

    # Step 5: TOKEN-OPTIMIZED AUDITOR INSTRUCTIONS
    auditor_instruction = (
        "You are an automated insurance compliance auditor. Your job is to semantically verify "
        "if the customer's disaster facts are fully covered or explicitly excluded by their policy terms. "
        "Evaluate synonyms intelligently."
    )

    prompt_template = f"""
        Policy Reference Clauses (Retrieved from Vector Storage):
        \"\"\"
        {retrieved_policy_rules}
        \"\"\"

        Extracted Customer Claim Facts:
        {json.dumps(extracted_data)}

        Task:
        Analyze the structural facts against the reference clauses above. Determine if this claim is covered or excluded.
        You must respond with a valid JSON object matching this exact shape:
        {{"status": "OK" or "VIOLATE", "policy_name": "{resolved_policy_name}", "reason": "A concise 1-sentence explanation matching claim parameters to policy text."}}
    """

    # Step 6: Execute compliance check with deterministic properties
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_template,
        config=types.GenerateContentConfig(
            system_instruction=auditor_instruction,
            temperature=0.0, # Complete deterministic execution logic
            response_mime_type="application/json"
        ),
    )

    # Step 6: Parse the response payload safely
    try:
        compliance_result = json.loads(response.text)
    except Exception:
        compliance_result = {
            "status": "VIOLATE", 
            "reason": "System validation exception parsing semantic policy terms."
        }

    # 🎯 FIX: Fetch the existing policy analysis data block to preserve upfront fields
    existing_policy_analysis = state.get("policy_analysis", {})
    
    # Merge Gemini's compliance verdict right into the existing dictionary structure
    updated_policy_analysis = {
        **existing_policy_analysis,          # Keeps client_name, policy_name, etc.
        "status": compliance_result.get("status", "VIOLATE"),
        "reason": compliance_result.get("reason", "")
    }

    print(f" -> Compliance Audit Finished. Status: {updated_policy_analysis['status']}")

    # Return the safely merged dictionary back to LangGraph
    return {
        "policy_analysis": updated_policy_analysis
    }
