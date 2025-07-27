"""Top-level package for the Babyland pacing agent.

Import conveniences so that other scripts can do:

    from pacing_agent import run_agent

without worrying about internal file layout.
"""

from .main import main as run_agent  # Re-export for convenience

__all__ = ["run_agent"]