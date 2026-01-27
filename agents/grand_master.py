import json
from gemini_wrapper import call_gemini_with_retry

def filter_and_merge_suggestions(all_suggestions):
    """
    Merges suggestions from all agents into a single approved list.
    """
    if not all_suggestions:
        return []

    prompt = f"""
    You are the Lead Code Architect.
    You have received suggestions from Security and Best Practice agents.

    Your Goals:
    1. **Validate:** Remove incorrect or hallucinated suggestions.
    2. **Deduplicate:** If two agents flag the same line, combine them into one strong suggestion.
    3. **Prioritize:** Security > Logic > Style.

    Input (JSON):
    {json.dumps(all_suggestions, indent=2)}

    Output:
    Return a strictly formatted JSON list of approved suggestions.
    
    [
      {{
        "file_path": "...",
        "line_number": 0,
        "suggestion": "...",
        "reason": "...",
        "confidence": "High"
      }}
    ]
    """

    result = call_gemini_with_retry(prompt, expect_json=True)
    return result if isinstance(result, list) else []