import os
from agents.distributor_agent import analyze_and_distribute
from agents.grand_master import filter_and_merge_suggestions
from all_agents import EXPERT_AGENTS
import git
import tempfile
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import concurrent.futures
import json

# from agents.security_agent import analyze_code_for_security
# from agents.best_practices_agent import analyze_code_for_security

# --- Load Environment Variables ---
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("🔴 FATAL: GITHUB_TOKEN environment variable not set.")

app = Flask(__name__)

# --- Helper Functions ---

def get_code_changes_from_diff(repo, pr_data):
    """Fetches the git diff between the base and head of the PR."""
    try:
        base_branch = pr_data['pull_request']['base']['ref']
        repo.remotes.origin.fetch()
        head_sha = pr_data['pull_request']['head']['sha']
        # Ensure we are comparing against the fetched origin branch
        diff_output = repo.git.diff(f'origin/{base_branch}', head_sha)
        return diff_output
    except Exception as e:
        print(f"🔴 Error generating git diff: {e}")
        return None
    
def format_final_report(suggestions):
    """Converts the Grand Master's JSON output into a beautiful Markdown report."""
    if not suggestions:
        return "✅ **Review Complete:** No critical issues found. Great job!"

    report = "## 🏗️ Grand Master Architect Report\n"
    report += "I have reviewed the findings from our security and logic experts. Here are the approved changes:\n\n"
    
    # Group by file for better readability
    files = {}
    for s in suggestions:
        path = s.get('file_path', 'Unknown File')
        if path not in files: files[path] = []
        files[path].append(s)

    for file_path, issues in files.items():
        report += f"### 📂 File: `{file_path}`\n"
        report += "| Line | Priority | Issue | Suggested Fix |\n"
        report += "| :--- | :--- | :--- | :--- |\n"
        for i in issues:
            confidence = i.get('confidence', 'Medium')
            report += f"| {i.get('line_number')} | {confidence} | {i.get('reason')} | `{i.get('suggestion')}` |\n"
        report += "\n"
    
    report += "---\n*Reply to this comment to request further specific analysis.*"
    return report

def process_pull_request(pr_data):
    repo_full_name = pr_data['repository']['full_name']
    pr_number = pr_data['pull_request']['number']
    all_expert_suggestions = []

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 1. Setup Repo
            repo = git.Repo.clone_from(
                f"https://x-access-token:{GITHUB_TOKEN}@github.com/{repo_full_name}.git",
                temp_dir,
                branch=pr_data['pull_request']['head']['ref']
            )
            # Helper to get diff (omitted here but assumed present in your code)
            from app import get_code_changes_from_diff 
            code_diff = get_code_changes_from_diff(repo, pr_data)
            
            if not code_diff: return []

            # 2. Distributor Phase
            required_keys = analyze_and_distribute(code_diff)
            if not required_keys:
                post_comment_to_pr(repo_full_name, pr_number, "Assistant", "✅ Minor changes; no deep review needed.")
                return []

            # 3. Expert Phase (Parallel Execution)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_agent = {
                    executor.submit(EXPERT_AGENTS[key]["function"], code_diff): key 
                    for key in required_keys if key in EXPERT_AGENTS
                }
                
                for future in concurrent.futures.as_completed(future_to_agent):
                    agent_result = future.result()
                    if isinstance(agent_result, list):
                        all_expert_suggestions.extend(agent_result)

            # 4. Grand Master Phase (Merge & Deduplicate)
            print(f"Found {len(all_expert_suggestions)} suggestions. Sending to Grand Master...")
            final_suggestions = filter_and_merge_suggestions(all_expert_suggestions)

            # 5. Final Reporting
            final_markdown = format_final_report(final_suggestions)
            post_comment_to_pr(repo_full_name, pr_number, "Grand Master", final_markdown)

            return final_suggestions

        except Exception as e:
            print(f"🔴 Critical Error: {e}")
            return []



def post_comment_to_pr(repo_full_name, pr_number, agent_name, comment_body):
    """Posts a comment to the specified pull request with a structured header."""
    print(f"Posting comment from '{agent_name}' to PR #{pr_number}...")
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Create a structured Markdown body for each agent's comment
    structured_body = f"### 🤖 {agent_name} Report\n\n---\n\n{comment_body}"
    data = {'body': structured_body}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 201:
            print(f"✅ Successfully posted '{agent_name}' review to PR #{pr_number}.")
        else:
            print(f"🔴 Failed to post comment to PR #{pr_number}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"🔴 Network error while posting comment to PR #{pr_number}: {e}")

# --- Core Logic ---

# In app.py, replace the existing process_pull_request function

# def process_pull_request(pr_data):
#     """
#     Orchestrates the analysis of a pull request using a distributor agent.
#     """
#     repo_full_name = pr_data['repository']['full_name']
#     pr_number = pr_data['pull_request']['number']
    
#     json_responses = []

#     with tempfile.TemporaryDirectory() as temp_dir:
#         try:
#             print(f"Cloning repo for PR #{pr_number}...")
#             repo = git.Repo.clone_from(
#                 f"https://x-access-token:{GITHUB_TOKEN}@github.com/{repo_full_name}.git",
#                 temp_dir,
#                 branch=pr_data['pull_request']['head']['ref']
#             )
#             code_diff = get_code_changes_from_diff(repo, pr_data)
            
#             if not code_diff:
#                 no_changes_report = "✅ No code changes were detected in this pull request."
#                 post_comment_to_pr(repo_full_name, pr_number, "DevSecOps Assistant", no_changes_report)
#                 return [{'agent': 'DevSecOps Assistant', 'report': no_changes_report}]

#             # --- 1. Call the Distributor Agent First ---
#             print(f"Calling Distributor Agent for PR #{pr_number}...")
#             required_agent_keys = analyze_and_distribute(code_diff)
#             print(f"Distributor decided the following agents are needed: {required_agent_keys}")

#             if not required_agent_keys:
#                 # If the distributor returns an empty list, no review is needed.
#                 no_review_needed_report = "✅ Changes are minor. No detailed review from expert agents is required."
#                 post_comment_to_pr(repo_full_name, pr_number, "DevSecOps Assistant", no_review_needed_report)
#                 return [{'agent': 'DevSecOps Assistant', 'report': no_review_needed_report}]

#             # --- 2. Run Only the Required Expert Agents ---
#             with concurrent.futures.ThreadPoolExecutor() as executor:
#                 future_to_agent = {}
#                 for agent_key in required_agent_keys:
#                     if agent_key in EXPERT_AGENTS:
#                         agent_info = EXPERT_AGENTS[agent_key]
#                         future = executor.submit(agent_info["function"], code_diff)
#                         future_to_agent[future] = agent_info["display_name"]
                
#                 for future in concurrent.futures.as_completed(future_to_agent):
#                     agent_name = future_to_agent[future]
#                     try:
#                         report = future.result()
#                         post_comment_to_pr(repo_full_name, pr_number, agent_name, report)
#                         json_responses.append({'agent': agent_name, 'report': report})
#                     except Exception as exc:
#                         error_message = f"An error occurred while running the {agent_name}: {exc}"
#                         print(f"🔴 {error_message}")
#                         json_responses.append({'agent': agent_name, 'error': error_message})

#         except Exception as e:
#             error_message = f"A critical error occurred during the pull request processing: {e}"
#             print(f"🔴 {error_message}")
#             post_comment_to_pr(repo_full_name, pr_number, "DevSecOps Assistant", f"### ❌ Assistant Error\n\n{error_message}")
#             return [{'agent': 'DevSecOps Assistant', 'error': error_message}]
            
#     return json_responses

# --- Flask Webhook Endpoint ---

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """
    This webhook is triggered by GitHub on pull request events.
    It orchestrates the analysis and returns a JSON response containing
    all the agent reports.
    """
    
    data = request.form.to_dict()
    if request.headers.get('X-GitHub-Event') == 'pull_request':
        # Use .get() to safely access 'payload'
        payload_str = data.get('payload')
        if payload_str:
            payload = json.loads(payload_str)
            action = payload.get('action')
        if action in ['opened', 'synchronize', 'reopened']:
            pr_number = data.get('number', 'N/A')
            print(f"Pull request event '{action}' for PR #{pr_number}. Triggering analysis.")
            
            # This call now blocks until all agents are done and comments are posted.
            # It returns the list of reports.
            agent_reports = process_pull_request(payload)
            
            print(f"Analysis complete for PR #{pr_number}. Sending final webhook response.")
            return jsonify({
                'status': f'success, processed PR #{pr_number}',
                'comments_posted': agent_reports
            }), 200

    return jsonify({'status': 'unhandled_event'}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)