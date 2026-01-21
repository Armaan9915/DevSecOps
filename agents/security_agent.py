import os
from google import genai

def analyze_code_for_security(code_diff):
    """Analyzes a git diff specifically for security vulnerabilities using Gemini."""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        return f"Security Agent Error: Could not configure Gemini. {e}"
    
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

    If you find one or more vulnerabilities, describe each one clearly, explain the potential risk, and suggest a specific code change to fix it.

    If you find NO security vulnerabilities, you MUST respond with the exact string: "No significant security vulnerabilities found."

    Here is the git diff:
    ```diff
    {code_diff}
    ```
    """

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.2,
                "top_p": 1,
                "top_k": 1,
            },
        )
        return response.text
    except Exception as e:
        return f"Security Agent Error: An exception occurred. {e}"