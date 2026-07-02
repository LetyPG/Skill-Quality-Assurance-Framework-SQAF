"""Tests for skills_discovery module."""
from __future__ import annotations

from pathlib import Path
import pytest
from sqaf.skills_discovery import discover_skills, skill_has_evals


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_skill(base: Path, name: str, with_eval_json: bool = False, with_evals_dir: bool = False) -> Path:
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}")
    if with_eval_json:
        (skill_dir / "eval.json").write_text("{}")
    if with_evals_dir:
        (skill_dir / "evals").mkdir()
    return skill_dir


# ── discover_skills ────────────────────────────────────────────────────────────

class TestDiscoverSkills:
    def test_finds_skill_directories(self, tmp_path):
        make_skill(tmp_path, "skill-a")
        make_skill(tmp_path, "skill-b")
        results = discover_skills(str(tmp_path))
        names = [Path(r).name for r in results]
        assert "skill-a" in names
        assert "skill-b" in names

    def test_ignores_directories_without_skill_md(self, tmp_path):
        (tmp_path / "not-a-skill").mkdir()
        results = discover_skills(str(tmp_path))
        assert results == []

    def test_ignores_hidden_directories(self, tmp_path):
        hidden = tmp_path / ".hidden-skill"
        hidden.mkdir()
        (hidden / "SKILL.md").write_text("# hidden")
        results = discover_skills(str(tmp_path))
        assert results == []

    def test_respects_max_depth(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        (deep / "SKILL.md").write_text("# deep")
        results = discover_skills(str(tmp_path), max_depth=3)
        assert str(deep) not in results

    def test_finds_nested_skills_within_depth(self, tmp_path):
        nested = tmp_path / "group" / "nested-skill"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("# nested")
        results = discover_skills(str(tmp_path), max_depth=4)
        names = [Path(r).name for r in results]
        assert "nested-skill" in names

    def test_results_are_sorted(self, tmp_path):
        make_skill(tmp_path, "z-skill")
        make_skill(tmp_path, "a-skill")
        make_skill(tmp_path, "m-skill")
        results = discover_skills(str(tmp_path))
        names = [Path(r).name for r in results]
        assert names == sorted(names)

    def test_empty_workspace_returns_empty_list(self, tmp_path):
        results = discover_skills(str(tmp_path))
        assert results == []


# ── skill_has_evals ────────────────────────────────────────────────────────────

class TestSkillHasEvals:
    def test_detects_eval_json(self, tmp_path):
        s = make_skill(tmp_path, "s1", with_eval_json=True)
        assert skill_has_evals(str(s)) is True

    def test_detects_evals_directory(self, tmp_path):
        s = make_skill(tmp_path, "s2", with_evals_dir=True)
        assert skill_has_evals(str(s)) is True

    def test_returns_false_when_no_evals(self, tmp_path):
        s = make_skill(tmp_path, "s3")
        assert skill_has_evals(str(s)) is False
