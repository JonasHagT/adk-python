"""Placeholder module for specialized sub-agents.

You can define additional LlmAgent (or other agent types) here and import
`env.SUB_AGENT_MODEL` as the default model if you want to keep the orchestration
agent on a heavier model while using a lighter/faster model for these
helpers.
"""

# Example stub – remove or extend when implementing a real sub-agent.
# from google.adk.agents import LlmAgent
# from . import env
#
# simple_formatter_agent = LlmAgent(
#     name="SimpleDataFormatter",
#     model=env.SUB_AGENT_MODEL,
#     tools=[],
#     instruction="""Format the incoming analysis payload into a human-readable
#     summary. Return the summary as markdown text.""",
# )