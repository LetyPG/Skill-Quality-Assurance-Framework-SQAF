"""
Tests for sqaf.cli — argument parsing and main() entry point.

Covers:
  - _parse_args: all flags and defaults
  - main(): non-interactive with valid skill → trigger emitted (non-TTY)
  - main(): non-interactive with missing skill → exits with error
  - main(): --help exits cleanly
  - Integration: full subprocess E2E to verify the installed entry point works
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import _parse_args directly for unit tests
from sqaf.cli import _parse_args


# ── _parse_args unit tests ─────────────────────────────────────────────────────

class TestParseArgs:

    def _parse(self, *argv: str):
        with patch("sys.argv", ["sqaf", *argv]):
            return _parse_args()

    def test_defaults_no_args(self):
        args = self._parse()
        assert args.skill_path is None
        assert args.run_eval is None
        assert args.output_directory is None
        assert args.non_interactive is False

    def test_positional_skill_path(self):
        args = self._parse("skills/my-skill")
        assert args.skill_path == "skills/my-skill"

    def test_eval_y(self):
        args = self._parse("skills/my-skill", "--eval", "y")
        assert args.run_eval == "y"

    def test_eval_yes(self):
        args = self._parse("skills/my-skill", "--eval", "yes")
        assert args.run_eval == "yes"

    def test_eval_n(self):
        args = self._parse("skills/my-skill", "--eval", "n")
        assert args.run_eval == "n"

    def test_eval_no(self):
        args = self._parse("skills/my-skill", "--eval", "no")
        assert args.run_eval == "no"

    def test_output_flag(self):
        args = self._parse("--output", "reports/")
        assert args.output_directory == "reports/"

    def test_non_interactive_flag(self):
        args = self._parse("--non-interactive")
        assert args.non_interactive is True

    def test_all_flags_combined(self):
        args = self._parse(
            "skills/my-skill",
            "--eval", "y",
            "--output", "out/",
            "--non-interactive",
        )
        assert args.skill_path == "skills/my-skill"
        assert args.run_eval == "y"
        assert args.output_directory == "out/"
        assert args.non_interactive is True

    def test_invalid_eval_value_raises(self):
        with pytest.raises(SystemExit):
            self._parse("--eval", "maybe")


# ── main() integration (subprocess) ───────────────────────────────────────────

class TestMainSubprocess:
    """
    Uses subprocess to call `sqaf` as a real process, so stdout is a pipe
    (not a TTY). This simulates the correct agent-driven execution context
    where the trigger is emitted cleanly without the no-agent error.
    """

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "sqaf", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            text=True,
        )

    def test_help_exits_zero(self):
        result = self._run("--help")
        assert result.returncode == 0
        # argparse writes --help to stdout; merged into result.stdout via stderr=STDOUT
        assert "SKILL_PATH" in result.stdout or "sqaf" in result.stdout

    def test_non_interactive_missing_skill_exits_nonzero(self):
        result = self._run("--non-interactive")
        assert result.returncode != 0

    def test_non_interactive_invalid_path_exits_nonzero(self, tmp_path):
        result = self._run(
            str(tmp_path / "nonexistent"),
            "--eval", "n",
            "--non-interactive",
        )
        assert result.returncode != 0

    def test_non_interactive_valid_skill_emits_trigger(self, tmp_path):
        skill = tmp_path / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# Test Skill")

        result = self._run(
            str(skill),
            "--eval", "n",
            "--non-interactive",
        )
        assert result.returncode == 0
        assert "SKILL.md" in result.stdout
        assert "Store results in:" in result.stdout

    def test_non_interactive_eval_enabled_trigger_includes_evals(self, tmp_path):
        skill = tmp_path / "eval-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# Skill")

        result = self._run(
            str(skill),
            "--eval", "y",
            "--non-interactive",
        )
        assert result.returncode == 0
        assert "eval.json" in result.stdout

    def test_non_interactive_output_dir_appears_in_trigger(self, tmp_path):
        skill = tmp_path / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("")

        result = self._run(
            str(skill),
            "--eval", "n",
            "--output", "custom-output/",
            "--non-interactive",
        )
        assert result.returncode == 0
        assert "custom-output/" in result.stdout
