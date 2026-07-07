# Submission Checklist

## Category 1 — The Pitch (30 pts)
- [ ] Core Concept & Value (10) — covered in `WRITEUP.md`
- [ ] YouTube Video (10) — record using `VIDEO_SCRIPT.md`, stay under 5 minutes
- [ ] Writeup (10) — `WRITEUP.md`

## Category 2 — The Implementation (70 pts)
- [ ] Technical Implementation (50) — `agent.py`, `risk_gate.py`, `mcp_server/scheme_server.py`, `tools.py`, `schemas.py`
  - [ ] Code is commented explaining design decisions, not just what each function does
  - [ ] No API keys or passwords anywhere in the repo (check `.env` is git-ignored, and check git history if you've already committed once)
- [ ] Documentation (20) — `README.md` (problem, solution, architecture, setup instructions, diagram)

## Key concepts (need ≥3 — this project demonstrates 4)
- [ ] Agent / multi-agent system (ADK) — `agent.py`
- [ ] MCP Server — `mcp_server/scheme_server.py` + the `requirements_agent` in `agent.py`
- [ ] Security features — `risk_gate.py` (deterministic high-risk branch) + `.env` key handling
- [ ] Agent skills (CLI) — mention/show `adk run` / `adk web` usage in video or README

## Before you submit
- [ ] Run the full pipeline end-to-end at least once with a real sample form image
- [ ] Run it once with a high-risk-style document to confirm the referral message fires instead of an answer sheet
- [ ] Double-check `requirements.txt` installs cleanly in a fresh virtual env
- [ ] Confirm the README's "Key concepts demonstrated" table matches what's actually in the code
- [ ] Video is under 5 minutes and covers: problem, why agents, architecture, demo, the build
- [ ] Repo has no `.env` file committed (only `.env.example`)
