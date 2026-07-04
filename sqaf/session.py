"""AssessmentSession — the single immutable data object shared by all layers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AssessmentSession:
    """
    Holds all information needed to run an assessment.
    Populated entirely by SessionBuilder before the orchestrator starts.
    The orchestrator never modifies this object.
    """

    # ── Core inputs ────────────────────────────────────────────────────────────
    skill_path: str | None = None
    run_eval: bool | None = None
    output_directory: str = "assessment/"
    workspace: str = "."

    # ── Derived / metadata (auto-populated) ────────────────────────────────────
    assessment_name: str | None = None
    framework_version: str = "0.1.0"
    execution_mode: str = "interactive"   # "interactive" | "non-interactive"
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.skill_path and self.assessment_name is None:
            self.assessment_name = Path(self.skill_path).name

    # ── Validation ─────────────────────────────────────────────────────────────

    def is_valid(self) -> bool:
        """True only when all mandatory fields are present and the skill path exists."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> list[str]:
        """Returns human-readable reasons why the session is not yet valid."""
        errors: list[str] = []

        if self.skill_path is None:
            errors.append("skill_path is required")
        else:
            p = Path(self.skill_path)
            if not p.exists():
                errors.append(f"Skill path does not exist: {self.skill_path}")
            elif not (p / "SKILL.md").exists():
                errors.append(f"SKILL.md not found in: {self.skill_path}")

        if self.run_eval is None:
            errors.append("run_eval must be True or False")

        return errors
