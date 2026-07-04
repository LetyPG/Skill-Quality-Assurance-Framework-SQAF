"""Tests for AssessmentSession."""
from __future__ import annotations

from pathlib import Path
from sqaf.session import AssessmentSession


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_skill_dir(tmp_path: Path, name: str = "my-skill") -> str:
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"# {name}")
    return str(skill_dir)


# ── is_valid ───────────────────────────────────────────────────────────────────

class TestIsValid:
    def test_valid_when_all_mandatory_fields_set(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(skill_path=path, run_eval=False)
        assert session.is_valid() is True

    def test_invalid_when_skill_path_none(self):
        session = AssessmentSession(run_eval=False)
        assert session.is_valid() is False

    def test_invalid_when_run_eval_none(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(skill_path=path)
        assert session.is_valid() is False

    def test_invalid_when_path_does_not_exist(self):
        session = AssessmentSession(skill_path="/nonexistent/path", run_eval=False)
        assert session.is_valid() is False

    def test_invalid_when_skill_md_missing(self, tmp_path):
        d = tmp_path / "no-md"
        d.mkdir()
        session = AssessmentSession(skill_path=str(d), run_eval=False)
        assert session.is_valid() is False

    def test_valid_with_run_eval_true(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(skill_path=path, run_eval=True)
        assert session.is_valid() is True


# ── validation_errors ──────────────────────────────────────────────────────────

class TestValidationErrors:
    def test_reports_missing_skill_path(self):
        session = AssessmentSession(run_eval=False)
        errors = session.validation_errors()
        assert any("skill_path" in e for e in errors)

    def test_reports_missing_run_eval(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(skill_path=path)
        errors = session.validation_errors()
        assert any("run_eval" in e for e in errors)

    def test_reports_both_missing(self):
        session = AssessmentSession()
        errors = session.validation_errors()
        assert len(errors) == 2

    def test_no_errors_when_valid(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(skill_path=path, run_eval=False)
        assert session.validation_errors() == []


# ── Auto-population ────────────────────────────────────────────────────────────

class TestAutoPopulation:
    def test_assessment_name_derived_from_skill_path(self, tmp_path):
        path = make_skill_dir(tmp_path, "intent-reviewer")
        session = AssessmentSession(skill_path=path, run_eval=False)
        assert session.assessment_name == "intent-reviewer"

    def test_timestamp_is_set_automatically(self):
        session = AssessmentSession()
        assert session.timestamp is not None
        assert "T" in session.timestamp  # ISO-8601

    def test_explicit_assessment_name_not_overridden(self, tmp_path):
        path = make_skill_dir(tmp_path)
        session = AssessmentSession(
            skill_path=path,
            run_eval=False,
            assessment_name="custom-name",
        )
        assert session.assessment_name == "custom-name"

    def test_defaults(self):
        session = AssessmentSession()
        assert session.output_directory == "assessment/"
        assert session.framework_version == "0.1.0"
        assert session.execution_mode == "interactive"
        assert session.workspace == "."
