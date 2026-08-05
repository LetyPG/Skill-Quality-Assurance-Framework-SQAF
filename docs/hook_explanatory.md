# SQAF Deterministic Security & Validation Hooks

> **Document Scope**: Explanatory guide for the SQAF runtime-agnostic entrypoint security and validation layer.

---

## 1. Overview & Architectural Goals

The **SQAF Hook System** establishes a shift-left, deterministic pre-execution gate before the Orchestrator activates. By moving input validation out of probabilistic LLM reasoning and into predictable Python code, SQAF guarantees fail-closed governance for every assessment request.

### Core Objectives
1. **Single Responsibility**: Decouple fast security pattern scanning from disk validation and language enrichment.
2. **Fail-Closed Gatekeeping**: Halt invalid or malicious requests before tool execution or orchestrator initialization.
3. **Traceability & Audit**: Generate a UUID4 `trace_id` per run to link security decisions to post-execution artifacts.
4. **Multilingual Compliance**: Detect user language offline (`lingua`) and propagate language rules to all generated reports.

---

## 2. Dual-Hook Pipeline Architecture

Hooks execute sequentially on the `UserPromptSubmit` event as configured in `.agent/settings.json`:

```
User Input ──> [ sqaf_security_hook.py ] ──(Pass)──> [ sqaf_performance_hook.py ] ──(Pass)──> Orchestrator
                     │                                      │
                  (Block)                                (Block)
                     ▼                                      ▼
             Return HookResult                      Return HookResult
            (execute_workflow=False)               (execute_workflow=False)
```

---

## 3. Hook 1: Security Gate (`sqaf_security_hook.py`)

A zero-I/O, ultra-fast pre-filter targeting prompt injection and unsafe attachments.

| Check | Constraint | Action on Violation |
|---|---|---|
| **Prompt Size** | ≤ 50 KB text payload | Block (`SIZE`) |
| **Injection Patterns** | Scans for override/jailbreak regex patterns | Block (`SECURITY`) |
| **File Extensions** | Denies executable extensions (`.py`, `.sh`, `.exe`, `.bat`, etc.) | Block (`SECURITY`) |

---

## 4. Hook 2: Performance & Validation Gate (`sqaf_performance_hook.py`)

Handles disk verification, structural checks, and language propagation.

| Check | Constraint | Action on Violation |
|---|---|---|
| **SKILL.md Path** | Exactly 1 absolute path ending in `/SKILL.md` | Block (`SKILL_MD`) |
| **SKILL.md Disk Check** | File must exist on disk and be ≤ 500 KB | Block (`SKILL_MD`) |
| **eval.json Check** | If referenced: absolute path, exists, valid JSON, ≤ 5 MB | Block (`EVAL_JSON`) |
| **Language Detection** | Offline detection (`lingua`) with confidence threshold ≥ 0.75 | Enriches `language_rule` |

---

## 5. Interface Contract (`HookResult`)

Both hooks emit JSON to `stdout` matching the standard `HookResult` interface defined in `hooks/hook_contract.py`:

```json
{
  "execute_workflow": true,
  "trace_id": "0c85cec2-862c-4a09-92e0-1b286193e564",
  "risk_level": null,
  "block_reason": null,
  "block_phase": null,
  "skill_path": "/absolute/path/to/SKILL.md",
  "eval_path": null,
  "language": "Spanish",
  "confidence": 0.95,
  "language_rule": "All SQAF assessment artifact text SHALL be written in Spanish...",
  "sanitized_context": { ... }
}
```

If `execute_workflow` is `false`, the runtime aborts immediately, and `block_reason` is displayed to the user.

---

## 6. Integration Configuration (`.agent/settings.json`)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "python3 hooks/sqaf_security_hook.py" }]
      },
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "python3 hooks/sqaf_performance_hook.py" }]
      }
    ]
  }
}
```

---

## 7. Verification & Automated Testing

The hook suite is validated by 75 automated unit and integration tests under `hooks/tests/`:

```bash
# Run hook test suite
python3 -m pytest hooks/tests/ -v
```
