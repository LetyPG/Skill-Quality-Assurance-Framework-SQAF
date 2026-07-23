"""
Calculator tests — pytest style.

Run all framework tests with a single command:
    ./venv/bin/python -m pytest tests/ -v
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

# ── Calculator import ──────────────────────────────────────────────────────────
# Add the calculator script directory to sys.path so it can be imported directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "assessment-summarizer" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))
import calculator  # type: ignore  # noqa: E402

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[TEST LOG] %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

class _Args:
    """Minimal namespace that mimics argparse output for calculator input."""

    def __init__(self, **kwargs):
        defaults = {
            "intent_score": None, "intent_risk": None,
            "instruction_score": None, "instruction_risk": None,
            "qa_score": None, "qa_risk": None,
            "execution_score": None, "execution_risk": None,
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


# ── Validation tests ───────────────────────────────────────────────────────────

class TestValidation:

    def test_valid_inputs(self):
        log.info("validate_and_parse_inputs(): valid score/risk combinations.")
        args = _Args(
            intent_score=90, intent_risk="LOW",
            instruction_score=85, instruction_risk="MEDIUM",
            qa_score=80, qa_risk="LOW",
            execution_score=95, execution_risk="LOW",
        )
        parsed = calculator.validate_and_parse_inputs(args)
        assert parsed["intent_score"] == 90.0
        assert parsed["intent_risk"] == "LOW"
        assert parsed["execution_score"] == 95.0

    def test_missing_design_reviewers(self):
        log.info("validate_and_parse_inputs(): at least one design reviewer required.")
        args = _Args(execution_score=90, execution_risk="LOW")
        with pytest.raises(ValueError, match="At least one design reviewer"):
            calculator.validate_and_parse_inputs(args)

    def test_copresence_error(self):
        log.info("validate_and_parse_inputs(): score and risk must be provided together.")
        args = _Args(
            intent_score=90, intent_risk=None,   # score without risk
            instruction_score=85, instruction_risk="MEDIUM",
            qa_score=80, qa_risk="LOW",
        )
        with pytest.raises(ValueError, match="both score and risk must be provided"):
            calculator.validate_and_parse_inputs(args)

    def test_score_out_of_range(self):
        log.info("validate_and_parse_inputs(): score range boundaries (0-100).")
        args = _Args(
            intent_score=105, intent_risk="LOW",
            instruction_score=85, instruction_risk="MEDIUM",
            qa_score=80, qa_risk="LOW",
        )
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            calculator.validate_and_parse_inputs(args)

    def test_invalid_risk_value(self):
        log.info("validate_and_parse_inputs(): risk level must be a known category.")
        args = _Args(
            intent_score=90, intent_risk="NONE",  # invalid
            instruction_score=85, instruction_risk="MEDIUM",
            qa_score=80, qa_risk="LOW",
        )
        with pytest.raises(ValueError, match="must be one of"):
            calculator.validate_and_parse_inputs(args)


# ── Metrics calculation tests ──────────────────────────────────────────────────

class TestCalculateMetrics:

    def test_full_assessment_all_reviewers(self):
        log.info("calculate_metrics(): Design + Execution reviewers completed.")
        parsed = {
            "intent_score": 90.0, "intent_risk": "LOW",
            "instruction_score": 85.0, "instruction_risk": "MEDIUM",
            "qa_score": 80.0, "qa_risk": "LOW",
            "execution_score": 95.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["design_quality"] == 85
        assert res["execution_quality"] == 95
        assert res["overall_quality"] == 90
        assert res["overall_risk"] == "MEDIUM"
        assert res["final_recommendation"] == "APPROVED"

    def test_design_only_assessment(self):
        log.info("calculate_metrics(): Design-only reviewers (no execution).")
        parsed = {
            "intent_score": 90.0, "intent_risk": "LOW",
            "instruction_score": 85.0, "instruction_risk": "MEDIUM",
            "qa_score": 80.0, "qa_risk": "LOW",
            "execution_score": None, "execution_risk": None,
        }
        res = calculator.calculate_metrics(parsed)
        assert res["design_quality"] == 85
        assert res["execution_quality"] is None
        assert res["overall_quality"] == 85
        assert res["overall_risk"] == "MEDIUM"
        assert res["final_recommendation"] == "APPROVED"


# ── Downgrade gate tests ───────────────────────────────────────────────────────

class TestDowngradeGates:

    def test_critical_risk_forces_not_approved(self):
        log.info("Downgrade: CRITICAL risk → NOT APPROVED.")
        parsed = {
            "intent_score": 95.0, "intent_risk": "CRITICAL",
            "instruction_score": 95.0, "instruction_risk": "LOW",
            "qa_score": 95.0, "qa_risk": "LOW",
            "execution_score": 95.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["overall_risk"] == "CRITICAL"
        assert res["final_recommendation"] == "NOT APPROVED"

    def test_high_risk_caps_at_requires_revision(self):
        log.info("Downgrade: HIGH risk → caps at REQUIRES REVISION.")
        parsed = {
            "intent_score": 95.0, "intent_risk": "HIGH",
            "instruction_score": 95.0, "instruction_risk": "LOW",
            "qa_score": 95.0, "qa_risk": "LOW",
            "execution_score": 95.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["overall_risk"] == "HIGH"
        assert res["final_recommendation"] == "REQUIRES REVISION"

    def test_score_below_60_caps_at_requires_revision(self):
        log.info("Downgrade: score < 60 → caps at REQUIRES REVISION.")
        parsed = {
            "intent_score": 90.0, "intent_risk": "LOW",
            "instruction_score": 55.0, "instruction_risk": "LOW",
            "qa_score": 90.0, "qa_risk": "LOW",
            "execution_score": 95.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["final_recommendation"] == "REQUIRES REVISION"

    def test_score_below_40_forces_not_approved(self):
        log.info("Downgrade: score < 40 → NOT APPROVED.")
        parsed = {
            "intent_score": 90.0, "intent_risk": "LOW",
            "instruction_score": 35.0, "instruction_risk": "LOW",
            "qa_score": 90.0, "qa_risk": "LOW",
            "execution_score": 95.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["final_recommendation"] == "NOT APPROVED"

    def test_severe_discrepancy_downgrades_recommendation(self):
        log.info("Downgrade: Design-Execution discrepancy > 40 → downgrade by one level.")
        # Design quality: 90, Execution quality: 45, Overall: 68
        # Preliminary: REQUIRES REVISION → downgraded → NOT APPROVED
        parsed = {
            "intent_score": 90.0, "intent_risk": "LOW",
            "instruction_score": 90.0, "instruction_risk": "LOW",
            "qa_score": 90.0, "qa_risk": "LOW",
            "execution_score": 45.0, "execution_risk": "LOW",
        }
        res = calculator.calculate_metrics(parsed)
        assert res["final_recommendation"] == "NOT APPROVED"


# ── CLI entrypoint test ────────────────────────────────────────────────────────

class TestCLI:

    def test_cli_execution(self):
        log.info("CLI: calculator.py parses args, validates, and outputs valid JSON.")
        script = str(_SCRIPTS_DIR / "calculator.py")
        cmd = [
            sys.executable, script,
            "--intent-score", "90", "--intent-risk", "LOW",
            "--instruction-score", "85", "--instruction-risk", "MEDIUM",
            "--qa-score", "80", "--qa-risk", "LOW",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

        data = json.loads(result.stdout.strip())
        assert data["design_quality"] == 85
        assert data["execution_quality"] is None
        assert data["overall_risk"] == "MEDIUM"
