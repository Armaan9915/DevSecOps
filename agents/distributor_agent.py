import json
from gemini_wrapper import call_gemini_with_retry

def analyze_and_distribute(code_diff):
    """
    Analyzes a git diff and determines which expert agents should review it.

    Returns:
        A list of agent keys (e.g., ['security', 'best_practices'])
    """
    
    # Check for very large diffs to avoid excessive API costs
    if len(code_diff) > 30000:
        print("Diff is very large. Routing to all agents.")
        return ["security", "best_practices"]

    prompt = f"""
    You are a technical project manager. Your job is to analyze a git diff and decide which specialists should review the code.

    The available specialist teams are:
    - "security": For anything related to authentication, authorization, data validation, dependencies, or potential vulnerabilities.
    - "best_practices": For code style, readability, potential bugs, complexity, and general code quality.
    - "database": For changes involving SQL queries, database models (like SQLAlchemy or Django ORM), or database connection logic.

    Based on the following git diff, provide a JSON-formatted list of the specialist teams that are required for a review.
    For example, if the changes involve both database access and complex logic, your response should be:
    ["security", "best_practices"]

    If the changes are minor (e.g., fixing a typo in a comment), return an empty list:
    []

    Here is the git diff:
    ```diff
    {code_diff}
    ```
    """

    try:
        response_text = call_gemini_with_retry(prompt)
        
        # Clean up the response to ensure it's valid JSON
        # Gemini sometimes wraps the JSON in markdown backticks
        if "```json" in response_text:
            response_text = response_text.replace("```json", "").replace("```", "").strip()

        # Safely parse the JSON response
        required_agents = json.loads(response_text)
        if isinstance(required_agents, list):
            return required_agents
        else:
            print(f"Distributor agent returned non-list data: {required_agents}")
            return [] # Return empty on unexpected format

    except json.JSONDecodeError:
        print(f"Failed to decode JSON from distributor agent. Response was: {response_text}")
        # Fallback: If the distributor fails, run all agents to be safe.
        return ["security", "best_practices"]
    except Exception as e:
        print(f"An error occurred in the distributor agent: {e}")
        # Fallback: If any other error occurs, run all agents.
        return ["security", "best_practices"]