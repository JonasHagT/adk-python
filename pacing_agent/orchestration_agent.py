import os
from typing import Dict, Any

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

from . import env

# -----------------------------------------------------------------------------
# 1. To-Do steps definition
# -----------------------------------------------------------------------------
# Mapping of internal step keys to human-readable descriptions that will appear
# inside the generated `todo.md` file. Keeping it here (instead of env) makes it
# easier to evolve the workflow without touching global config.
# -----------------------------------------------------------------------------

TODO_STEPS = {
    "INITIALIZE": "Initialize and create the To-Do list.",
    "CHECK_DATA": "Check for fresh data from the AdHelp.io pipeline.",
    "VERIFY_DATA": "Verify sales data integrity and get platform insights.",
    "GENERATE_REPORT": "Synthesize all data into a final Slack message.",
    "DELIVER_REPORT": "Post the final report to the Slack channel.",
    "COMPLETE": "Finalize the process and exit the loop."
}

# -----------------------------------------------------------------------------
# 2. Tool implementations
# -----------------------------------------------------------------------------

def update_todo_list(completed_step: str, next_step: str) -> dict:
    """Create or update *todo.md* to reflect the agent's progress.

    Args:
        completed_step: The step that just finished.
        next_step: The upcoming step to execute on the next loop turn.
    """
    print(
        f"  [Tool Call] update_todo_list: Marking '{completed_step}' as complete. Next is '{next_step}'."
    )
    with open(env.TODO_FILENAME, "w", encoding="utf-8") as f:
        f.write("# AI Agent To-Do List\n\n")
        f.write("This file tracks the agent's progress for debugging.\n\n")
        is_step_completed = True
        for step_key, step_desc in TODO_STEPS.items():
            f.write(f"- [{'x' if is_step_completed else ' '}] {step_desc}\n")
            if step_key == completed_step:
                # All subsequent steps are pending
                is_step_completed = False
    return {"status": f"todo.md updated. Next step is {next_step}"}


def exit_loop(tool_context: ToolContext) -> dict:
    """Signal the surrounding LoopAgent to halt execution."""
    print(
        f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}. All tasks complete."
    )
    tool_context.actions.escalate = True
    return {"status": "Loop exit signal sent."}


def check_data_and_run_analysis(tool_context: ToolContext) -> Dict[str, Any]:
    """Stub for data-fetch + analysis logic."""
    print("  [Agent Action] Checking for fresh data and running initial analysis...")
    pacing_analysis = {
        "Babyland SE - Google Ads": {"status": "Overspend", "delta": 4.5}
    }
    return {"analysis_payload": pacing_analysis}


def get_platform_insights_and_verify(tool_context: ToolContext) -> Dict[str, Any]:
    """Stub verification tool – gatekeeper to exit criteria."""
    print("  [Agent Action] Verifying sales data and fetching platform insights...")
    verification_passed = True
    print(f"  [Verification Step] Sales data verification result: {verification_passed}")
    return {"verification_passed": verification_passed}


def post_to_slack(message: str) -> dict:
    """Pretend to POST a message to Slack – prints to stdout instead."""
    print("\n--- Slack Delivery ---")
    print(f"Message posted to #babyland-pacing:\n{message}")
    print("--- End Slack Delivery ---\n")
    return {"status": "Message successfully posted."}

# -----------------------------------------------------------------------------
# 3. Main orchestrator agent definition
# -----------------------------------------------------------------------------

controller_agent = LlmAgent(
    name="PacingControllerAgent",
    model=env.ORCHESTRATOR_MODEL,
    tools=[
        update_todo_list,
        exit_loop,
        check_data_and_run_analysis,
        get_platform_insights_and_verify,
        post_to_slack,
    ],
    instruction="""You are a highly organized orchestrator. You MUST follow a pre-defined to-do list step-by-step to ensure quality and provide a debug trail.

**Current Step:** {{current_step | default('INITIALIZE')}}

**Your Task:** Execute ONLY the current step based on the logic below, then update the to-do list to proceed to the next one.

- **IF `current_step` is `INITIALIZE`:** Call `update_todo_list` to create the to-do file, setting the next step to `CHECK_DATA`.
- **IF `current_step` is `CHECK_DATA`:** Call `check_data_and_run_analysis` to get data, then call `update_todo_list` to advance to `VERIFY_DATA`.
- **IF `current_step` is `VERIFY_DATA`:** Call `get_platform_insights_and_verify`. Then, call `update_todo_list` to advance to `GENERATE_REPORT`.
- **IF `current_step` is `GENERATE_REPORT`:** Formulate the final Slack report text. Then, call `update_todo_list` to advance to `DELIVER_REPORT`.
- **IF `current_step` is `DELIVER_REPORT`:** Call `post_to_slack` with the report text. Then, call `update_todo_list` to advance to `COMPLETE`.
- **IF `current_step` is `COMPLETE`:** First call `update_todo_list` to mark the final step, then immediately call `exit_loop` to terminate the process.
""",
    output_key_map={"current_step": env.STATE_CURRENT_STEP},
    description="The main orchestrator. Manages the workflow step-by-step using a todo.md file.",
)