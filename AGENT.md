# AGENT.md — Skill Quality Assurance Framework (SQAF)

> **Industry Standard Agent Discovery & Entry Point Manifest**  
> This file serves as the discovery entry point, operational memory, and router for AI agents interacting with this repository.

---

## 1. Project Overview

The **Skill Quality Assurance Framework (SQAF)** is a systematic, "shift-left" quality assurance framework designed to validate, benchmark, and evaluate AI agent skills (specifically `SKILL.md` instructions, architectural structure, robustness, and `eval.json` test suites) before deployment to agent ecosystems (Claude Code, Cursor, Antigravity, Copilot, Windsurf, etc.).

- **Core Goal**: Evaluate the skill definition itself—isolating prompt design, ambiguous instructions, context bloat, and hallucination risks from external model or agent execution logic.
- **Language & Stack**: Python 3.11+, Pytest, Ruff, Rich CLI runner (`sqaf`).

---

## 2. Principal Project Router: `orchestrator.md`

The master entry point for the skill assessment workflow is:
**[`orchestrator.md`](orchestrator.md)**

### Critical Operating Directives for AI Agents:
1. **Primary Router**: When instructed to assess a skill or run SQAF, load and follow [`orchestrator.md`](orchestrator.md) as the workflow coordinator.
2. **Do Not Modify Core Prompts**: **NEVER modify** `orchestrator.md`, reviewer prompts in `sub-agents/`, or skill definitions in `skills/`. Doing so degrades deterministic evaluation guarantees.
3. **Mandatory Input Preconditions**:
   - The orchestrator **strictly requires** an **absolute path** to the target `SKILL.md` (e.g., `/path/to/my-skill/SKILL.md`) and optionally `eval.json`.
   - The orchestrator **MUST NEVER** attempt workspace auto-discovery or assess skills without an explicit absolute path.
4. **Hook Compliance**:
   - Requests are intercepted by deterministic pre-execution hooks in [`hooks/`](hooks/). Respect hook outputs (`execute_workflow`, `trace_id`, `language_rule`).

---

## 3. Architecture & Repository Map

| Path | Purpose & Agent Scope |
|---|---|
| [`orchestrator.md`](orchestrator.md) | **Workflow Router**: Validates inputs, dispatches reviewers, verifies artifacts, triggers summary. |
| [`sub-agents/`](sub-agents/) | **Isolated Reviewers**: `intent-reviewer`, `instruction-reviewer`, `qa-reviewer`, and `eval-reviewer`. Must run with strict isolation. |
| [`skills/`](skills/) | **Framework Skills**: Contains `assessment-summarizer` to aggregate findings into the final report. |
| [`sqaf/`](sqaf/) | **Core Python Package**: `sqaf-calculator` engine, CLI entry points, score calculation formulas. |
| [`hooks/`](hooks/) | **Deterministic Hooks**: `sqaf_security_hook.py` and `sqaf_performance_hook.py` guardrails. |
| [`docs/`](docs/) | **Architecture & Documentation**: Guidelines, CLI guide, scoring criteria, and test definitions. |
| [`framework-assessment/`](framework-assessment/) | **Output Directory**: Stores `<skill-name>-assessment/` artifacts and final `skill-quality-report.md`. |

---

## 4. Non-Breaking Component Rules

To preserve framework integrity and determinism across agent sessions:
- **Reviewer Isolation**: Reviewer sub-agents must never communicate with each other, share state, or inspect another reviewer's intermediate files.
- **Artifact Contract**: Reviewers output standardized JSON artifacts in `<skill-name>-assessment/`; aggregation is handled strictly by `assessment-summarizer`.
- **Preserve Existing Code**: Do not refactor existing hook schemas, calculation formulas, or CLI logic unless explicitly directed by the user for an intentional feature or bug fix.

---

## 5. User Work Style & Custom Specifications
>(For Users Only) This section is only for Users no for Agents

> **User Customization Area**: Add your project-specific guidelines, coding standards, prompt styles, or model configurations below without modifying core framework components.

### Work Style Preferences:
- **Tone & Communication**: Concise, precise, and evidence-driven. Provide clickable `file://` links for referenced paths.
- **Code Standards**: Adhere to PEP 8, formatted via `ruff`, validated via `pytest tests/`.
- **Language**: Preserve user language selection as detected by the pre-execution hook pipeline.

### Custom Project Notes / Temporary Agent Memory:
*(Add transient notes, task specifications, or repo context here as needed)*
