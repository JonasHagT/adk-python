import asyncio
import os

from google.adk.agents import LoopAgent
from google.adk.runners import InMemoryRunner

from . import env
from .orchestration_agent import controller_agent


async def main():
    """Entry point for running the Babyland daily pacing agent."""
    # Ensure we start from a clean slate.
    if os.path.exists(env.TODO_FILENAME):
        os.remove(env.TODO_FILENAME)

    print("Starting Babyland Daily Budget-Pacing Agent (Modular Version)...")

    # Build the root loop agent – it only contains the orchestrator for now.
    root_agent = LoopAgent(
        name="TodoPacingLoop",
        sub_agents=[controller_agent],
        max_iterations=15,  # Safety valve during development.
    )

    # Run everything entirely in-memory.
    runner = InMemoryRunner()
    initial_state = {}

    final_event = await runner.run(root_agent, initial_state)

    print("\n--- Agent Execution Complete ---")
    if final_event and final_event.get("error"):
        print(f"Agent finished with an error: {final_event.get('error')}")
    else:
        print("Agent loop completed successfully.")
    print("--------------------------------\n")

    # Expose the final state of the todo file for manual inspection.
    print(f"--- Final State of {env.TODO_FILENAME} ---")
    if os.path.exists(env.TODO_FILENAME):
        with open(env.TODO_FILENAME, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("todo.md was not created.")
    print("--------------------------------")


if __name__ == "__main__":
    asyncio.run(main())