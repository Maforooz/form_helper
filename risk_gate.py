"""
RiskGate -- a custom ADK agent implementing a deterministic safety branch.

Why this exists:
    The classifier agent labels risk_level as low/medium/high, but an LLM
    label alone is just a suggestion until something in the code actually
    acts on it. This agent wraps the "research + fill loop" portion of the
    pipeline and simply does not run it when risk_level is 'high' -- it
    emits a short, clear message instead and lets the pipeline end there.

    This is deliberately implemented as plain Python control flow (a
    CustomAgent), not as an LLM decision, because "should we proceed" is
    exactly the kind of decision that shouldn't depend on the model
    reliably choosing to follow an instruction under all conditions.

NOTE ON ADK VERSIONS:
    BaseAgent's async generator signature has shifted across ADK releases.
    The pattern below matches the documented approach as of this writing
    (override `_run_async_impl`, yield Events, delegate to sub-agents via
    `sub_agent.run_async(ctx)`). If your installed `google-adk` version
    exposes a different signature, check `google.adk.agents.base_agent`
    for the current method name/signature and adjust the delegation calls
    accordingly -- the *logic* here (check state, branch, delegate or
    short-circuit) is what matters and should carry over directly.
"""

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types


class RiskGate(BaseAgent):
    """Runs `safe_branch` unless classification.risk_level == 'high'."""

    safe_branch: BaseAgent

    def __init__(self, name: str, safe_branch: BaseAgent):
        super().__init__(name=name, sub_agents=[safe_branch], safe_branch=safe_branch)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        classification = ctx.session.state.get("classification")
        risk_level = getattr(classification, "risk_level", None) or (
            classification.get("risk_level") if isinstance(classification, dict) else None
        )

        if risk_level == "high":
            # Deliberately do NOT run the research tier or fill loop.
            # Write directly to the state key output_composer expects, so
            # the rest of the pipeline still produces a coherent final
            # message rather than erroring on missing state.
            ctx.session.state["plain_summary"] = None
            ctx.session.state["requirements_notes"] = None
            ctx.session.state["fill_state"] = None
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[
                        types.Part(
                            text=(
                                "This document looks like it involves serious "
                                "legal or urgent matters. We're not going to "
                                "guess at how to fill it out -- please contact "
                                "free legal aid or the relevant helpline before "
                                "taking any action on it."
                            )
                        )
                    ]
                ),
            )
            return

        # Low/medium risk: proceed with the normal pipeline.
        async for event in self.safe_branch.run_async(ctx):
            yield event
