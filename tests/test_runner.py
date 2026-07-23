"""
Tests for sqaf.runner — trigger prompt builder and emitter.

Covers:
  - build_trigger_prompt output for design-only and full (eval-enabled) sessions
  - trigger() print mode writes to stdout
  - trigger() subprocess mode raises NotImplementedError (Phase 3 reserved)
  - trigger() unknown mode raises ValueError
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sqaf.runner import build_trigger_prompt, trigger
from sqaf.session import AssessmentSession

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_session(
    tmp_path: Path,
    skill_name: str = "test-skill",
    run_eval: bool = False,
    output: str = "assessment/",
) -> AssessmentSession:
    skill = tmp_path / skill_name
    skill.mkdir()
    (skill / "SKILL.md").write_text("")
    return AssessmentSession(
        skill_path=str(skill),
        run_eval=run_eval,
        output_directory=output,
        execution_mode="non-interactive",
    )


# ── build_trigger_prompt ───────────────────────────────────────────────────────

class TestBuildTriggerPrompt:

    def test_includes_skill_md_path(self, tmp_path):
        session = make_session(tmp_path)
        prompt = build_trigger_prompt(session)
        assert "SKILL.md" in prompt
        assert "test-skill" in prompt

    def test_design_only_includes_skip_clause(self, tmp_path):
        session = make_session(tmp_path, run_eval=False)
        prompt = build_trigger_prompt(session)
        assert "execution review skipped" in prompt
        assert "no evals provided" in prompt

    def test_eval_enabled_includes_eval_path(self, tmp_path):
        session = make_session(tmp_path, run_eval=True)
        prompt = build_trigger_prompt(session)
        assert "eval.json" in prompt
        assert "with evals at" in prompt

    def test_includes_output_directory(self, tmp_path):
        session = make_session(tmp_path, output="reports/")
        prompt = build_trigger_prompt(session)
        assert "reports/" in prompt
        assert "Store results in:" in prompt

    def test_prompt_is_multiline(self, tmp_path):
        session = make_session(tmp_path)
        prompt = build_trigger_prompt(session)
        lines = prompt.strip().splitlines()
        assert len(lines) >= 3, "Trigger must have at least 3 lines"

    def test_skill_path_present_in_first_line(self, tmp_path):
        session = make_session(tmp_path, skill_name="my-skill")
        prompt = build_trigger_prompt(session)
        first_line = prompt.splitlines()[0]
        assert "my-skill" in first_line

    def test_output_dir_present_in_last_line(self, tmp_path):
        session = make_session(tmp_path, output="out/")
        prompt = build_trigger_prompt(session)
        last_line = prompt.splitlines()[-1]
        assert "out/" in last_line


# ── trigger() ─────────────────────────────────────────────────────────────────

class TestTrigger:

    def test_print_mode_outputs_trigger_to_stdout(self, tmp_path, capsys):
        session = make_session(tmp_path)
        trigger(session, mode="print")
        captured = capsys.readouterr()
        assert "SKILL.md" in captured.out
        assert "Store results in:" in captured.out

    def test_print_mode_is_default(self, tmp_path, capsys):
        session = make_session(tmp_path)
        trigger(session)   # no mode arg
        captured = capsys.readouterr()
        assert "SKILL.md" in captured.out

    def test_subprocess_mode_raises_not_implemented(self, tmp_path):
        session = make_session(tmp_path)
        with pytest.raises(NotImplementedError, match="Phase 3"):
            trigger(session, mode="subprocess")

    def test_unknown_mode_raises_value_error(self, tmp_path):
        session = make_session(tmp_path)
        with pytest.raises(ValueError, match="Unknown runner mode"):
            trigger(session, mode="invalid")

    def test_output_matches_build_trigger_prompt(self, tmp_path, capsys):
        """trigger(print) must emit exactly what build_trigger_prompt returns."""
        session = make_session(tmp_path)
        expected = build_trigger_prompt(session)
        trigger(session)
        captured = capsys.readouterr()
        assert captured.out.strip() == expected.strip()
