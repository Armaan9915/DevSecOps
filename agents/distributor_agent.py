from gemini_wrapper import call_gemini_with_retry

def analyze_and_distribute(code_diff):
    """
    Returns a list of agent keys required for the diff.
    """
    prompt = f"""
    You are a Technical Project Manager. Analyze the git diff below.
    Determine which specialist agents are required to review this code.
    
    Available Agents:
    - "security": For logic changes, auth, sql, inputs, or dependencies.
    - "best_practices": For new code, refactoring, or complex logic.
    
    Output ONLY a JSON list of strings. Example: ["security", "best_practices"]
    
    Diff:
    {code_diff} 
    """
    
    result = call_gemini_with_retry(prompt, expect_json=True)
    if not isinstance(result, list):
        return ["security", "best_practices"] # Fallback
    return result