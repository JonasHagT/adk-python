"""orchestration_agent.py
This module houses the *brains* of the Babyland pacing workflow.

Key Concepts for non-developers
===============================
1.  **Tools** – Think of these like small utility functions ("super-powers") that the
    language model can call.  For example, *update_todo_list* can create or
    update a markdown file on disk, while *post_to_slack* would normally send a
    chat message (here it only prints to the console).
2.  **LlmAgent** – A wrapper around a large-language model (LLM).  We give it a
    *system prompt* (a.k.a. "instruction") that describes the rules it must
    follow.  The agent can then decide which *tool* to call at each turn.
3.  **LoopAgent (defined in main.py)** – Runs one or more `LlmAgent`s again and
    again until a special "exit" signal is raised.  This creates an explicit
    "while-loop" that is easy to debug.

If you are new to Python, just remember:
•  Anything inside triple quotes (like this block) is a *docstring* – a comment
   that explains what the file/function/class does.
•  Lines starting with `#` are single-line comments.
"""

# -----------------------------------------------------------------------------
# Standard library / third-party imports
# -----------------------------------------------------------------------------
import os
from typing import Dict, Any

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

from . import env

# -----------------------------------------------------------------------------
# 1. To-Do steps definition
# -----------------------------------------------------------------------------
# We keep the high-level workflow in a single dictionary so that non-technical
# stakeholders can modify the order or wording without touching any other code.
# The keys (left side) are internal identifiers; the values (right side) are the
# human-readable lines that show up in *todo.md*.
# -----------------------------------------------------------------------------

TODO_STEPS = {
    "INITIALIZE": "Initialize and create the To-Do list.",
    "CHECK_DATA": "Check for fresh data from the AdHelp.io pipeline.",
    "VERIFY_DATA": "Verify sales data integrity and get platform insights.",
    "GENERATE_REPORT": "Synthesize all data into a final Slack message.",
    "DELIVER_REPORT": "Post the final report to the Slack channel.",
    "COMPLETE": "Finalize the process and exit the loop.",
}

# -----------------------------------------------------------------------------
# 2. Tool implementations – what the agent can *do*
# -----------------------------------------------------------------------------

# NOTE: Each tool returns a *plain python dictionary*.  The surrounding ADK
#       framework merges these return values into the agent's *state*, making
#       the data available in subsequent turns.


def update_todo_list(completed_step: str, next_step: str) -> dict:
    """Create or update *todo.md* to reflect the agent's progress.

    The file will look like:
    
    - [x] Initialize and create the To-Do list.
    - [ ] Check for fresh data from the AdHelp.io pipeline.
    - ...
    
    Brackets with an **x** mean *done*; empty brackets mean *pending*.
    """
    print(
        f"  [Tool Call] update_todo_list: Marking '{completed_step}' as complete. Next is '{next_step}'."
    )
    with open(env.TODO_FILENAME, "w", encoding="utf-8") as f:
        f.write("# AI Agent To-Do List\n\n")
        f.write("This file tracks the agent's progress for debugging.\n\n")
        is_step_completed = True  # Flip to False once we hit current step.
        for step_key, step_desc in TODO_STEPS.items():
            f.write(f"- [{'x' if is_step_completed else ' '}] {step_desc}\n")
            if step_key == completed_step:
                is_step_completed = False  # All following steps are pending.
    return {"status": f"todo.md updated. Next step is {next_step}"}


def exit_loop(tool_context: ToolContext) -> dict:
    """Tell the *LoopAgent* that the mission is accomplished.

    Setting `tool_context.actions.escalate = True` is the ADK shorthand for
    "please break the loop and stop running agents".
    """
    print(
        f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}. All tasks complete."
    )
    tool_context.actions.escalate = True
    return {"status": "Loop exit signal sent."}


def check_data_and_run_analysis(tool_context: ToolContext) -> Dict[str, Any]:
    """Simulate the data-fetch + analysis step.

    In production this would query BigQuery, Snowflake, etc.  Here we return a
    hard-coded dictionary so the example can run offline.
    """
    print("  [Agent Action] Checking for fresh data and running initial analysis...")
    pacing_analysis = {
        "Babyland SE - Google Ads": {"status": "Overspend", "delta": 4.5}
    }
    return {"analysis_payload": pacing_analysis}


def get_platform_insights_and_verify(tool_context: ToolContext) -> Dict[str, Any]:
    """Second stub – acts as a *gatekeeper* before we exit the loop."""
    print("  [Agent Action] Verifying sales data and fetching platform insights...")
    verification_passed = True  # In real life this would be computed.
    print(f"  [Verification Step] Sales data verification result: {verification_passed}")
    return {"verification_passed": verification_passed}


def post_to_slack(message: str) -> dict:
    """Mimic a Slack API call by printing to stdout."""
    print("\n--- Slack Delivery ---")
    print(f"Message posted to #babyland-pacing:\n{message}")
    print("--- End Slack Delivery ---\n")
    return {"status": "Message successfully posted."}

# -----------------------------------------------------------------------------
# 3. System prompt (a.k.a. *instruction*) for the controller agent
# -----------------------------------------------------------------------------
# Writing the prompt as a standalone variable makes the code easier to scan and
# allows product managers / analysts to tweak the wording without hunting
# through constructor arguments.
# -----------------------------------------------------------------------------

CONTROLLER_SYSTEM_PROMPT = (
    """You are a highly organized orchestrator. You MUST follow a pre-defined to-do "
    "list step-by-step to ensure quality and provide a debug trail.\n\n"
    "**Current Step:** {{current_step | default('INITIALIZE')}}\n\n"
    "**Your Task:** Execute ONLY the current step based on the logic below, then "
    "update the to-do list to proceed to the next one.\n\n"
    "- **IF `current_step` is `INITIALIZE`:** Call `update_todo_list` to create "
    "the to-do file, setting the next step to `CHECK_DATA`.\n"
    "- **IF `current_step` is `CHECK_DATA`:** Call `check_data_and_run_analysis` "
    "to get data, then call `update_todo_list` to advance to `VERIFY_DATA`.\n"
    "- **IF `current_step` is `VERIFY_DATA`:** Call `get_platform_insights_and_verify`. "
    "Then, call `update_todo_list` to advance to `GENERATE_REPORT`.\n"
    "- **IF `current_step` is `GENERATE_REPORT`:** Formulate the final Slack "
    "report text. Then, call `update_todo_list` to advance to `DELIVER_REPORT`.\n"
    "- **IF `current_step` is `DELIVER_REPORT`:** Call `post_to_slack` with the "
    "report text. Then, call `update_todo_list` to advance to `COMPLETE`.\n"
    "- **IF `current_step` is `COMPLETE`:** First call `update_todo_list` to mark "
    "the final step, then immediately call `exit_loop` to terminate the process."
)

# -----------------------------------------------------------------------------
# 4. LlmAgent definition – plugs together *tools* + *system prompt*
# -----------------------------------------------------------------------------

controller_agent = LlmAgent(
    name="PacingControllerAgent",  # Appears in logs / debugging output.
    model=env.ORCHESTRATOR_MODEL,
    tools=[
        update_todo_list,
        exit_loop,
        check_data_and_run_analysis,
        get_platform_insights_and_verify,
        post_to_slack,
    ],
    instruction=CONTROLLER_SYSTEM_PROMPT,
    # The agent will write the chosen *next step* into the state key below so
    # the LoopAgent knows what to do on the following iteration.
    output_key_map={"current_step": env.STATE_CURRENT_STEP},
    description=(
        "The main orchestrator. Manages the workflow step-by-step using a todo.md file."
    ),
)