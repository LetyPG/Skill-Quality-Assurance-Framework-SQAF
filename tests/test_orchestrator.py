"""
Tests for sqaf.orchestrator — OrchestratorRunner.

Covers:
  - Cancelled assessment (confirm=False): error shown, trigger NOT called
  - Confirmed assessment in non-TTY (agent mode): trigger called, no exit
  - Confirmed assessment in TTY (standalone): trigger called, then exits with code 1
  - Summary rendering: correct fields from session
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from sqaf.orchestrator import OrchestratorRunner
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
        execution_mode="interactive",
    )


class MockRenderer:
    """Minimal mock renderer for orchestrator tests."""

    def __init__(self, confirm_response: bool = True) -> None:
        self.calls: list[tuple] = []
        self._confirm_response = confirm_response

    def header(self, title: str) -> None:
        self.calls.append(("header", title))

    def step(self, n: int, total: int, label: str) -> None:
        self.calls.append(("step", n, total, label))

    def info(self, label: str, value: str) -> None:
        self.calls.append(("info", label, value))

    def blank(self) -> None:
        self.calls.append(("blank",))

    def paragraph(self, text: str) -> None:
        self.calls.append(("paragraph", text))

    def success(self, message: str) -> None:
        self.calls.append(("success", message))

    def error(self, message: str) -> None:
        self.calls.append(("error", message))

    def numbered_list(self, items: list[str]) -> None:
        self.calls.append(("numbered_list", items))

    def prompt(self, question: str, default: str | None = None) -> str:
        self.calls.append(("prompt", question))
        return default or ""

    def confirm(self, question: str, default: bool = True) -> bool:
        self.calls.append(("confirm", question))
        return self._confirm_response

    def _call_types(self) -> list[str]:
        return [c[0] for c in self.calls]


# ── Cancellation ───────────────────────────────────────────────────────────────

class TestCancellation:

    def test_cancelled_shows_error_message(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=False)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        runner.execute()
        assert "error" in renderer._call_types()

    def test_cancelled_does_not_call_trigger(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=False)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger") as mock_trigger:
            runner.execute()
        mock_trigger.assert_not_called()

    def test_cancelled_does_not_exit(self, tmp_path):
        """Cancellation must return normally — not sys.exit."""
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=False)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        # Should complete without raising SystemExit
        runner.execute()


# ── Confirmed — agent mode (non-TTY) ──────────────────────────────────────────

class TestConfirmedNonTTY:

    def test_trigger_is_called(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger") as mock_trigger, patch.object(sys.stdout, "isatty", return_value=False):
                runner.execute()
        mock_trigger.assert_called_once_with(session)

    def test_does_not_exit(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger"), patch.object(sys.stdout, "isatty", return_value=False):
                # Must complete without SystemExit
                runner.execute()

    def test_no_agent_error_not_shown(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger"), patch.object(sys.stdout, "isatty", return_value=False):
                runner.execute()
        errors = [c for c in renderer.calls if c[0] == "error"]
        assert not errors, "No error should be shown when agent is present (non-TTY)"


# ── Confirmed — standalone terminal (TTY) ─────────────────────────────────────

class TestConfirmedTTY:

    def test_trigger_is_still_called(self, tmp_path):
        """Trigger must be emitted before the error — agents piping output still get it."""
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger") as mock_trigger, patch.object(sys.stdout, "isatty", return_value=True):
                with pytest.raises(SystemExit):
                    runner.execute()
        mock_trigger.assert_called_once_with(session)

    def test_exits_with_code_1(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger"), patch.object(sys.stdout, "isatty", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    runner.execute()
        assert exc_info.value.code == 1

    def test_no_agent_error_is_shown(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger"), patch.object(sys.stdout, "isatty", return_value=True):
                with pytest.raises(SystemExit):
                    runner.execute()
        errors = [c for c in renderer.calls if c[0] == "error"]
        assert any("No assessment produced" in str(c) for c in errors)

    def test_how_to_fix_info_is_shown(self, tmp_path):
        session = make_session(tmp_path)
        renderer = MockRenderer(confirm_response=True)
        runner = OrchestratorRunner(session=session, renderer=renderer)
        with patch("sqaf.orchestrator.trigger"), patch.object(sys.stdout, "isatty", return_value=True):
                with pytest.raises(SystemExit):
                    runner.execute()
        info_values = [c[2] for c in renderer.calls if c[0] == "info"]
        assert any("Run sqaf" in str(v) or "agent CLI" in str(v) for v in info_values)


# ── Summary rendering ──────────────────────────────────────────────────────────

class TestSummaryRendering:

    def _run_to_summary(self, tmp_path, skill_name="my-skill", run_eval=False):
        """Run only the summary step by aborting at confirmation."""
        session = make_session(tmp_path, skill_name=skill_name, run_eval=run_eval)
        renderer = MockRenderer(confirm_response=False)
        OrchestratorRunner(session=session, renderer=renderer).execute()
        return renderer

    def test_summary_shows_skill_name(self, tmp_path):
        renderer = self._run_to_summary(tmp_path, skill_name="demo-skill")
        info_values = [c[2] for c in renderer.calls if c[0] == "info"]
        assert any("demo-skill" in v for v in info_values)

    def test_summary_shows_eval_enabled(self, tmp_path):
        renderer = self._run_to_summary(tmp_path, run_eval=True)
        info_values = [c[2] for c in renderer.calls if c[0] == "info"]
        assert any("Enabled" in v for v in info_values)

    def test_summary_shows_eval_skipped(self, tmp_path):
        renderer = self._run_to_summary(tmp_path, run_eval=False)
        info_values = [c[2] for c in renderer.calls if c[0] == "info"]
        assert any("Skipped" in v for v in info_values)

    def test_summary_shows_output_directory(self, tmp_path):
        session = make_session(tmp_path, output="reports/")
        renderer = MockRenderer(confirm_response=False)
        OrchestratorRunner(session=session, renderer=renderer).execute()
        info_values = [c[2] for c in renderer.calls if c[0] == "info"]
        assert any("reports/" in v for v in info_values)

    def test_step_4_is_rendered(self, tmp_path):
        renderer = self._run_to_summary(tmp_path)
        steps = [c for c in renderer.calls if c[0] == "step"]
        assert any(c[1] == 4 for c in steps), "Step 4 must be rendered"
