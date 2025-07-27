"""main.py – *entry point* for the Babyland daily pacing agent.

Run this file to watch the entire workflow execute locally:

    python -m pacing_agent.main

The script does four things:
1.  Removes any old *todo.md* file so we always start fresh.
2.  Builds a `LoopAgent` that will keep invoking our *controller* until told to
    stop.
3.  Executes the loop completely in memory (no external servers involved).
4.  Prints the final *todo.md* so you can confirm every box is ticked.
"""

import asyncio
import os

from google.adk.agents import LoopAgent
from google.adk.runners import InMemoryRunner

from . import env
from .orchestration_agent import controller_agent


async def main() -> None:
    """Kick off the agent run – this is the *program's* `main()` function."""
    # 1. Ensure a clean slate --------------------------------------------------
    if os.path.exists(env.TODO_FILENAME):
        os.remove(env.TODO_FILENAME)

    print("Starting Babyland Daily Budget-Pacing Agent (Modular Version)...")

    # 2. Assemble the root LoopAgent ------------------------------------------
    root_agent = LoopAgent(
        name="TodoPacingLoop",  # Shows up in logs – feel free to change.
        sub_agents=[controller_agent],
        max_iterations=15,  # Safety valve so we never loop forever.
    )

    # 3. Fire up the in-memory runner -----------------------------------------
    runner = InMemoryRunner()
    initial_state = {}
    final_event = await runner.run(root_agent, initial_state)

    # 4. Human-friendly completion summary ------------------------------------
    print("\n--- Agent Execution Complete ---")
    if final_event and final_event.get("error"):
        print(f"Agent finished with an error: {final_event.get('error')}")
    else:
        print("Agent loop completed successfully.")
    print("--------------------------------\n")

    # Print the *todo.md* for quick visual verification.
    print(f"--- Final State of {env.TODO_FILENAME} ---")
    if os.path.exists(env.TODO_FILENAME):
        with open(env.TODO_FILENAME, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("todo.md was not created.")
    print("--------------------------------")


if __name__ == "__main__":
    asyncio.run(main())