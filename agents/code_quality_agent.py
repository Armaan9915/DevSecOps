import subprocess
import json

def analyze_code(directory):
    """Runs pylint on a directory and returns the results."""
    try:
        result = subprocess.run(
            ['pylint', '--output-format=json', directory],
            capture_output=True,
            text=True,
            check=False  # IMPORTANT
        )

        # pylint outputs JSON even when exit code != 0
        if result.stdout.strip():
            return json.loads(result.stdout)

        return []

    except FileNotFoundError:
        print("pylint is not installed or not in PATH")
        return []

    except json.JSONDecodeError as e:
        print("Failed to parse pylint output:", e)
        print("Raw output:", result.stdout)
        return []
