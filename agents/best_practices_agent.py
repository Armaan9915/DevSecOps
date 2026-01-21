import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def analyze_for_best_practices(code_diff):
    """Analyzes a git diff specifically for code quality and best practices."""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        return f"Best Practices Agent Error: Could not configure Gemini. {e}"
    
    prompt = f"""
    You are a Senior Python Developer and an expert in writing clean, efficient, and maintainable code. Your sole task is to review the following git diff for violations of best practices.

    Analyze only the added lines (starting with '+'). Ignore all other lines.

    Identify issues related to:
    - Readability and PEP 8 compliance.
    - Potential bugs or logical errors.
    - Overly complex code that could be simplified.
    - Performance bottlenecks.
    - Lack of comments or unclear variable names.

    For each issue you find, provide a specific suggestion for improvement.

    If the code is well-written and follows best practices, you MUST respond with the exact string: "Code follows best practices. No major issues found."

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
        return f"Best Practices Agent Error: An exception occurred. {e}"