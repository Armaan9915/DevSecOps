from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def github_webhook():
    if request.headers.get('X-GitHub-Event') == 'pull_request':
        data = request.json
        action = data.get('action')

        if action in ['opened', 'synchronize']:
            print(f"Pull request {action} for PR #{data['number']}")
            # This is where you will trigger your agents later
            process_pull_request(data)

        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'unhandled_event'}), 200

def process_pull_request(pr_data):
    # Placeholder for your agent logic
    print("Processing pull request...")
    pr_number = pr_data['pull_request']['number']
    repo_full_name = pr_data['repository']['full_name']
    head_sha = pr_data['pull_request']['head']['sha']

    # TODO: Clone the repo, checkout the branch, and run agents
    print(f"Repo: {repo_full_name}, PR: {pr_number}, SHA: {head_sha}")


if __name__ == '__main__':
    app.run(port=5000, debug=True)