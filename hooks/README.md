# SQAF Deterministic Security & Validation Hooks

This directory contains the entry-point security and validation hooks for the **Skill Quality Assurance Framework (SQAF)**.

The hooks act as a deterministic pre-execution gate before the SQAF orchestrator activates. They run automatically on `UserPromptSubmit` events to sanitize inputs, enforce structural constraints, block prompt injection, and detect the user's language.

---

## Directory Structure

```
hooks/
├── sqaf_security_hook.py      # Hook 1: Security gate (injection, extensions, prompt size)
├── sqaf_performance_hook.py   # Hook 2: Validation gate (SKILL.md, eval.json, language)
├── hook_contract.py           # Single source of truth for input/output dataclasses
├── hook_utils.py              # Shared primitives (stdin parsing, trace ID, output emitters)
└── tests/                     # Comprehensive test suite (75 tests)
    ├── conftest.py            # Test fixtures (skill/eval directory factories)
    ├── test_security.py       # Unit tests for sqaf_security_hook.py
    └── test_performance.py    # Unit tests for sqaf_performance_hook.py
```

---

## Pipeline Execution Order

Hooks run in sequence via `.agent/settings.json`:

1. **`sqaf_security_hook.py` (Fast Gate)**:
   - Validates prompt size (≤ 50 KB).
   - Scans for prompt injection / jailbreak patterns.
   - Blocks forbidden executable file extensions (`.py`, `.sh`, `.exe`, etc.).
   - *Fails fast with zero disk I/O.*

2. **`sqaf_performance_hook.py` (Validation & Enrichment Gate)**:
   - Enforces single `SKILL.md` path (absolute, exists on disk, ≤ 500 KB).
   - Enforces optional `eval.json` path (absolute, exists on disk, valid JSON, ≤ 5 MB).
   - Detects user language via `lingua` and injects `language_rule` into context.
   - Generates unique `trace_id` for audit linkage across all generated artifacts.

---

## Registration

To enable the hooks in your agent runtime (e.g. Claude Code, Antigravity, Gemini CLI), register them in your `.agent/settings.json` or `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "python3 hooks/sqaf_security_hook.py" }] },
      { "hooks": [{ "type": "command", "command": "python3 hooks/sqaf_performance_hook.py" }] }
    ]
  }
}
```

---

## Running Tests

```bash
python3 -m pytest hooks/tests/ -v
```
