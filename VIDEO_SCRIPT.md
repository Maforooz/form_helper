# Video Script — Form Sahayak (target: ~5 minutes)

Record with screen capture + your voice. Suggested tool: OBS Studio (free) or macOS's built-in screen recording (Cmd+Shift+5). Keep each section tight — it's easy to run long on the demo.

---

## 0:00–0:45 — Problem statement

**Say:** Explain who gets stuck: someone without a lawyer, translator, or literate family member on hand, facing a government form, a bank notice, a subsidy application. State the real cost plainly — missed deadlines, unclaimed benefits, worse outcomes — because the paperwork is written for lawyers, not for them.

**Show:** A photo of a genuinely dense sample form/notice (yours or a stock example) on screen while you talk.

## 0:45–1:30 — Why agents

**Say:** A single LLM call can summarize text, but this needs a workflow with real decisions: classify the document first, check claims against a source of truth instead of guessing, hold a multi-turn conversation to collect field values, and — the important part — know when to stop and defer to a human for high-stakes documents. That last one especially isn't a single-completion problem.

**Show:** (optional) the architecture diagram, teased — full version comes next.

## 1:30–2:45 — Architecture

**Say:** Walk through the pipeline stage by stage using the diagram: intake → classifier → risk gate (the branch point) → parallel research tier → fill loop → output composer. Spend a few extra seconds on the risk gate specifically — explain it's a deterministic code branch, not a prompt instruction, and why that distinction matters.

**Show:** The architecture diagram image (export from the chat/artifact, or redraw in a slide). Point at each stage as you describe it.

## 2:45–4:00 — Demo

**Say:** Narrate what's happening as you go, but let the product speak — this is the section graders remember.

**Show, live:**
1. Attach a sample form photo in `adk web`.
2. Show the plain-language explanation appear.
3. Show the requirements-lookup result (mention: "this came from our own MCP server, not a guess").
4. Answer 2–3 of the field-fill questions live.
5. Show the final answer sheet.
6. **Also show the high-risk path**: run it once with a court-notice-style sample and show the referral message instead of an answer sheet — this is worth including explicitly, since it's the design decision you're proudest of.

## 4:00–4:45 — The build

**Say:** Name your tools plainly: built with Google's ADK (Agent Development Kit), a custom MCP server for the requirements lookup, Gemini as the underlying model. Mention any dev-environment tooling you used. Mention the deliberate scoping choice (a small set of document types for this MVP, not "any document").

**Show:** A quick flash of the repo structure / key files (`agent.py`, `risk_gate.py`, `mcp_server/scheme_server.py`).

## 4:45–5:00 — Close

**Say:** One sentence on impact/vision — who this is for and why it matters — and thank the viewer.

---

### Recording checklist
- [ ] Full run-through under 5:00 (rehearse once with a timer)
- [ ] Both the normal path AND the high-risk referral path shown
- [ ] Architecture diagram clearly visible for at least 10 seconds
- [ ] No API keys visible on screen (check terminal history/`.env` isn't shown)
- [ ] Audio levels checked before final take
