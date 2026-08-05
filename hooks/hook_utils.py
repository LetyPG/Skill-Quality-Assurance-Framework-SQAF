"""
SQAF Hook Shared Utilities

Zero-logic, zero-side-effect helper functions shared by both SQAF hooks.
Neither hook should reimplement these primitives.

Used by:
    hooks/sqaf_security_hook.py
    hooks/sqaf_performance_hook.py
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import List, Tuple

from hooks.hook_contract import HookResult


# ===========================================================================
# Stdin / payload parsing
# ===========================================================================

def resolve_file_paths(tool_input: dict) -> List[str]:
    """Extract file path strings from a tool_input dict."""
    paths: List[str] = []
    for value in tool_input.values():
        if isinstance(value, str):
            candidate = value.strip()
            if (
                candidate.startswith("/")
                or candidate.startswith("./")
                or candidate.startswith("../")
                or (len(candidate) < 512 and "." in Path(candidate).name)
            ):
                paths.append(candidate)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    paths.append(item.strip())
    return paths


def parse_stdin() -> Tuple[dict, List[str]]:
    """
    Read the JSON payload from stdin.

    UserPromptSubmit payload (Claude Code and compatible runtimes):
        { "user_message": "...", "session_id": "...", ... }

    PreToolUse fallback:
        { "tool_name": "...", "tool_input": { ... } }

    Returns:
        (raw_payload, list_of_file_paths)
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return ({}, [])
        payload = json.loads(raw)
        tool_input = payload.get("tool_input", {})
        file_paths = resolve_file_paths(tool_input)
        return (payload, file_paths)
    except json.JSONDecodeError:
        return ({}, [])


def extract_user_prompt(payload: dict) -> str:
    """
    Extract the user-facing text for validation and language detection.

    Priority:
        1. 'user_message'   — UserPromptSubmit event (primary hook event)
        2. 'prompt', 'query', 'content', 'text' — PreToolUse tool_input keys
        3. Longest string value in tool_input (fallback)
    """
    user_msg = payload.get("user_message", "")
    if isinstance(user_msg, str) and user_msg.strip():
        return user_msg.strip()

    tool_input = payload.get("tool_input", {})
    for key in ("prompt", "query", "content", "text", "user_prompt"):
        val = tool_input.get(key, "")
        if isinstance(val, str) and len(val.strip()) > 10:
            return val.strip()

    candidates = [
        v for v in tool_input.values()
        if isinstance(v, str) and len(v.strip()) > 20
    ]
    if candidates:
        return max(candidates, key=len)

    return ""


# ===========================================================================
# Trace ID
# ===========================================================================

def generate_trace_id() -> str:
    """Generate a UUID4 trace ID for audit trail linkage."""
    return str(uuid.uuid4())


# ===========================================================================
# Emit helpers
# ===========================================================================

def emit_block(
    trace_id: str,
    risk: str,
    reason: str,
    phase: str,
) -> None:
    """
    Emit a blocking HookResult to stdout and exit. Never returns.

    Exit code is always 0 — a non-zero exit crashes some agent runtimes.
    """
    result = HookResult(
        execute_workflow=False,
        trace_id=trace_id,
        risk_level=risk,  # type: ignore[arg-type]
        block_reason=reason,
        block_phase=phase,  # type: ignore[arg-type]
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False))
    sys.exit(0)


def emit_allow(result: HookResult) -> None:
    """Emit a passing HookResult to stdout and exit."""
    print(json.dumps(result.to_dict(), ensure_ascii=False))
    sys.exit(0)
