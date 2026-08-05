#!/usr/bin/env python3
"""
SQAF Security Hook  —  UserPromptSubmit Phase 3

Single responsibility: detect and block adversarial inputs before any
disk access or enrichment occurs. Designed to be fast and free of I/O.

Checks (fail-closed, in order):
    3a. Prompt size         — blocks oversized prompts (token flooding)
    3b. Prompt injection    — blocks known override / jailbreak patterns
    3c. Blocked extensions  — blocks executable and script file references

Runs BEFORE sqaf_performance_hook.py in the UserPromptSubmit pipeline.
If this hook blocks, sqaf_performance_hook.py never executes.

Output:
    execute_workflow: false  → runtime blocks; user sees block_reason
    execute_workflow: true   → minimal allow; performance hook runs next

Exit code is always 0 — a non-zero exit crashes some agent runtimes.

Dependencies: stdlib only (no optional installs required).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path when script is executed directly via python3
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from hooks.hook_contract import HookResult
from hooks.hook_utils import (
    emit_allow,
    emit_block,
    extract_user_prompt,
    generate_trace_id,
    parse_stdin,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PROMPT_BYTES: int = 50 * 1024  # 50 KB — prevents token flooding

BLOCKED_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".dll", ".so", ".bat", ".cmd", ".ps1", ".sh",
    ".js", ".vbs", ".py", ".bin", ".apk", ".jar",
    ".docm", ".xlsm",
})

INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+a",
    r"forget\s+(your\s+)?role",
    r"override\s+(your\s+)?system\s+prompt",
    r"act\s+as\s+if",
    r"disregard\s+(the\s+)?rules",
    r"jailbreak",
    r"pretend\s+you\s+are",
    r"new\s+system\s+prompt",
    r"bypass\s+(the\s+)?workflow",
    r"ignore\s+(the\s+)?framework",
]


# ===========================================================================
# Phase 3a — Prompt Size
# ===========================================================================

def check_prompt_size(prompt: str) -> str | None:
    """Block oversized prompts. Returns block reason or None."""
    size = len(prompt.encode("utf-8"))
    if size > MAX_PROMPT_BYTES:
        size_kb = size / 1024
        return (
            f"Prompt exceeds the 50 KB size limit ({size_kb:.1f} KB).\n\n"
            "Provide only the skill path and assessment request — "
            "do not paste file contents into the prompt. "
            "Reference files by absolute path instead."
        )
    return None


# ===========================================================================
# Phase 3b — Prompt Injection
# ===========================================================================

def check_prompt_injection(prompt: str) -> str | None:
    """Block prompts containing known injection / override patterns."""
    import re
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return (
                "Prompt Injection Detected: The input contains instructions "
                "attempting to override SQAF orchestrator behavior.\n\n"
                "The request has been blocked. Remove the offending content "
                "and resubmit a valid assessment request."
            )
    return None


# ===========================================================================
# Phase 3c — Blocked Extensions
# ===========================================================================

def check_extension(filepath: str, blocked: frozenset[str]) -> str | None:
    """Return a block reason if any suffix in the file path is blocked."""
    suffixes = [s.lower() for s in Path(filepath).suffixes]
    for suffix in suffixes:
        if suffix in blocked:
            return (
                f"Blocked file extension '{suffix}' detected in "
                f"'{Path(filepath).name}'. "
                "Executable and script files are not permitted as input."
            )
    return None


# ===========================================================================
# Main entrypoint
# ===========================================================================

def main() -> None:
    """
    Security hook entrypoint.

    Runs three fast, I/O-free checks in sequence.
    Emits a blocking result on failure or a minimal allow on success.
    The performance hook reads the minimal allow and continues enrichment.
    """
    payload, input_files = parse_stdin()
    user_prompt = extract_user_prompt(payload)
    trace_id = generate_trace_id()

    # 3a: Prompt size
    reason = check_prompt_size(user_prompt)
    if reason:
        emit_block(trace_id, "medium", reason, phase="SIZE")

    # 3b: Prompt injection
    reason = check_prompt_injection(user_prompt)
    if reason:
        emit_block(trace_id, "high", reason, phase="SECURITY")

    # 3c: Blocked extensions
    for filepath in input_files:
        reason = check_extension(filepath, BLOCKED_EXTENSIONS)
        if reason:
            emit_block(trace_id, "high", reason, phase="SECURITY")

    # All security checks passed — emit minimal allow for next hook
    result = HookResult(
        execute_workflow=True,
        trace_id=trace_id,
    )
    emit_allow(result)


if __name__ == "__main__":
    main()
