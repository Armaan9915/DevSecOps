# agents/gemini_agent.py
import os
import google.generativeai as genai
import glob

# Configure the API key
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except AttributeError:
    print("GEMINI_API_KEY not found. Please set it in your .env file.")
    # You might want to handle this more gracefully
    # For now, the agent will fail if the key is not set.

def get_code_files_content(directory):
    """Reads all Python files in a directory and returns their content as a single string."""
    code_content = ""
    # Use glob to find all .py files recursively
    py_files = glob.glob(os.path.join(directory, '**', '*.py'), recursive=True)

    for file_path in py_files:
        # Exclude files from virtual environments
        if 'venv/' in file_path or 'site-packages/' in file_path:
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
        print("No Python code found to review.")
        return "No Python code was found in the pull request to review."

    # For safety measures, you can add a limit to the code size
    if len(code_to_review) > 50000: # Limit to ~50k characters
        print("Code size exceeds limit. Truncating for review.")
        code_to_review = code_to_review[:50000] + "\n... (code truncated)"

    # Set up the model
    generation_config = {
      "temperature": 0.2,
      "top_p": 1,
      "top_k": 1,
      "max_output_tokens": 2048,
    }
    model = genai.GenerativeModel(model_name="gemini-pro", generation_config=generation_config)

    prompt = f"""
    You are an expert Senior Software Engineer performing a code review. Your tone should be professional, helpful, and constructive.

    Analyze the following Python code from a pull request. Provide a concise summary of the changes and then identify potential issues or suggest improvements in these categories:
    1.  **Logic Errors:** Any potential bugs or incorrect logic.
    2.  **Security Vulnerabilities:** Any obvious security flaws (e.g., hardcoded secrets, injection risks).
    3.  **Best Practices & Readability:** Adherence to Python best practices (PEP 8), code clarity, and maintainability. Suggest cleaner ways to write the code if applicable.
    4.  **Performance:** Any obvious performance bottlenecks.

    If you find no major issues, state that the code looks good and provide one or two minor suggestions for improvement if possible. Format your response in Markdown.

    Here is the code:
    {code_to_review}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"An error occurred while communicating with the AI model: {e}"