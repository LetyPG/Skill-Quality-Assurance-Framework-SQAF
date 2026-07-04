"""
SessionBuilder — the key abstraction between the CLI and the orchestrator.

Single responsibility: collect enough information to produce a valid
AssessmentSession, regardless of whether the source is CLI arguments,
interactive prompts, or defaults.

Priority order for each field:
  1. CLI argument (pre_filled_*)
  2. Interactive prompt  (only when execution_mode == "interactive")
  3. Safe default        (for optional fields only)

The orchestrator never calls this class. It only receives a complete,
validated AssessmentSession.
"""
from __future__ import annotations

from pathlib import Path

from sqaf.session import AssessmentSession
from sqaf.skills_discovery import skill_has_evals
from sqaf.ui.renderer import Renderer


class SessionBuilder:

    def __init__(
        self,
        renderer: Renderer,
        pre_filled_skill: str | None = None,
        pre_filled_eval: bool | None = None,
        pre_filled_output: str | None = None,
        execution_mode: str = "interactive",
        workspace: str = ".",
    ) -> None:
        self._r = renderer
        self._skill = pre_filled_skill
        self._eval = pre_filled_eval
        self._output = pre_filled_output
        self._mode = execution_mode
        self._workspace = workspace

    # ── Public ─────────────────────────────────────────────────────────────────

    def build(self) -> AssessmentSession:
        """Collect all fields and return a validated AssessmentSession."""
        session = AssessmentSession(
            execution_mode=self._mode,
            workspace=self._workspace,
        )

        session.skill_path = self._resolve_skill_path()
        session.run_eval = self._resolve_run_eval(session.skill_path)
        session.output_directory = self._resolve_output_dir()

        if session.skill_path:
            session.assessment_name = Path(session.skill_path).name

        errors = session.validation_errors()
        if errors:
            for e in errors:
                self._r.error(e)
            raise ValueError(f"Session validation failed: {errors}")

        return session

    # ── Skill path ─────────────────────────────────────────────────────────────

    def _resolve_skill_path(self) -> str:
        if self._skill is not None:
            p = Path(self._skill)
            if p.exists() and (p / "SKILL.md").exists():
                self._r.success(f"Skill: {p.name}")
                return str(p.resolve())
            self._r.error(
                f"Skill not found or missing SKILL.md: {self._skill}"
            )
            # Fall through to interactive if available, else raise
        if self._mode != "interactive":
            raise ValueError(
                "--skill is required in non-interactive mode "
                "(or the provided path was invalid)"
            )
        return self._prompt_skill_selection()

    def _prompt_skill_selection(self) -> str:
        self._r.step(1, 4, "Select the skill to review")
        self._r.info("Note", "Only one skill can be assessed at a time.")
        self._r.blank()

        # Ask the user for the skill path and validate it.
        while True:
            path_input = self._r.prompt(
                "Enter the path to the skill directory (must contain SKILL.md)"
            )
            p = Path(path_input.strip())
            if p.exists() and (p / "SKILL.md").exists():
                break
            self._r.error(
                f"Path not found or missing SKILL.md: {path_input!r}. Please try again."
            )

        skill_path = str(p.resolve())
        skill_name = p.name

        # Confirm selection — no further input needed once path is valid.
        self._r.blank()
        self._r.success(f"Skill selected: {skill_name}")
        return skill_path

    # ── Eval ───────────────────────────────────────────────────────────────────

    def _resolve_run_eval(self, skill_path: str | None) -> bool:
        if self._eval is not None:
            return self._eval
        if self._mode != "interactive":
            return False   # safe default: skip eval in non-interactive
        return self._prompt_eval(skill_path)

    def _prompt_eval(self, skill_path: str | None) -> bool:
        self._r.step(2, 4, "Execution Review")
        has_evals = skill_path is not None and skill_has_evals(skill_path)
        if has_evals:
            self._r.success("This skill contains an evals/ directory.\n")
            return self._r.confirm(
                "Would you like to perform an execution assessment?",
                default=True,
            )
        self._r.info(
            "Note",
            "No evals/ directory or eval.json found — execution review skipped.",
        )
        return False

    # ── Output directory ───────────────────────────────────────────────────────

    def _resolve_output_dir(self) -> str:
        if self._output:
            return self._output
        default = "assessment/"
        if self._mode != "interactive":
            return default
        return self._prompt_output_dir(default)

    def _prompt_output_dir(self, default: str) -> str:
        self._r.step(3, 4, "Output Directory")
        result = self._r.prompt(
            "Assessment output directory", default=default
        )
        return result if result else default
