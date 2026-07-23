"""
Tests for SessionBuilder.

Uses MockRenderer to exercise the builder without a real terminal,
validating both the non-interactive (all args pre-filled) and
interactive (missing args, prompts answered via MockRenderer) paths.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sqaf.session_builder import SessionBuilder

# ── Mock renderer ──────────────────────────────────────────────────────────────

class MockRenderer:
    """Records all render calls and returns pre-configured answers for prompts."""

    def __init__(self):
        self.calls: list[tuple] = []
        self._prompts: list[str] = []
        self._confirms: list[bool] = []

    def queue_prompts(self, *answers: str) -> None:
        self._prompts.extend(answers)

    def queue_confirms(self, *answers: bool) -> None:
        self._confirms.extend(answers)

    def header(self, title: str) -> None:
        self.calls.append(("header", title))

    def step(self, n: int, total: int, label: str) -> None:
        self.calls.append(("step", n, total, label))

    def info(self, label: str, value: str) -> None:
        self.calls.append(("info", label, value))

    def success(self, message: str) -> None:
        self.calls.append(("success", message))

    def error(self, message: str) -> None:
        self.calls.append(("error", message))

    def numbered_list(self, items: list[str]) -> None:
        self.calls.append(("numbered_list", items))

    def blank(self) -> None:
        self.calls.append(("blank",))

    def paragraph(self, text: str) -> None:
        self.calls.append(("paragraph", text))

    def prompt(self, question: str, default: str | None = None) -> str:
        self.calls.append(("prompt", question))
        return self._prompts.pop(0) if self._prompts else (default or "")

    def confirm(self, question: str, default: bool = True) -> bool:
        self.calls.append(("confirm", question))
        return self._confirms.pop(0) if self._confirms else default


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_skill(tmp_path: Path, name: str = "test-skill", with_evals: bool = False) -> Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}")
    if with_evals:
        (skill_dir / "eval.json").write_text("{}")
    return skill_dir


# ── Non-interactive (all pre-filled) ──────────────────────────────────────────

class TestNonInteractive:
    def test_builds_session_from_all_args(self, tmp_path):
        skill = make_skill(tmp_path)
        renderer = MockRenderer()
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=True,
            pre_filled_output="out/",
            execution_mode="non-interactive",
        ).build()
        assert session.skill_path == str(skill.resolve())
        assert session.run_eval is True
        assert session.output_directory == "out/"
        assert session.execution_mode == "non-interactive"

    def test_raises_when_skill_missing(self, tmp_path):
        renderer = MockRenderer()
        with pytest.raises(ValueError, match="non-interactive"):
            SessionBuilder(
                renderer=renderer,
                pre_filled_skill=None,
                pre_filled_eval=True,
                execution_mode="non-interactive",
            ).build()

    def test_raises_when_skill_path_invalid(self, tmp_path):
        renderer = MockRenderer()
        with pytest.raises(ValueError):
            SessionBuilder(
                renderer=renderer,
                pre_filled_skill="/does/not/exist",
                pre_filled_eval=False,
                execution_mode="non-interactive",
            ).build()

    def test_defaults_eval_to_false_when_not_provided(self, tmp_path):
        skill = make_skill(tmp_path)
        renderer = MockRenderer()
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=None,
            execution_mode="non-interactive",
        ).build()
        assert session.run_eval is False

    def test_defaults_output_directory(self, tmp_path):
        skill = make_skill(tmp_path)
        renderer = MockRenderer()
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=False,
            pre_filled_output=None,
            execution_mode="non-interactive",
        ).build()
        assert session.output_directory == "assessment/"


# ── Interactive (prompts answered via MockRenderer) ────────────────────────────

class TestInteractive:
    def test_prompts_for_skill_by_number(self, tmp_path):
        skill = make_skill(tmp_path, "my-skill")
        renderer = MockRenderer()
        # User types the skill path — selection is automatic once path is valid
        renderer.queue_prompts(str(skill))
        renderer.queue_confirms(False)    # eval: No
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=None,
            execution_mode="interactive",
        ).build()
        assert session.skill_path is not None
        assert Path(session.skill_path).name == "my-skill"

    def test_prompts_for_skill_by_name(self, tmp_path):
        skill = make_skill(tmp_path, "qa-reviewer")
        renderer = MockRenderer()
        # User types the skill path — selection is automatic once path is valid
        renderer.queue_prompts(str(skill))
        renderer.queue_confirms(False)
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=None,
            execution_mode="interactive",
        ).build()
        assert session.skill_path is not None
        assert Path(session.skill_path).name == "qa-reviewer"

    def test_skips_eval_prompt_when_no_evals_present(self, tmp_path):
        skill = make_skill(tmp_path, "no-eval-skill", with_evals=False)
        renderer = MockRenderer()
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=None,
            execution_mode="interactive",
        ).build()
        assert session.run_eval is False
        # confirm should NOT have been called for eval
        confirm_calls = [c for c in renderer.calls if c[0] == "confirm"]
        assert confirm_calls == []

    def test_prompts_eval_when_evals_present(self, tmp_path):
        skill = make_skill(tmp_path, "eval-skill", with_evals=True)
        renderer = MockRenderer()
        renderer.queue_confirms(True)   # eval: Yes
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=None,
            execution_mode="interactive",
        ).build()
        assert session.run_eval is True

    def test_assessment_name_matches_directory_name(self, tmp_path):
        skill = make_skill(tmp_path, "intent-reviewer")
        renderer = MockRenderer()
        session = SessionBuilder(
            renderer=renderer,
            pre_filled_skill=str(skill),
            pre_filled_eval=False,
            execution_mode="non-interactive",
        ).build()
        assert session.assessment_name == "intent-reviewer"
