"""
A small custom MCP server for Form Sahayak.

Why this exists (design note for the write-up):
    Open web search is unreliable for confirming exact local/regional
    bureaucratic requirements -- results are inconsistent, often outdated,
    and rural-specific schemes are frequently not well indexed at all.
    Instead we expose a curated "source of truth" over MCP: a small,
    versioned dataset of known document types and their requirements.

    This is intentionally a stand-in for a real deployment, where this
    server would instead call an official government open-data API.
    Swapping the data source later means editing SCHEME_DATA below (or
    replacing lookup_scheme_requirements's body) -- nothing in agent.py
    needs to change, because MCP decouples the agent from the data source.

Run standalone for a quick manual test:
    python3 mcp_server/scheme_server.py
(it will just sit waiting for stdio input -- that's expected; it's meant
to be launched as a child process by MCPToolset, not run interactively)
"""

import asyncio

import mcp.server.stdio
import mcp.types as mcp_types
from mcp.server.lowlevel import Server

# ---------------------------------------------------------------------------
# Curated dataset. In production this would be a call to a real government
# open-data API instead of a hardcoded dict.
# ---------------------------------------------------------------------------
SCHEME_DATA = {
    "subsidy application": (
        "Typically requires: proof of identity, proof of income (pay slip, "
        "ration card, or income certificate), and a recent address proof. "
        "Most subsidy schemes process applications within 30 days of "
        "receiving a complete form. An incomplete form is usually returned "
        "with a request for the missing document rather than rejected "
        "outright."
    ),
    "bank kyc form": (
        "Standard KYC requires one proof of identity (Aadhaar, passport, "
        "voter ID) and one proof of address. Self-attested photocopies are "
        "usually accepted; the bank verifies against the original at "
        "submission. There is generally no fee for a standard KYC update."
    ),
    "utility notice": (
        "Utility bill notices typically give 15-30 days to pay or dispute "
        "a charge before a late fee or service interruption. Disputing a "
        "charge usually requires visiting or calling the provider's "
        "customer service line listed on the notice itself, not this tool."
    ),
}

DEFAULT_GUIDANCE = (
    "No curated entry exists for this document type yet. Treat any stated "
    "deadline in the original document as authoritative, and if unsure, "
    "recommend the person confirm directly with the issuing office."
)


def lookup_scheme_requirements(doc_type: str) -> str:
    """Look up general requirements for a class of document.

    Args:
        doc_type: A general document category, e.g. 'subsidy application',
            'bank kyc form', 'utility notice'. Not a specific person's case.

    Returns:
        Plain-text guidance about typical requirements/timelines for that
        category of document.
    """
    key = doc_type.strip().lower()
    return SCHEME_DATA.get(key, DEFAULT_GUIDANCE)


# ---------------------------------------------------------------------------
# MCP server plumbing -- wraps the function above as an MCP tool
# ---------------------------------------------------------------------------
app = Server("form-sahayak-scheme-server")


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="lookup_scheme_requirements",
            description=(
                "Look up general requirements for a class of official "
                "document (e.g. 'subsidy application', 'bank kyc form', "
                "'utility notice'). Returns typical requirements and "
                "timelines, not case-specific advice."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_type": {
                        "type": "string",
                        "description": "General document category",
                    }
                },
                "required": ["doc_type"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    if name == "lookup_scheme_requirements":
        result = lookup_scheme_requirements(arguments.get("doc_type", ""))
        return [mcp_types.TextContent(type="text", text=result)]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
