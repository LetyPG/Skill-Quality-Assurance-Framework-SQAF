#!/usr/bin/env python3
"""
SQAF Performance Hook  —  UserPromptSubmit Phases 1, 2, 4

Single responsibility: validate assessment inputs and enrich the orchestrator
context with verified paths and the detected user language.

Checks (fail-closed, in order):
    Phase 1 — SKILL.md Block
        1a. Single-skill guard   (exactly one SKILL.md path in prompt)
        1b. Absolute path check  (must start with /)
        1c. Format check         (must end with /SKILL.md)
        1d. Disk existence check (file must exist on filesystem)
        1e. File size check      (≤ 500 KB)

    Phase 2 — eval.json Block   (only if eval.json is referenced in prompt)
        2a. Absolute path check
        2b. Disk existence check
        2c. Valid JSON check     (file must be parseable)
        2d. File size check      (≤ 5 MB)

    Phase 4 — Language Detection
        Detect user language offline via lingua (optional dep).
        Inject language_rule into context for the orchestrator.
        Always emits execute_workflow: true when reached.

Runs AFTER sqaf_security_hook.py in the UserPromptSubmit pipeline.
Only executes if the security hook allowed the request.

Output:
    execute_workflow: false  → runtime blocks; user sees block_reason
    execute_workflow: true   → full enriched allow (orchestrator contract)
        Fields: skill_path, eval_path, language, language_rule,
                confidence, trace_id, sanitized_context

Exit code is always 0 — a non-zero exit crashes some agent runtimes.

Dependencies:
    Required : stdlib only
    Optional : lingua-language-detector  (pip install lingua-language-detector)
               python-magic              (pip install python-magic)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, Tuple

# Ensure project root is in sys.path when script is executed directly via python3
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from hooks.hook_contract import HookContext, HookResult
from hooks.hook_utils import (
    emit_allow,
    emit_block,
    extract_user_prompt,
    generate_trace_id,
    parse_stdin,
)

# ---------------------------------------------------------------------------
# Optional imports — graceful degradation
# ---------------------------------------------------------------------------

try:
    import magic  # type: ignore[import-untyped]
    _MAGIC_AVAILABLE = True
except ImportError:
    _MAGIC_AVAILABLE = False

try:
    from lingua import Language, LanguageDetectorBuilder  # type: ignore[import-untyped]
    _LINGUA_AVAILABLE = True
except ImportError:
    _LINGUA_AVAILABLE = False

# ---------------------------------------------------------------------------
# Size limits
# ---------------------------------------------------------------------------

MAX_SKILL_MD_BYTES: int  = 500 * 1024        # 500 KB
MAX_EVAL_JSON_BYTES: int = 5 * 1024 * 1024   # 5 MB

BLOCKED_MIME_PREFIXES: tuple[str, ...] = (
    "application/x-executable",
    "application/x-sharedlib",
    "application/x-dosexec",
    "application/x-msdownload",
    "application/x-sh",
    "application/x-python",
    "application/java-archive",
    "application/vnd.ms-office",
    "application/zip",
    "application/x-zip",
)

# ---------------------------------------------------------------------------
# Input patterns
# ---------------------------------------------------------------------------

import re  # noqa: E402 — imported here to keep constants grouped above

SKILL_PATH_PATTERN = re.compile(
    r"((?:/[\w.\-]+)+/SKILL\.md)",
    re.IGNORECASE,
)

EVAL_PATH_PATTERN = re.compile(
    r"((?:/[\w.\-]+)+/eval(?:s)?\.json)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Language detection constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD: float = 0.75

LANGUAGE_RULES: dict[str, str] = {
    "Spanish": (
        "All SQAF assessment artifact text SHALL be written in Spanish. "
        "This includes: all findings, recommendations, risk descriptions, "
        "executive summaries, and the full body of skill-quality-report.md. "
        "JSON field names (e.g. 'findings', 'recommendations', 'score') "
        "remain in English. Do not mix languages in final deliverables."
    ),
    "English": (
        "All SQAF assessment artifact text SHALL be written in English."
    ),
    "Portuguese": (
        "All SQAF assessment artifact text SHALL be written in Portuguese. "
        "JSON field names remain in English. "
        "Do not mix languages in final deliverables."
    ),
    "French": (
        "All SQAF assessment artifact text SHALL be written in French. "
        "JSON field names remain in English. "
        "Do not mix languages in final deliverables."
    ),
    "German": (
        "All SQAF assessment artifact text SHALL be written in German. "
        "JSON field names remain in English. "
        "Do not mix languages in final deliverables."
    ),
    "Italian": (
        "All SQAF assessment artifact text SHALL be written in Italian. "
        "JSON field names remain in English. "
        "Do not mix languages in final deliverables."
    ),
}

_LINGUA_LANGUAGE_MAP: dict[str, str] = {
    "SPANISH": "Spanish",
    "ENGLISH": "English",
    "PORTUGUESE": "Portuguese",
    "FRENCH": "French",
    "GERMAN": "German",
    "ITALIAN": "Italian",
}


# ===========================================================================
# Phase 1 — SKILL.md Block
# ===========================================================================

def validate_skill_md(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate the SKILL.md reference in the user prompt.

    Returns:
        (block_reason, skill_path) — block_reason is None on success.
    """
    matches = SKILL_PATH_PATTERN.findall(prompt)

    # 1a: single-skill guard
    if len(matches) == 0:
        return (
            "No SKILL.md path found in the request.\n\n"
            "SQAF requires exactly one absolute skill path.\n"
            "Required format:\n"
            "  Assess the quality of the following skill: "
            "/absolute/path/to/skill/SKILL.md",
            None,
        )
    if len(matches) > 1:
        return (
            f"Multiple skill paths detected ({len(matches)} SKILL.md references).\n\n"
            "SQAF processes exactly one skill per assessment request.\n"
            "Please submit separate requests for each skill.",
            None,
        )

    skill_path = matches[0].strip()

    # 1b: absolute path
    if not skill_path.startswith("/"):
        return (
            f"Skill path must be absolute (starting with '/').\n"
            f"Received: '{skill_path}'\n\n"
            "Example: /home/user/my-project/skills/my-skill/SKILL.md",
            None,
        )

    # 1c: ends with SKILL.md (regex enforces this — defensive check)
    if not skill_path.endswith("SKILL.md"):
        return (f"Path must end with 'SKILL.md'. Received: '{skill_path}'", None)

    # 1d: disk existence
    p = Path(skill_path)
    if not p.exists():
        return (
            f"SKILL.md not found on disk: '{skill_path}'\n\n"
            "Verify the path is correct and the skill directory exists.",
            None,
        )
    if not p.is_file():
        return (f"'{skill_path}' exists but is not a file.", None)

    # 1e: file size
    size = p.stat().st_size
    if size > MAX_SKILL_MD_BYTES:
        size_kb = size / 1024
        return (
            f"SKILL.md exceeds the 500 KB size limit ({size_kb:.1f} KB).\n\n"
            "Split large reference material into separate files loaded "
            "via progressive disclosure.",
            None,
        )

    return None, skill_path


# ===========================================================================
# Phase 2 — eval.json Block
# ===========================================================================

def validate_eval_json(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate the eval.json reference in the user prompt.
    Skipped entirely if eval.json is not referenced.

    Returns:
        (block_reason, eval_path)
        Returns (None, None) when eval is not referenced — not an error.
    """
    matches = EVAL_PATH_PATTERN.findall(prompt)

    if not matches:
        return None, None  # eval not referenced — skip

    if len(matches) > 1:
        return (
            f"Multiple eval.json paths detected ({len(matches)}).\n\n"
            "Provide at most one eval.json per assessment request.",
            None,
        )

    eval_path = matches[0].strip()

    # 2a: absolute path
    if not eval_path.startswith("/"):
        return (
            f"eval.json path must be absolute (starting with '/').\n"
            f"Received: '{eval_path}'",
            None,
        )

    # 2b: disk existence
    p = Path(eval_path)
    if not p.exists() or not p.is_file():
        return (
            f"eval.json not found on disk: '{eval_path}'\n\n"
            "Verify the path is correct or omit the eval reference "
            "if not running execution review.",
            None,
        )

    # 2c: valid JSON
    try:
        with open(p, encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as exc:
        return (
            f"eval.json is not valid JSON: {exc}\n\n"
            "Fix the eval.json file before requesting execution review.",
            None,
        )

    # 2d: file size
    size = p.stat().st_size
    if size > MAX_EVAL_JSON_BYTES:
        size_mb = size / (1024 * 1024)
        return (
            f"eval.json exceeds the 5 MB size limit ({size_mb:.2f} MB).\n\n"
            "Consider splitting evaluation definitions into smaller files.",
            None,
        )

    return None, eval_path


# ===========================================================================
# Phase 4 — Language Detection
# ===========================================================================

def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of the user prompt using lingua (offline).

    Returns:
        (language_name, confidence)
        Falls back to ("English", 0.0) when:
          - lingua is not installed
          - detected language is unsupported
          - confidence < CONFIDENCE_THRESHOLD
    """
    if not _LINGUA_AVAILABLE or not text or not text.strip():
        return ("English", 0.0)

    try:
        target_languages = [
            Language.ENGLISH,
            Language.SPANISH,
            Language.PORTUGUESE,
            Language.FRENCH,
            Language.GERMAN,
            Language.ITALIAN,
        ]
        detector = (
            LanguageDetectorBuilder
            .from_languages(*target_languages)
            .with_minimum_relative_distance(0.1)
            .build()
        )
        result = detector.detect_language_of(text)
        if result is None:
            return ("English", 0.0)

        lang_name = _LINGUA_LANGUAGE_MAP.get(result.name)
        if lang_name is None:
            return ("English", 0.0)

        confidence_values = detector.compute_language_confidence_values(text)
        confidence = 0.0
        for cv in confidence_values:
            if cv.language == result:
                confidence = round(cv.value, 4)
                break

        if confidence < CONFIDENCE_THRESHOLD:
            return ("English", confidence)

        return (lang_name, confidence)

    except Exception:  # noqa: BLE001
        return ("English", 0.0)


def build_allow_result(
    context: HookContext,
    trace_id: str,
    skill_path: str,
    eval_path: Optional[str],
) -> HookResult:
    """
    Build the final enriched HookResult — the orchestrator contract.

    Includes: skill_path, eval_path, language, language_rule,
              confidence, trace_id, sanitized_context.
    """
    detected_lang, confidence = detect_language(context.user_prompt)
    rule = LANGUAGE_RULES.get(detected_lang, LANGUAGE_RULES["English"])

    return HookResult(
        execute_workflow=True,
        trace_id=trace_id,
        skill_path=skill_path,
        eval_path=eval_path,
        language=detected_lang,
        confidence=confidence,
        language_rule=rule,
        sanitized_context={
            "user_prompt": context.user_prompt,
            "input_files": context.input_files,
        },
    )


# ===========================================================================
# Main entrypoint
# ===========================================================================

def main() -> None:
    """
    Performance hook entrypoint.

    Validates SKILL.md and eval.json from disk, detects user language,
    and emits the full enriched HookResult (orchestrator contract).
    Runs after sqaf_security_hook.py has already cleared the request.
    """
    payload, input_files = parse_stdin()
    user_prompt = extract_user_prompt(payload)
    trace_id = generate_trace_id()

    # ── Phase 1: SKILL.md Block ──────────────────────────────────────────────
    reason, skill_path = validate_skill_md(user_prompt)
    if reason:
        emit_block(trace_id, "high", reason, phase="SKILL_MD")

    # ── Phase 2: eval.json Block ─────────────────────────────────────────────
    reason, eval_path = validate_eval_json(user_prompt)
    if reason:
        emit_block(trace_id, "high", reason, phase="EVAL_JSON")

    # ── Phase 4: Language Detection + emit orchestrator contract ─────────────
    context = HookContext(user_prompt=user_prompt, input_files=input_files)
    result = build_allow_result(context, trace_id, skill_path, eval_path)  # type: ignore[arg-type]
    emit_allow(result)


if __name__ == "__main__":
    main()
