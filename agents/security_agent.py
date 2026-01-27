import json
from gemini_wrapper import call_gemini_with_retry

def analyze_code_for_security(code_diff):
    """Analyzes a git diff specifically for security vulnerabilities using Gemini."""
    
    
    prompt = f"""
    You are a cybersecurity expert specializing in Python. Your sole task is to analyze the following git diff for security vulnerabilities.

    Analyze only the added lines (starting with '+'). Ignore all other lines.

    Identify potential security issues such as:
    - Hardcoded secrets (API keys, passwords)
    - SQL Injection
    - Cross-Site Scripting (XSS)
    - Insecure Deserialization
    - Command Injection
    - Use of outdated or insecure libraries

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
    Output ONLY raw JSON.

    Here is the git diff:
    ```diff
    {code_diff}
    ```
    """

    return call_gemini_with_retry(prompt, expect_json=True)