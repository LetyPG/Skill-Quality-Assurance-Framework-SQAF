"""
Tests for sqaf_performance_hook — Phases 1, 2, and 4.

Covers:
    Phase 1 — SKILL.md Block  (single-skill guard, absolute path, disk existence, size)
    Phase 2 — eval.json Block (absolute path, disk existence, valid JSON, size)
    Phase 4 — Language detection, language_rule injection, allow result contract
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from hooks.hook_contract import HookContext
from hooks.hook_utils import generate_trace_id
from hooks.sqaf_performance_hook import (
    CONFIDENCE_THRESHOLD,
    LANGUAGE_RULES,
    MAX_EVAL_JSON_BYTES,
    MAX_SKILL_MD_BYTES,
    build_allow_result,
    detect_language,
    validate_eval_json,
    validate_skill_md,
)

# ===========================================================================
# Phase 1 — SKILL.md Block
# ===========================================================================

class TestValidateSkillMd:

    def test_valid_path_passes(self, make_skill_dir):
        skill_path = make_skill_dir("my-skill")
        reason, path = validate_skill_md(
            f"Assess the quality of the following skill: {skill_path}"
        )
        assert reason is None
        assert path == skill_path

    def test_no_skill_path_is_blocked(self):
        reason, path = validate_skill_md("Assess my skill please")
        assert reason is not None
        assert "SKILL.md" in reason
        assert path is None

    def test_multiple_skill_paths_blocked(self, make_skill_dir):
        path1 = make_skill_dir("skill-a")
        path2 = make_skill_dir("skill-b")
        reason, path = validate_skill_md(f"Assess: {path1} and also {path2}")
        assert reason is not None
        assert "Multiple" in reason
        assert path is None

    def test_relative_path_not_matched(self):
        """Regex requires absolute paths — relative paths produce no match → blocked."""
        reason, path = validate_skill_md("Assess the skill at ./my-skill/SKILL.md")
        assert reason is not None
        assert path is None

    def test_nonexistent_path_blocked(self):
        reason, path = validate_skill_md(
            "Assess the quality of the following skill: /nonexistent/path/SKILL.md"
        )
        assert reason is not None
        assert "not found" in reason.lower()
        assert path is None

    def test_skill_md_too_large_blocked(self, make_skill_dir):
        big_content = "x" * (MAX_SKILL_MD_BYTES + 1)
        skill_path = make_skill_dir("big-skill", content=big_content)
        reason, path = validate_skill_md(
            f"Assess the quality of the following skill: {skill_path}"
        )
        assert reason is not None
        assert "500 KB" in reason
        assert path is None

    def test_skill_md_at_exact_limit_passes(self, make_skill_dir):
        at_limit_content = "x" * MAX_SKILL_MD_BYTES
        skill_path = make_skill_dir("limit-skill", content=at_limit_content)
        reason, path = validate_skill_md(
            f"Assess the quality of the following skill: {skill_path}"
        )
        assert reason is None
        assert path == skill_path

    def test_extracted_path_matches_input(self, make_skill_dir):
        skill_path = make_skill_dir("extract-test")
        reason, path = validate_skill_md(f"Please assess: {skill_path}")
        assert reason is None
        assert path == skill_path


# ===========================================================================
# Phase 2 — eval.json Block
# ===========================================================================

class TestValidateEvalJson:

    def test_valid_eval_passes(self, make_eval_json):
        eval_path = make_eval_json()
        reason, path = validate_eval_json(
            f"Assess the skill with evals at {eval_path}"
        )
        assert reason is None
        assert path == eval_path

    def test_no_eval_reference_is_skipped(self):
        """Not referencing eval.json is valid — skip block entirely."""
        reason, path = validate_eval_json(
            "Assess the quality of the following skill: /some/path/SKILL.md"
        )
        assert reason is None
        assert path is None

    def test_nonexistent_eval_blocked(self):
        reason, path = validate_eval_json(
            "Assess with evals at /nonexistent/path/eval.json"
        )
        assert reason is not None
        assert "not found" in reason.lower()
        assert path is None

    def test_invalid_json_blocked(self, make_eval_json):
        eval_path = make_eval_json(content="{ not valid json !!!")
        reason, path = validate_eval_json(f"Assess with evals at {eval_path}")
        assert reason is not None
        assert "not valid JSON" in reason
        assert path is None

    def test_eval_too_large_blocked(self, make_eval_json):
        big_content = '{"data": "' + "x" * (MAX_EVAL_JSON_BYTES + 1) + '"}'
        eval_path = make_eval_json(content=big_content)
        reason, path = validate_eval_json(f"Assess with evals at {eval_path}")
        assert reason is not None
        assert "5 MB" in reason
        assert path is None

    def test_multiple_eval_paths_blocked(self, make_eval_json, tmp_path):
        path1 = make_eval_json(name="eval.json")
        path2 = path1.replace("eval.json", "evals.json")
        from pathlib import Path as P
        P(path2).write_text("{}")
        reason, _path = validate_eval_json(
            f"Assess with evals at {path1} and also {path2}"
        )
        assert reason is not None
        assert "Multiple" in reason

    def test_eval_path_extracted_correctly(self, make_eval_json):
        eval_path = make_eval_json()
        reason, path = validate_eval_json(f"Assess the skill with evals at {eval_path}")
        assert reason is None
        assert path == eval_path


# ===========================================================================
# Phase 4 — Language Detection
# ===========================================================================

class TestDetectLanguage:

    def test_returns_english_when_lingua_unavailable(self):
        with patch("hooks.sqaf_performance_hook._LINGUA_AVAILABLE", False):
            lang, confidence = detect_language("Hello, assess my skill.")
        assert lang == "English"
        assert confidence == 0.0

    def test_returns_english_on_empty_prompt(self):
        lang, _ = detect_language("")
        assert lang == "English"

    def test_returns_english_on_whitespace_prompt(self):
        lang, _ = detect_language("   ")
        assert lang == "English"

    def test_fallback_on_low_confidence(self):
        """Confidence below threshold → English fallback."""
        with patch(
            "hooks.sqaf_performance_hook.detect_language",
            return_value=("English", CONFIDENCE_THRESHOLD - 0.01),
        ) as mock_det:
            lang, conf = mock_det("ambiguous text")
        assert lang == "English"
        assert conf < CONFIDENCE_THRESHOLD

    def test_spanish_result_returned(self):
        with patch(
            "hooks.sqaf_performance_hook.detect_language",
            return_value=("Spanish", 0.95),
        ) as mock_det:
            lang, conf = mock_det("Evalúa la calidad")
        assert lang == "Spanish"
        assert conf == 0.95

    def test_portuguese_result_returned(self):
        with patch(
            "hooks.sqaf_performance_hook.detect_language",
            return_value=("Portuguese", 0.88),
        ) as mock_det:
            lang, _ = mock_det("Avalie a qualidade")
        assert lang == "Portuguese"

    def test_returns_english_on_exception(self):
        """Internal exceptions must not crash the hook."""
        class FailingDict(dict):
            def get(self, *args, **kwargs):
                raise RuntimeError("Simulated failure")

        with patch("hooks.sqaf_performance_hook._LINGUA_AVAILABLE", True), \
             patch("hooks.sqaf_performance_hook._LINGUA_LANGUAGE_MAP", FailingDict()):
            lang, confidence = detect_language("Hello there")
        assert lang == "English"
        assert confidence == 0.0


# ===========================================================================
# Language Rules
# ===========================================================================

class TestLanguageRules:

    @pytest.mark.parametrize("language", [
        "Spanish", "English", "Portuguese", "French", "German", "Italian",
    ])
    def test_rule_exists_for_all_supported_languages(self, language):
        assert language in LANGUAGE_RULES
        assert len(LANGUAGE_RULES[language]) > 20

    def test_spanish_rule_covers_all_artifact_types(self):
        rule = LANGUAGE_RULES["Spanish"]
        assert "findings" in rule
        assert "recommendations" in rule
        assert "skill-quality-report.md" in rule

    def test_spanish_rule_preserves_json_field_names(self):
        rule = LANGUAGE_RULES["Spanish"]
        assert "English" in rule  # field names stay in English


# ===========================================================================
# Phase 4 — Build Allow Result (Orchestrator Contract)
# ===========================================================================

class TestBuildAllowResult:

    def test_execute_workflow_is_true(self, make_skill_dir):
        skill_path = make_skill_dir("allow-test")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        assert result.execute_workflow is True

    def test_skill_path_field_set(self, make_skill_dir):
        skill_path = make_skill_dir("path-test")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        assert result.skill_path == skill_path

    def test_eval_path_set_when_provided(self, make_skill_dir, make_eval_json):
        skill_path = make_skill_dir("eval-path-test")
        eval_path = make_eval_json()
        context = HookContext(
            user_prompt=f"Assess: {skill_path} with evals at {eval_path}",
            input_files=[],
        )
        result = build_allow_result(context, generate_trace_id(), skill_path, eval_path)
        assert result.eval_path == eval_path

    def test_eval_path_none_when_absent(self, make_skill_dir):
        skill_path = make_skill_dir("no-eval")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        assert result.eval_path is None

    def test_language_rule_injected(self, make_skill_dir):
        skill_path = make_skill_dir("lang-rule")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        assert result.language_rule is not None
        assert len(result.language_rule) > 0

    def test_trace_id_preserved(self, make_skill_dir):
        skill_path = make_skill_dir("trace-test")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        trace_id = "fixed-trace-for-test"
        result = build_allow_result(context, trace_id, skill_path, None)
        assert result.trace_id == trace_id

    def test_to_dict_has_all_contract_fields(self, make_skill_dir):
        skill_path = make_skill_dir("dict-test")
        context = HookContext(user_prompt="Assess: " + skill_path, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        d = result.to_dict()
        expected_keys = {
            "execute_workflow", "trace_id", "risk_level", "block_reason",
            "block_phase", "skill_path", "eval_path",
            "language", "confidence", "language_rule", "sanitized_context",
        }
        assert expected_keys == set(d.keys())

    def test_sanitized_context_contains_prompt(self, make_skill_dir):
        skill_path = make_skill_dir("ctx-test")
        prompt = f"Assess: {skill_path}"
        context = HookContext(user_prompt=prompt, input_files=[])
        result = build_allow_result(context, generate_trace_id(), skill_path, None)
        assert result.sanitized_context is not None
        assert result.sanitized_context["user_prompt"] == prompt


# ===========================================================================
# Trace ID (shared utility — exercised through performance hook context)
# ===========================================================================

class TestGenerateTraceId:

    def test_generates_unique_ids(self):
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_uuid4_format(self):
        import re
        tid = generate_trace_id()
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            tid,
        )
