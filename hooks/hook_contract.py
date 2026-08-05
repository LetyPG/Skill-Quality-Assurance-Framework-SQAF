"""
Stable Hook Interface Contract — SQAF

Single source of truth for the interface between the SQAF security hook
and the orchestrator runtime. This file defines ONLY data structures —
no logic, no side-effects.

Adapted from: Pro09/qa-requirements-analyzer-agents-team/hooks/hook_contract.py
SQAF additions: block_phase, skill_path, eval_path fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# HookExtensions — backward-compatible optional policy overrides.
# New fields can be added here without breaking existing hook implementations.
# ---------------------------------------------------------------------------

@dataclass
class HookExtensions:
    """Optional policy overrides passed from .agent/settings.json at runtime."""
    allowed_extensions: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HookContext — stable input structure.
# The agent runtime builds this from the UserPromptSubmit payload and
# passes it to the hook.
# ---------------------------------------------------------------------------

@dataclass
class HookContext:
    """Input to every hook invocation."""
    user_prompt: str
    input_files: list[str]
    runtime_config: dict | None = None
    extensions: HookExtensions | None = None


# ---------------------------------------------------------------------------
# HookResult — stable output structure.
# The hook MUST return a value serialisable to this structure.
#
# The agent runtime reads execute_workflow to decide whether to proceed.
# All other fields are enrichment for the orchestrator or for audit logs.
# ---------------------------------------------------------------------------

@dataclass
class HookResult:
    """Output contract for every SQAF hook invocation."""

    # ── Master gate (always required) ─────────────────────────────────────────
    execute_workflow: bool
    trace_id: str

    # ── Block metadata (when execute_workflow is False) ────────────────────────
    risk_level: Literal["low", "medium", "high"] | None = None
    block_reason: str | None = None
    block_phase: Literal["SKILL_MD", "EVAL_JSON", "SECURITY", "SIZE"] | None = None

    # ── Allow enrichment (when execute_workflow is True) ──────────────────────
    skill_path: str | None = None        # Validated absolute SKILL.md path
    eval_path: str | None = None         # Validated eval.json path (if present)
    language: str | None = None
    confidence: float | None = None
    language_rule: str | None = None
    sanitized_context: dict | None = None

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON emission to stdout."""
        return {
            "execute_workflow": self.execute_workflow,
            "trace_id": self.trace_id,
            "risk_level": self.risk_level,
            "block_reason": self.block_reason,
            "block_phase": self.block_phase,
            "skill_path": self.skill_path,
            "eval_path": self.eval_path,
            "language": self.language,
            "confidence": self.confidence,
            "language_rule": self.language_rule,
            "sanitized_context": self.sanitized_context,
        }
