# Form Helper

An ADK multi-agent system that helps people understand and fill out government forms, notices, and other bureaucratic paperwork they don't have easy access to a translator or advisor for.

**Track:** Agents for Good — Accessibility / Digital Inclusion

## The problem

People without a lawyer, translator, or literate family member on hand routinely miss out on benefits, deadlines, or legal protections they're entitled to — not because they don't qualify, but because the paperwork asking for their qualification is impenetrable. This hits hardest for people with low literacy, non-native speakers, and anyone in a low-access rural setting without a nearby advisor.

## The solution

Photograph a form or notice. The agent:
1. Reads it (multimodal, no OCR pipeline needed)
2. Explains what it actually says, in plain language, in your own language
3. Confirms official requirements against a source of truth rather than guessing
4. Walks you through filling it out field by field
5. Produces a plain answer sheet you copy onto the real paper form by hand
6. **Refuses to autofill anything it flags as high-stakes** (legal/court/eviction matters) and instead tells you to contact a professional

That last point is a deliberate design choice, not a missing feature — see "Why we don't autofill everything" below.

## Architecture

```
DocumentIntakeAgent (multimodal)
        |
ClassifierAgent  -->  { doc_type, risk_level, deadline }
        |
   RiskGate (custom agent, deterministic branch on risk_level)
        |
   ---- risk_level == 'high' ---->  short-circuit: referral message only
        |
   ---- otherwise ---->  ResearchAndFill:
                            ParallelAgent:
                              - PlainLanguageExplainer
                              - RequirementsLookupAgent  (calls our MCP server)
                            LoopAgent:
                              - FillAssistantAgent
                              - ValidatorAgent
                              (max 5 iterations, or early exit via exit_loop tool)
        |
OutputComposerAgent  -->  final answer sheet + checklist
```

A diagram image is included at `docs/architecture.png` (or see the version in the project write-up).

### Key concepts demonstrated

| Concept | Where |
|---|---|
| Agent / multi-agent system (ADK) | `agent.py` — the full `SequentialAgent` / `ParallelAgent` / `LoopAgent` pipeline |
| MCP Server | `mcp_server/scheme_server.py` (custom server) + `agent.py`'s `requirements_agent`, which calls it via `MCPToolset` |
| Security features | `risk_gate.py` — a deterministic code branch (not an LLM instruction) that hard-stops autofill help for high-risk documents; `.env`-based key handling (see Setup) |
| Agent skills (CLI) | Built and tested throughout with `adk run` / `adk web` (see Setup → Run) |

### Why we don't autofill everything

The `RiskGate` custom agent (`risk_gate.py`) checks the classifier's `risk_level` in plain Python — not by hoping the model follows an instruction — and skips the research/fill pipeline entirely for anything flagged high-risk (court notices, eviction, deportation-related matters). The person gets a clear referral to legal aid instead of an AI-generated answer sheet for something with serious legal consequences. We consider this a feature: knowing the limits of automation is part of building this responsibly.

### Why we don't edit the original document image

`OutputComposerAgent` produces a plain-text answer sheet ("write X in the box labeled Y") rather than an edited copy of the official form. Editing an official document image is legally murkier and more error-prone than giving clear copy-by-hand instructions.


## Sample documents used for testing

We tested against: a subsidy application form and a utility/bank notice (see `samples/` if included). The MCP server's curated dataset (`mcp_server/scheme_server.py`) currently covers these categories; extending it to more document types is a matter of adding entries to `SCHEME_DATA`.

## Known limitations / next steps

- Document coverage is intentionally narrow for this MVP (a small set of common form types) rather than "any document."
- The MCP server's data is hardcoded for the demo; a production version would call a real government open-data API.
- `RiskGate`'s branching logic depends on ADK's `BaseAgent` internals, which have shifted across versions — see the note at the top of `risk_gate.py` if you hit an API mismatch.
- No persistent user accounts/history across sessions yet — each conversation starts fresh.
