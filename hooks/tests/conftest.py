"""
pytest fixtures for SQAF hook tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def make_skill_dir(tmp_path: Path):
    """
    Factory fixture. Creates a valid skill directory with SKILL.md.
    Returns the absolute path to SKILL.md.

    Usage:
        skill_md_path = make_skill_dir("my-skill")
        skill_md_path = make_skill_dir("my-skill", content="# big content")
    """
    def _factory(name: str = "test-skill", content: str = "# Test Skill\n") -> str:
        skill_dir = tmp_path / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(content, encoding="utf-8")
        return str(skill_md)
    return _factory


@pytest.fixture()
def make_eval_json(tmp_path: Path):
    """
    Factory fixture. Creates a valid eval.json file.
    Returns the absolute path to the file.
    """
    def _factory(
        name: str = "eval.json",
        data: dict | None = None,
        content: str | None = None,
    ) -> str:
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir(parents=True, exist_ok=True)
        eval_file = evals_dir / name
        if content is not None:
            eval_file.write_text(content, encoding="utf-8")
        else:
            payload = data or {
                "prompt": "Test prompt",
                "expected_output": "Expected result",
                "assertions": [{"text": "Output is not empty"}],
            }
            eval_file.write_text(json.dumps(payload), encoding="utf-8")
        return str(eval_file)
    return _factory


@pytest.fixture()
def valid_prompt(make_skill_dir):
    """A minimal valid assessment prompt with a real SKILL.md on disk."""
    skill_path = make_skill_dir("valid-skill")
    return f"Assess the quality of the following skill: {skill_path}"


@pytest.fixture()
def valid_prompt_with_eval(make_skill_dir, make_eval_json):
    """A valid prompt referencing both SKILL.md and eval.json on disk."""
    skill_path = make_skill_dir("valid-skill-eval")
    eval_path = make_eval_json()
    return (
        f"Assess the quality of the following skill: {skill_path} "
        f"with evals at {eval_path}"
    )
