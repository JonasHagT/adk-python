APP_NAME = "babyland_pacing_agent_v5_commented"
USER_ID = "growth_team_user_01"
SESSION_ID_BASE = "daily_pacing_commented_session"

# Debugging file name
TODO_FILENAME = "todo.md"

# Model configuration
ORCHESTRATOR_MODEL = "gemini-1.5-pro-latest"
# If additional sub-agents are added in the future, consider using a lighter model for them.
# SUB_AGENT_MODEL = "gemini-1.5-flash-latest"

# ----- Keys used by the in-memory agent state -----
STATE_CURRENT_STEP = "current_step"
STATE_VERIFICATION_PASSED = "verification_passed"
STATE_ANALYSIS_PAYLOAD = "analysis_payload"