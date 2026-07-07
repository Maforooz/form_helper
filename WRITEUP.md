# Form Sahayak — Project Write-up

## The problem

Millions of people navigate government forms, subsidy applications, bank paperwork, and legal notices every year without a lawyer, translator, or literate family member available to help. This isn't a rare edge case — it's a structural gap: benefits go unclaimed, deadlines get missed, and people fall through the cracks not because they don't qualify for help, but because the paperwork asking for their qualification is written for lawyers, not for them.

This matters as an "Agents for Good" problem because it's a real, well-documented equity gap, and because a language model is genuinely well-suited to closing it: reading dense, jargon-heavy text and re-expressing it in plain language is one of the things LLMs already do well — the missing piece has always been packaging that into something a person could actually pick up and use in the moment they're staring at a confusing form.

## Why agents, specifically

A single LLM call could summarize a form. But the actual task isn't a single question-and-answer — it's a small workflow with real decisions embedded in it:

- The system needs to figure out **what kind of document this is** before it can decide how to help.
- It needs to **check itself against a source of truth** (not just generate plausible-sounding bureaucratic requirements from memory — being wrong here has real consequences).
- It needs to **hold a multi-turn conversation** to collect field values one at a time, adapting to what the person has already told it.
- And, critically, it needs to **know when to stop** — some documents (court notices, eviction, immigration enforcement) are too high-stakes for an AI to walk someone through alone.

That last point is the one a plain chatbot doesn't do well: an LLM asked nicely to "not help with legal matters" will usually comply, but "usually" isn't good enough when the downside is real. So we built that boundary as actual code — a custom agent (`RiskGate`) that checks the document's risk classification and deterministically skips the fill-out pipeline for high-risk cases, rather than trusting a prompt instruction to hold under all conditions. Getting an agent to make and enforce a judgment call like this is a genuinely multi-step, multi-agent problem, not a single completion.

## Solution overview

Form Sahayak is a five-stage ADK pipeline:

1. **Document intake** — reads a photographed form or notice (multimodal, no separate OCR step).
2. **Classification & risk assessment** — identifies the document type and flags whether it's routine or high-stakes.
3. **Risk gate** — a deterministic branch: high-risk documents get a referral message and nothing else; everything else proceeds.
4. **Research tier (parallel)** — one agent rewrites the document in plain, simple language; another confirms official requirements and timelines against a curated MCP server, rather than guessing.
5. **Field-fill loop** — walks the person through the form field by field, validating formats as it goes, up to five rounds (or fewer, once every field is filled).
6. **Output composer** — produces a plain-language answer sheet the person can copy onto the real form by hand, plus a checklist of anything to bring and any deadline.

## Architecture

See `README.md` for the full architecture diagram and the table mapping each required "key concept" (multi-agent ADK system, MCP server, security features, agent skills) to exactly where it's demonstrated in the code.

## The build journey

We started from a much broader idea — a general-purpose "learn anything" tutor agent — and deliberately narrowed it after realizing that a broad knowledge tutor doesn't solve a specific, documented problem for a specific person; it's a feature, not a mission. Reframing around a concrete accessibility gap (bureaucratic paperwork) gave the project both a sharper pitch and a more interesting architecture, since the interesting engineering work — grounding against a real source of truth, deciding when to defer to a human — only shows up once you're solving something concrete.

The hardest design decision was the risk gate. It would have been easy to just instruct the model to "be careful with legal documents" and call it done, but that's exactly the kind of safety property that shouldn't rest entirely on an LLM choosing to follow an instruction. Moving that decision into a plain Python branch, external to the model's discretion, was the point in the project where it started to feel like a system built with real judgment about automation's limits, rather than just a clever demo.

## What we'd do with more time

- Expand the MCP server's curated dataset to cover far more document types, ideally backed by a real government open-data source instead of a hardcoded dictionary.
- Add text-to-speech for genuinely low-literacy users, since the plain-language, short-sentence output was already designed with that extension in mind.
- Build a proper evaluation set of real (anonymized) sample forms to measure how often the classifier's risk labeling agrees with a human reviewer's judgment — this is the piece we'd want the most confidence in before trusting it with real users.
