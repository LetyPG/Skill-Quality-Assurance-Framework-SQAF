"""
CLI entry point — argument parsing and mode detection only.

Responsibilities:
  1. Parse argv.
  2. Detect execution mode (interactive vs non-interactive).
  3. Select renderer (TTY-aware).
  4. Hand off to SessionBuilder → OrchestratorRunner.

Contains zero assessment logic.
"""
from __future__ import annotations

import argparse
import sys

from sqaf.orchestrator import OrchestratorRunner
from sqaf.session_builder import SessionBuilder
from sqaf.ui.banner import render_banner
from sqaf.ui.renderer import get_renderer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sqaf",
        description="Skill Quality Assessment Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  sqaf                              # interactive guided mode\n"
            "  sqaf skills/my-skill              # pre-fill skill, prompt for the rest\n"
            "  sqaf skills/my-skill --eval y     # pre-fill skill + eval flag\n"
            "  sqaf skills/my-skill --eval y --non-interactive  # fully automated\n"
        ),
    )
    parser.add_argument(
        "skill_path",
        nargs="?",
        default=None,
        metavar="SKILL_PATH",
        help="Path to the skill directory (must contain SKILL.md)",
    )
    parser.add_argument(
        "--eval",
        dest="run_eval",
        choices=["y", "n", "yes", "no"],
        default=None,
        metavar="y|n",
        help="Run execution review (y/n)",
    )
    parser.add_argument(
        "--output",
        dest="output_directory",
        default=None,
        metavar="DIR",
        help="Output directory for assessment artifacts (default: assessment/)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Disable interactive prompts; all required values must be provided via flags",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    run_eval: bool | None = None
    if args.run_eval is not None:
        run_eval = args.run_eval in ("y", "yes")

    execution_mode = "non-interactive" if args.non_interactive else "interactive"
    renderer = get_renderer()

    render_banner()
    renderer.header("Skill Quality Assessment Framework (SQAF)")

    if execution_mode == "interactive":
        renderer.blank()
        renderer.paragraph(
            "Welcome! I'll guide you through a structured skill quality assessment."
        )
        renderer.blank()
        renderer.paragraph(
            "SQAF uses a shift-left QA approach: it evaluates your AI skill's design"
        )
        renderer.paragraph(
            "quality before execution — identifying ambiguities, hallucination risks,"
        )
        renderer.paragraph(
            "and instruction gaps early, at significantly lower cost."
        )
        renderer.blank()
        renderer.paragraph(
            "After your assessment, use the quality report to refine your skill with"
        )
        renderer.paragraph(
            "an improvement agent, then re-assess once. This is far more efficient"
        )
        renderer.paragraph(
            "than running multiple full assessments iteratively."
        )
        renderer.blank()
        renderer.info("⚠ Precondition", "sqaf must be run inside an active AI agent CLI session.")
        renderer.info("", "(Claude Code, Antigravity, Gemini CLI, etc.)")
        renderer.info("", "The assessment trigger is printed to stdout for your agent to act on.")
        renderer.info("", "Without an active agent, no assessment artifacts will be produced.")
        renderer.blank()

    try:
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=args.skill_path,
            pre_filled_eval=run_eval,
            pre_filled_output=args.output_directory,
            execution_mode=execution_mode,
        ).build()
    except (ValueError, KeyboardInterrupt):
        sys.exit(1)

    OrchestratorRunner(session=session, renderer=renderer).execute()
