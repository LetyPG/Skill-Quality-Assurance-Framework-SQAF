"""
Runner — agent-agnostic workflow trigger (Phase 1: print mode).

Builds the orchestrator trigger prompt from a validated AssessmentSession
and emits it to stdout. The embedding AI agent reads this and acts on it.

Phase 3 will add a --runner flag for subprocess invocation.
"""
from __future__ import annotations

from sqaf.session import AssessmentSession


def build_trigger_prompt(session: AssessmentSession) -> str:
    """Constructs the orchestrator trigger message from a validated session."""
    eval_clause = (
        f"with evals at {session.skill_path}/eval.json"
        if session.run_eval
        else "(execution review skipped — no evals provided)"
    )
    lines = [
        f"Assess the quality of the following skill: {session.skill_path}/SKILL.md",
        eval_clause,
        f"Store results in: {session.output_directory}",
    ]
    return "\n".join(lines)


def trigger(session: AssessmentSession, mode: str = "print") -> None:
    """
    Triggers the assessment workflow.

    Modes
    -----
    print (default)
        Prints the orchestrator trigger prompt to stdout.
        All agent CLI tools (Claude Code, Antigravity, Gemini CLI, etc.)
        read this and act on it — no coupling to any specific agent binary.
    subprocess
        Reserved for Phase 3.
    """
    if mode == "print":
        print(build_trigger_prompt(session))
    elif mode == "subprocess":
        raise NotImplementedError(
            "Subprocess runner is reserved for Phase 3. "
            "Use mode='print' for now."
        )
    else:
        raise ValueError(f"Unknown runner mode: {mode!r}")
