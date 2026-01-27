from gemini_wrapper import call_gemini_with_retry

def analyze_code_for_security(code_diff):
    """
    Returns a list of security suggestions.
    """
    prompt = f"""
    You are a Security Expert. Analyze the git diff for vulnerabilities.
    
    Instead of a report, output a JSON list of specific suggestions.
    
    IMPORTANT: 
    1. Use the line numbers from the 'Right' side of the diff (the new code).
    2. "suggestion" must be the complete replacement code for that line/block.
    
    Output format:
    [
      {{
        "file_path": "path/to/file.py",
        "line_number": 15,
        "suggestion": "api_key = os.getenv('KEY')",
        "reason": "Hardcoded secret detected.",
        "confidence": "High"
      }}
    ]

    If no issues, return [].
    
    Diff:
    {code_diff}
    """

    return call_gemini_with_retry(prompt, expect_json=True)