"""
OrchestratorRunner — receives a validated AssessmentSession and executes
the assessment workflow.

Invariants (from spec):
  - Never prompts for input.
  - Never modifies the session.
  - Never performs skill discovery or session building.
  - Delegates execution entirely to runner.trigger().
"""
from __future__ import annotations

import sys

from sqaf.runner import trigger
from sqaf.session import AssessmentSession
from sqaf.ui.renderer import Renderer


class OrchestratorRunner:

    def __init__(self, session: AssessmentSession, renderer: Renderer) -> None:
        self._session = session
        self._renderer = renderer

    def execute(self) -> None:
        """Show confirmation screen, then launch if confirmed."""
        self._show_summary()
        if not self._renderer.confirm("Start Assessment?", default=True):
            self._renderer.blank()
            self._renderer.error("Assessment cancelled.")
            return

        self._renderer.blank()
        self._renderer.success("Starting Skill Assessment...\n")
        trigger(self._session)

        # ── Post-trigger precondition check ────────────────────────────────────
        # When an agent CLI runs sqaf as a subprocess, stdout is PIPED — the
        # agent reads the trigger above and acts on it. Assessment proceeds.
        #
        # When a human runs sqaf directly in a terminal, stdout IS a TTY —
        # nothing is reading the trigger. The assessment will NOT be produced.
        # In this case, show a clear diagnostic instead of a false success.
        if sys.stdout.isatty():
            self._show_no_agent_error()

    def _show_summary(self) -> None:
        self._renderer.step(4, 4, "Review Summary")
        self._renderer.info(
            "Skill", self._session.assessment_name or self._session.skill_path or ""
        )
        self._renderer.info(
            "Execution Review",
            "Enabled" if self._session.run_eval else "Skipped",
        )
        self._renderer.info("Output", self._session.output_directory)
        self._renderer.info("Mode", self._session.execution_mode)
        self._renderer.blank()

    def _show_no_agent_error(self) -> None:
        """
        Shown when the trigger was emitted to an interactive terminal — meaning
        no agent CLI is reading stdout and the assessment will not be executed.
        """
        self._renderer.blank()
        self._renderer.error(
            "No assessment produced — agent CLI not detected."
        )
        self._renderer.blank()
        self._renderer.info("Root cause", "sqaf was run in a standalone terminal.")
        self._renderer.info(
            "",
            "The trigger above requires an active AI agent CLI to act on it.",
        )
        self._renderer.info(
            "",
            "No agent was found reading stdout, so no artifacts were created.",
        )
        self._renderer.blank()
        self._renderer.info("How to fix", "Run sqaf inside an active agent CLI session:")
        self._renderer.blank()
        self._renderer.paragraph("  Claude Code CLI   → claude (then run sqaf from within the session)")
        self._renderer.paragraph("  Antigravity       → antigravity (then run sqaf from within the session)")
        self._renderer.paragraph("  Gemini CLI        → gemini (then run sqaf from within the session)")
        self._renderer.blank()
        self._renderer.info(
            "Alternatively",
            "Pass the skill path directly in non-interactive mode:",
        )
        self._renderer.paragraph(
            "  sqaf <path/to/skill> --eval n --non-interactive"
        )
        self._renderer.paragraph(
            "  and pipe the output to your agent runner."
        )
        self._renderer.blank()
        self._renderer.info(
            "Docs",
            "See docs/cli_user_guide.md → Agent Precondition section.",
        )
        self._renderer.blank()
        sys.exit(1)
