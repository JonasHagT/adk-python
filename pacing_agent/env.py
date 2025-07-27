"""env.py
Central place for **configuration constants** – edit these to change how the
agent behaves without touching any other Python files.

Quick reference for non-developers
----------------------------------
•  Strings inside quotes (e.g. "gemini-1.5-pro-latest") are plain text.  Change
   them as needed (keep the quotes!).
•  UPPER_CASE names are *constants* – they should not be reassigned elsewhere.
"""

# --- High-level identifiers ---------------------------------------------------
APP_NAME = "babyland_pacing_agent_v5_commented"  # Unique name for analytics / logging
USER_ID = "growth_team_user_01"  # Maps agent activity back to a human owner
SESSION_ID_BASE = "daily_pacing_commented_session"  # Used to group related runs

# --- Debugging file name ------------------------------------------------------
TODO_FILENAME = "todo.md"  # Markdown checklist showing progress

# --- Model selection ----------------------------------------------------------
# `gemini-1.5-pro` is more capable but also more expensive/latency prone.
ORCHESTRATOR_MODEL = "gemini-1.5-pro-latest"
# SUB_AGENT_MODEL = "gemini-1.5-flash-latest"  # <- uncomment when a sub-agent is added

# --- State keys (shared memory between agent turns) ---------------------------
STATE_CURRENT_STEP = "current_step"
STATE_VERIFICATION_PASSED = "verification_passed"
STATE_ANALYSIS_PAYLOAD = "analysis_payload"