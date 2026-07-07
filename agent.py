"""
Form Sahayak -- core agent pipeline (capstone Step 3).

Pipeline shape:
    intake_agent
      -> classifier_agent
      -> risk_gated_pipeline  (RiskGate, a custom agent)
           -- if risk_level == 'high': short-circuits with a referral
              message and skips everything below
           -- otherwise, runs research_and_fill:
                research_tier   (ParallelAgent: explainer + requirements lookup)
                fill_loop       (LoopAgent: fill_agent + validator_agent)
      -> output_composer

Key concepts demonstrated in this file (see also mcp_server/scheme_server.py
and risk_gate.py):
    - Multi-agent system (ADK): the whole pipeline above
    - MCP Server: requirements_agent calls our custom MCP server instead of
      a built-in tool
    - Security features: risk_gated_pipeline is a deterministic code branch,
      not an LLM instruction, for documents flagged high-risk
"""

import os

from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from .schemas import DocumentClassification, PlainLanguageSummary
from .tools import exit_loop
from .risk_gate import RiskGate

MODEL = "gemini-2.5-flash"

# Absolute path to our custom MCP server script -- MCPToolset launches this
# as a child process and talks to it over stdio.
_MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mcp_server", "scheme_server.py"
)

# ---------------------------------------------------------------------------
# 1. Document intake agent -- multimodal, reads the photographed document.
#    No special code needed for the image itself: Gemini 2.5 Flash is
#    natively multimodal, so whatever image the person attaches in
#    `adk web` (or passes via the Runner) is just part of the input the
#    model sees.
# ---------------------------------------------------------------------------
intake_agent = LlmAgent(
    name="DocumentIntakeAgent",
    model=MODEL,
    instruction="""
You will receive a photo of a government form, notice, or letter.

Do NOT transcribe the document word-for-word -- describe its content in
your own words instead. This avoids reproducing exact copyrighted text,
and it's also all the downstream agents actually need.

Output plain text with two sections:

CONTENT:
A paraphrased description of what the document says: who it's from, what
it's about, any amounts/dates/conditions mentioned, and anything the
reader needs to know. Do not copy sentences directly from the document --
restate them in different words.

FIELDS:
A list of each blank field, checkbox, or signature line, describing what
it's asking for (e.g. "Applicant full name", "Date of birth", "Signature
line"). You can quote a short field *label* (a few words) verbatim since
labels aren't the concern here, but do not quote surrounding paragraphs.
""",
    output_key="document_text",
)

# ---------------------------------------------------------------------------
# 2. Classification & risk agent
# ---------------------------------------------------------------------------
classifier_agent = LlmAgent(
    name="ClassifierAgent",
    model=MODEL,
    instruction="""
Read the extracted document below and classify it.

Document:
{document_text}

Be conservative about risk_level -- when genuinely unsure whether
something is routine or high-stakes, prefer 'medium' or 'high' over
'low'.
""",
    output_schema=DocumentClassification,
    output_key="classification",
)

# ---------------------------------------------------------------------------
# 3. Research tier -- these two agents don't depend on each other's
#    output, so running them as a ParallelAgent saves a round trip
#    compared to a strict sequence.
# ---------------------------------------------------------------------------
explainer_agent = LlmAgent(
    name="PlainLanguageExplainer",
    model=MODEL,
    instruction="""
Rewrite the document below at roughly a 5th-grade reading level.

Document: {document_text}
Document type: {classification}

Describe what the document says and asks for. Do not advise the person on
what decision to make -- describe content, don't give guidance. If any
part is genuinely unclear, say so in unclear_parts instead of guessing.
""",
    output_schema=PlainLanguageSummary,
    output_key="plain_summary",
)

# This agent demonstrates MCP tool use: instead of hoping web search turns
# up something relevant (unreliable for regional/rural schemes), it calls
# our curated MCP server as a source of truth. See mcp_server/scheme_server.py
# for the data and the note on why it's structured this way.
requirements_agent = LlmAgent(
    name="RequirementsLookupAgent",
    model=MODEL,
    instruction="""
Document type: {classification}

Call the lookup_scheme_requirements tool with the general document
category (not this specific person's case) to confirm typical
requirements and timelines. Report back plainly what it returns. If the
tool has no specific entry, say so rather than guessing at bureaucratic
rules from memory -- getting this wrong could genuinely hurt someone
relying on it.
""",
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python3",
                    args=[_MCP_SERVER_PATH],
                ),
            ),
        )
    ],
    output_key="requirements_notes",
)

research_tier = ParallelAgent(
    name="ResearchTier",
    sub_agents=[explainer_agent, requirements_agent],
)

# ---------------------------------------------------------------------------
# 4. Field-by-field fill loop
# ---------------------------------------------------------------------------
fill_agent = LlmAgent(
    name="FillAssistantAgent",
    model=MODEL,
    instruction="""
Fields to fill: {document_text}
Plain-language summary: {plain_summary}

Ask the person for the value of ONE field you don't already have, in
simple language. If the conversation so far already contains values for
every field, call the exit_loop tool instead of asking anything else.
""",
    tools=[exit_loop],
    output_key="fill_state",
)

validator_agent = LlmAgent(
    name="ValidatorAgent",
    model=MODEL,
    instruction="""
Latest field value: {fill_state}

Check whether the value's format looks reasonable for that kind of field
(a date looks like a date, an ID number has a plausible length, etc). If
something looks wrong, say what's wrong in one short sentence so the fill
agent can ask again next turn. If it looks fine, just say "ok".
""",
    output_key="validation_feedback",
)

fill_loop = LoopAgent(
    name="FieldFillLoop",
    sub_agents=[fill_agent, validator_agent],
    max_iterations=5,  # safety net; exit_loop above allows finishing earlier
)

# ---------------------------------------------------------------------------
# 4.5 Safety gate -- wraps BOTH the research tier and the fill loop.
#     High-risk documents never reach either one; see risk_gate.py for why
#     this is enforced in code rather than left to a prompt instruction.
# ---------------------------------------------------------------------------
research_and_fill = SequentialAgent(
    name="ResearchAndFill", sub_agents=[research_tier, fill_loop]
)
risk_gated_pipeline = RiskGate(name="RiskGatedPipeline", safe_branch=research_and_fill)

# ---------------------------------------------------------------------------
# 5. Output composer
# ---------------------------------------------------------------------------
output_composer = LlmAgent(
    name="OutputComposerAgent",
    model=MODEL,
    instruction="""
Classification: {classification}
Plain-language summary: {plain_summary}
Requirements notes: {requirements_notes}
Collected field values: {fill_state}

Produce, in this order:
1. A short answer sheet -- "write X in the box labeled Y" for each field,
   so the person can copy it onto the real paper form by hand (we
   deliberately don't edit the official document image itself).
2. A checklist of anything to bring or attach, and any deadline.
3. If classification.risk_level is 'high', end with a clear, unmissable
   line recommending the person contact free legal aid or the relevant
   helpline before relying on this answer sheet alone.
""",
    output_key="final_output",
)

# ---------------------------------------------------------------------------
# Root pipeline -- this is what ADK's CLI/web UI auto-discovers
# ---------------------------------------------------------------------------
root_agent = SequentialAgent(
    name="FormSahayakPipeline",
    sub_agents=[
        intake_agent,
        classifier_agent,
        risk_gated_pipeline,
        output_composer,
    ],
)
