from gemini_wrapper import call_gemini_with_retry

def analyze_for_database_issues(code_diff):
    prompt = f"""
    You are a Database Administrator (DBA) expert specializing in Python.
    Analyze the following git diff for database-related issues.

    Focus on:
    - N+1 query problems.
    - Inefficient queries (e.g., lack of indexing).
    - Potential for SQL injection (double-check this).
    - Improper use of transactions.

    If you find issues, explain the problem and suggest a fix. If none are found, respond with "No significant database issues found."

    Here is the git diff:
    ```diff
    {code_diff}
    ```
    """
    return call_gemini_with_retry(prompt)