"""Custom function tools used by the fill-loop agents."""

from google.adk.tools import ToolContext


def exit_loop(tool_context: ToolContext) -> dict:
    """Call this ONLY when every required field already has a valid value.

    Setting escalate=True tells the parent LoopAgent to stop iterating
    even though max_iterations hasn't been reached yet -- this is what
    lets the loop end early for a short form instead of always running
    the full 5 iterations.
    """
    tool_context.actions.escalate = True
    return {"status": "all_fields_complete"}
