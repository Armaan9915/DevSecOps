# agents/gemini_agent.py
import os
import glob
from flask.cli import load_dotenv
from google import genai
import dotenv
# Initialize Gemini client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_code_files_content(directory):
    """Reads all Python files in a directory and returns their content as a single string."""
    code_content = ""
    py_files = glob.glob(os.path.join(directory, "**", "*.py"), recursive=True)

    for file_path in py_files:
        if "venv/" in file_path or "site-packages/" in file_path:
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                code_content += f"\n--- File: {os.path.relpath(file_path, directory)} ---\n"
                code_content += content
        except Exception as e:
            code_content += f"\n--- Error reading file {file_path}: {e} ---\n"

    return code_content


def review_code_with_gemini(directory):
    """
    Analyzes the code in the given directory using the Gemini API and returns a review.
    """
    code_to_review = get_code_files_content(directory)

    if not code_to_review.strip():
        return "No Python code was found in the pull request to review."

    # Safety limit (character-based guard)
    if len(code_to_review) > 50_000:
        print("Code size exceeds limit. Truncating for review.")
        code_to_review = code_to_review[:50_000] + "\n... (code truncated)"

    prompt = f"""
You are an expert Senior Software Engineer performing a code review.
Your tone should be professional, helpful, and constructive.

Analyze the following Python code from a pull request. Provide:
1. A concise summary of the changes
2. Potential issues or suggestions in these categories:
   - Logic Errors
   - Security Vulnerabilities
   - Best Practices & Readability
   - Performance

If no major issues are found, say so and provide 1–2 minor suggestions.

Format your response in Markdown.

Here is the code:
{code_to_review}
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.2,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            },
        )

        # Token usage (NEW SDK)
        if response.usage_metadata:
            print("Prompt tokens:", response.usage_metadata.prompt_token_count)
            print("Response tokens:", response.usage_metadata.candidates_token_count)
            print("Total tokens:", response.usage_metadata.total_token_count)

        return response.text

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"An error occurred while communicating with the AI model: {e}"
