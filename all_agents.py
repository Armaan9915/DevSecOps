# In app.py, near the top with your other imports

from agents.security_agent import analyze_code_for_security
from agents.best_practices_agent import analyze_for_best_practices
from agents.database_agent import analyze_for_database_issues 

EXPERT_AGENTS = {
    "security": {
        "function": analyze_code_for_security,
        "display_name": "Security Agent"
    },
    "best_practices": {
        "function": analyze_for_best_practices,
        "display_name": "Best Practices Agent"
    },
    "database": {
        "function": analyze_for_database_issues,
        "display_name": "Database Agent"
    }
}