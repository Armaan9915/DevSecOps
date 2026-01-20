
import os
import git
import tempfile
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import json

# Import BOTH agent functions
from agents.code_quality_agent import analyze_code
from agents.gemini_agent import review_code_with_gemini

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

app = Flask(__name__)

def post_comment_to_pr(repo_full_name, pr_number, comment_body):
    """Posts a single, consolidated comment to a GitHub pull request."""
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set. Cannot post comment.")
        return

    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github+json'}
    data = {'body': comment_body}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Successfully posted consolidated comment to PR #{pr_number}.")
    else:
        print(f"Failed to post comment: {response.status_code} - {response.text}")

def process_pull_request(pr_data):
    """Clones the PR's branch and triggers all agents."""

    repo_full_name = pr_data['repository']['full_name']
    # clone_url = pr_data['repository']['clone_url']
    clone_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{repo_full_name}.git"
    branch_name = pr_data['pull_request']['head']['ref']
    pr_number = pr_data['pull_request']['number']

    reports = [] # A list to hold reports from all agents

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning {clone_url}, branch '{branch_name}' into {temp_dir}")
        try:
            git.Repo.clone_from(clone_url, temp_dir, branch=branch_name)

            # 2. Run Gemini Agent (AI Review)
            print("Running AI Code Review Agent (Gemini)...")
            gemini_review = review_code_with_gemini(temp_dir)
            reports.append(f"### 🧠 AI Code Review (Gemini)\n\n{gemini_review}")

        except git.exc.GitCommandError as e:
            print(f"Error cloning repository: {e}")
            reports.append(f"### ❌ Error\n\nCould not clone the repository to perform analysis. Please check permissions. Error: `{e}`")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            reports.append(f"### ❌ Error\n\nAn unexpected error occurred during analysis: `{e}`")

    # --- Consolidate and Post Comment ---
    final_comment = "## 🤖 DevSecOps Assistant Report\n\n"
    final_comment += "\n---\n".join(reports)
    post_comment_to_pr(repo_full_name, pr_number, final_comment)

# Your existing /webhook route...
@app.route('/webhook', methods=['POST'])
def github_webhook():
    
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    if request.headers.get('X-GitHub-Event') == 'pull_request':
        payload = json.loads(data.get('payload'))
        action = payload.get('action')

        if action in ['opened', 'synchronize', 'reopened']:
            print(f"Pull request '{action}' for PR #{payload['number']}. Triggering analysis.")
            process_pull_request(payload)
            return jsonify({'status': f'success, processed PR #{payload["number"]}'}), 200

    return jsonify({'status': 'unhandled_event'}), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)