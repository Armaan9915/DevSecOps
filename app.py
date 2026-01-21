import os
import git
import tempfile
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import concurrent.futures # Import the library for parallel execution
import json

from agents.security_agent import analyze_code_for_security
from agents.best_practices_agent import analyze_for_best_practices
from gemini_wrapper import call_gemini_with_retry

load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

app = Flask(__name__)

# ... (get_code_changes_from_diff and post_comment_to_pr functions remain the same) ...

def get_code_changes_from_diff(repo, pr_data):
    # This function is unchanged
    try:
        base_branch = pr_data['pull_request']['base']['ref']
        repo.remotes.origin.fetch()
        head_sha = pr_data['pull_request']['head']['sha']
        diff_output = repo.git.diff(f'origin/{base_branch}', head_sha)
        return diff_output
    except Exception as e:
        print(f"🔴 Error generating git diff: {e}")
        return None

def synthesize_final_review(diff, agent_reports):
    # This function is now simplified to use the wrapper
    print("Synthesizing final review from agent reports...")
    context = "\n\n---\n\n".join(
        f"**{agent}:**\n{report}" for agent, report in agent_reports.items()
    )
    prompt = f"""
    You are a Principal Software Engineer responsible for delivering the final code review comment.
    Synthesize the reports from your specialist agents into a single, coherent, well-formatted Markdown comment.
    Acknowledge reports that found no issues. Integrate and rephrase findings from other reports.
    Add a high-level summary of the changes based on the git diff. Conclude with a final remark.

    Git Diff for context:
    ```diff
    {diff}
    ```

    Specialist Agent Reports:
    {context}
    """
    return call_gemini_with_retry(prompt)


# --- THE NEW PARALLEL ORCHESTRATOR LOGIC ---
def process_pull_request(pr_data):
    repo_full_name = pr_data['repository']['full_name']
    pr_number = pr_data['pull_request']['number']
    final_comment = ""
    agent_reports = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"Cloning repo for PR #{pr_number}...")
            repo = git.Repo.clone_from(f"https://x-access-token:{GITHUB_TOKEN}@github.com/{repo_full_name}.git", temp_dir, branch=pr_data['pull_request']['head']['ref'])
            code_diff = get_code_changes_from_diff(repo, pr_data)
            
            if not code_diff:
                final_comment = "✅ No code changes detected in this pull request."
            else:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_security = executor.submit(analyze_code_for_security, code_diff)
                    future_practices = executor.submit(analyze_for_best_practices, code_diff)
                    agent_reports["Security Agent"] = future_security.result()

                    agent_reports["Best Practices Agent"] = future_practices.result()
                final_comment = synthesize_final_review(code_diff, agent_reports)

        except Exception as e:
            final_comment = f"### ❌ Assistant Error\n\nAn unexpected error occurred: `{e}`"

    post_comment_to_pr(repo_full_name, pr_number, final_comment)

def post_comment_to_pr(repo_full_name, pr_number, comment_body):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    data = {'body': f"## 🤖 DevSecOps Assistant Report\n\n{comment_body}"}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"✅ Successfully posted final review to PR #{pr_number}.")
    else:
        print(f"🔴 Failed to post comment to PR #{pr_number}: {response.status_code} - {response.text}")

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