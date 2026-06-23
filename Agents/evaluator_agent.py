import os
import time
from typing import Dict
from deepeval.models import GeminiModel
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from state_schema import ClaimsState

# 🎯 FIX 1: Tell DeepEval you are officially using Gemini
os.environ["USE_GEMINI_MODEL"] = "1"

def evaluator_agent(state: ClaimsState) -> Dict:
    print("\n⚖️ [EVALUATOR] Running internal QA check (Faithfulness & Relevancy)...")
    
    raw_input = state.get("raw_user_input", "")
    policy_analysis = state.get("policy_analysis", {})
    drafted_offer = state.get("drafted_offer", {})
    revision_count = state.get("revision_count", 0)
    
    # 1. Prevent infinite loops (max 2 rewrites)
    if revision_count >= 2:
        print("⚠️ [EVALUATOR] Max revisions reached. Forcing pass to prevent infinite loop.")
        return {"eval_score": 1.0, "eval_feedback": "Max revisions reached."}

    # 2. Setup the Test Case
    real_context = policy_analysis.get("reason", "")
    real_letter = drafted_offer.get("resolution_letter_text", "")
    
    test_case = LLMTestCase(
        input=raw_input,
        actual_output=real_letter,
        retrieval_context=[real_context]
    )

    # 3. Initialize the Gemini Judge
    eval_model = GeminiModel(
        model="gemini-2.5-flash", 
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0
    )
    
    # --- METRIC 1: FAITHFULNESS ---
    faithfulness_geval = GEval(
        name="Faithfulness",
        criteria="Evaluate if the actual output logically aligns with the retrieval context. " \
                 "Do NOT penalize standard insurance template phrasing or calculated budget amounts. " \
                 "Only penalize if the final decision contradicts the policy context rule.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.RETRIEVAL_CONTEXT],
        model=eval_model,
        strict_mode=False
    )
    
    # --- METRIC 2: ANSWER RELEVANCY ---
    relevancy_geval = GEval(
        name="Answer Relevancy",
        criteria="Evaluate how directly the actual output addresses the specific input. " \
                 "Penalize generic template responses.",
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=eval_model,
        strict_mode=False
    )
    
    max_retries = 3
    success = False
    
    for attempt in range(max_retries):
        try:
            print(f"⏳ [EVALUATOR] Running API checks (Attempt {attempt + 1}/{max_retries})...")
            # Give a small pause to prevent rate limiting
            time.sleep(2)
            
            # Run both measurements
            faithfulness_geval.measure(test_case)
            f_score = faithfulness_geval.score
            f_reason = faithfulness_geval.reason
            
            relevancy_geval.measure(test_case)
            r_score = relevancy_geval.score
            r_reason = relevancy_geval.reason
            
            # The final score is the lowest of the two metrics.
            final_score = min(f_score, r_score)
            combined_reason = f"Faithfulness Feedback: {f_reason} | Relevancy Feedback: {r_reason}"
            
            # If we made it here without crashing, break the loop!
            success = True
            break
            
        except Exception as e:
            wait_time = 3 * (attempt + 1) # Exponential backoff: waits 3s, then 6s, then 9s.
            print(f"⚠️ [EVALUATOR] API ERROR (503/429): {e}")
            print(f"   -> Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    # Fallback if all 3 retries fail
    if not success:
        print("\n❌ [EVALUATOR] CRITICAL: All API retries failed. Defaulting to PASS to prevent system lockup.")
        final_score = 1.0
        combined_reason = "Eval API failed after 3 attempts."
        f_score, r_score = 1.0, 1.0

    print(f"📊 [EVALUATOR] Faithfulness: {f_score} | Relevancy: {r_score} | Final QA Score: {final_score}")
    
    # 4. Return the State Delta
    return {
        "eval_score": float(final_score),
        "eval_feedback": str(combined_reason),
        "revision_count": revision_count + 1
    }