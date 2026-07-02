"""
Tests for sqaf.ui.banner — startup banner rendering.

All tests verify the three core guarantees from the spec:
  1. Banner is suppressed when stdout is not a TTY.
  2. Banner falls back to plain text when pyfiglet is unavailable.
  3. Any rendering exception is swallowed — the framework never crashes.
"""
from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from sqaf.ui.banner import render_banner, _figlet_text, _TITLE, _VERSION


# ── TTY detection ──────────────────────────────────────────────────────────────

class TestTTYGating:

    def test_suppressed_when_not_tty(self, capsys):
        """render_banner() must produce no output when stdout is not a TTY."""
        with patch("sys.stdout.isatty", return_value=False):
            render_banner()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_does_not_raise_when_not_tty(self):
        """render_banner() must never raise regardless of TTY state."""
        with patch("sys.stdout.isatty", return_value=False):
            render_banner()  # should complete silently


# ── pyfiglet availability ──────────────────────────────────────────────────────

class TestFigletFallback:

    def test_figlet_returns_none_when_import_fails(self):
        """_figlet_text() returns None when pyfiglet cannot be imported."""
        with patch.dict("sys.modules", {"pyfiglet": None}):
            result = _figlet_text()
        assert result is None

    def test_figlet_returns_string_when_available(self):
        """_figlet_text() returns a non-empty string when pyfiglet is present."""
        mock_figlet = MagicMock()
        mock_figlet.return_value.renderText.return_value = "  SQAF  "
        mock_module = MagicMock()
        mock_module.Figlet = mock_figlet
        with patch.dict("sys.modules", {"pyfiglet": mock_module}):
            result = _figlet_text()
        assert result == "  SQAF  "


# ── Exception safety ───────────────────────────────────────────────────────────

class TestExceptionSafety:

    def test_rich_failure_is_swallowed(self):
        """If rich raises during banner rendering, execution must continue."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("sqaf.ui.banner._figlet_text", side_effect=RuntimeError("boom")):
                render_banner()  # must not raise

    def test_console_print_failure_is_swallowed(self):
        """If Console.print raises, execution must continue."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("sqaf.ui.banner._figlet_text", return_value=None):
                mock_console = MagicMock()
                mock_console.return_value.print.side_effect = Exception("render error")
                # Console is lazily imported inside render_banner, so patch at source
                with patch("rich.console.Console", mock_console):
                    render_banner()  # must not raise


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:

    def test_version_format(self):
        assert _VERSION.startswith("v")

    def test_title_is_sqaf(self):
        assert _TITLE == "SQAF"
