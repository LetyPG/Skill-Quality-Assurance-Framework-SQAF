"""
Tests for sqaf.ui.renderer, sqaf.ui.plain_renderer, and sqaf.ui.rich_renderer.

Covers:
  - get_renderer() factory behavior (gated by stdout TTY status)
  - PlainRenderer methods (header, step, info, prompt, confirm, success, error, numbered_list, blank, paragraph)
  - RichRenderer methods (header, step, info, prompt, confirm, success, error, numbered_list, blank, paragraph)
"""
from __future__ import annotations

import sys
from unittest.mock import patch

from sqaf.ui.plain_renderer import PlainRenderer
from sqaf.ui.renderer import get_renderer
from sqaf.ui.rich_renderer import RichRenderer


# ── Renderer Factory (get_renderer) ──────────────────────────────────────────

class TestGetRenderer:

    def test_get_renderer_returns_rich_when_tty(self):
        with patch.object(sys.stdout, "isatty", return_value=True):
            renderer = get_renderer()
            assert isinstance(renderer, RichRenderer)

    def test_get_renderer_returns_plain_when_not_tty(self):
        with patch.object(sys.stdout, "isatty", return_value=False):
            renderer = get_renderer()
            assert isinstance(renderer, PlainRenderer)


# ── PlainRenderer Tests ───────────────────────────────────────────────────────

class TestPlainRenderer:

    def test_header(self, capsys):
        renderer = PlainRenderer()
        renderer.header("Test Title")
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "────────" in captured.out

    def test_step(self, capsys):
        renderer = PlainRenderer()
        renderer.step(2, 5, "Loading Workspace")
        captured = capsys.readouterr()
        assert "Step 2 of 5 — Loading Workspace" in captured.out

    def test_info(self, capsys):
        renderer = PlainRenderer()
        renderer.info("Skill Path", "/path/to/skill")
        captured = capsys.readouterr()
        assert "Skill Path" in captured.out
        assert "/path/to/skill" in captured.out

    def test_prompt_no_default(self):
        renderer = PlainRenderer()
        with patch("builtins.input", return_value="user input") as mock_input:
            res = renderer.prompt("Enter value")
            assert res == "user input"
            mock_input.assert_called_once_with("Enter value: ")

    def test_prompt_with_default(self):
        renderer = PlainRenderer()
        with patch("builtins.input", return_value="") as mock_input:
            res = renderer.prompt("Enter value", default="default_val")
            assert res == "default_val"
            mock_input.assert_called_once_with("Enter value [default_val]: ")

        with patch("builtins.input", return_value="custom") as mock_input:
            res = renderer.prompt("Enter value", default="default_val")
            assert res == "custom"

    def test_confirm_default_true(self):
        renderer = PlainRenderer()
        # Enter empty string -> returns default (True)
        with patch("builtins.input", return_value="") as mock_input:
            assert renderer.confirm("Continue?", default=True) is True
            mock_input.assert_called_once_with("Continue? [Y/n]: ")

        # Enter y -> returns True
        with patch("builtins.input", return_value="y"):
            assert renderer.confirm("Continue?", default=True) is True

        # Enter yes -> returns True
        with patch("builtins.input", return_value="yes"):
            assert renderer.confirm("Continue?", default=True) is True

        # Enter n -> returns False
        with patch("builtins.input", return_value="n"):
            assert renderer.confirm("Continue?", default=True) is False

    def test_confirm_default_false(self):
        renderer = PlainRenderer()
        # Enter empty string -> returns default (False)
        with patch("builtins.input", return_value="") as mock_input:
            assert renderer.confirm("Continue?", default=False) is False
            mock_input.assert_called_once_with("Continue? [y/N]: ")

        # Enter y -> returns True
        with patch("builtins.input", return_value="y"):
            assert renderer.confirm("Continue?", default=False) is True

    def test_success(self, capsys):
        renderer = PlainRenderer()
        renderer.success("Assessment Complete")
        captured = capsys.readouterr()
        assert "✓ Assessment Complete" in captured.out

    def test_error(self, capsys):
        renderer = PlainRenderer()
        renderer.error("Verification Failed")
        captured = capsys.readouterr()
        assert "✗ Verification Failed" in captured.out

    def test_numbered_list(self, capsys):
        renderer = PlainRenderer()
        renderer.numbered_list(["item A", "item B"])
        captured = capsys.readouterr()
        assert "1. item A" in captured.out
        assert "2. item B" in captured.out

    def test_blank(self, capsys):
        renderer = PlainRenderer()
        renderer.blank()
        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_paragraph(self, capsys):
        renderer = PlainRenderer()
        renderer.paragraph("This is a simple paragraph.")
        captured = capsys.readouterr()
        assert "This is a simple paragraph." in captured.out


# ── RichRenderer Tests ────────────────────────────────────────────────────────

class TestRichRenderer:

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_header(self, mock_print):
        renderer = RichRenderer()
        renderer.header("Interactive Test")
        # header prints a blank line, a panel, and another blank line
        assert mock_print.call_count == 3
        found = False
        for call in mock_print.call_args_list:
            if call.args:
                arg = call.args[0]
                if hasattr(arg, 'renderable'):
                    if "Interactive Test" in str(arg.renderable):
                        found = True
                elif "Interactive Test" in str(arg):
                    found = True
        assert found

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_step(self, mock_print):
        renderer = RichRenderer()
        renderer.step(3, 3, "Final Step")
        assert mock_print.call_count == 2
        found = False
        for call in mock_print.call_args_list:
            if call.args:
                arg = call.args[0]
                val = str(getattr(arg, "title", arg))
                if "Step 3 of 3" in val and "Final Step" in val:
                    found = True
        assert found

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_info(self, mock_print):
        renderer = RichRenderer()
        renderer.info("Sub-agent", "intent-reviewer")
        mock_print.assert_called_once()
        arg = mock_print.call_args[0][0]
        assert "Sub-agent" in arg
        assert "intent-reviewer" in arg

    @patch("sqaf.ui.rich_renderer.Prompt.ask")
    def test_prompt(self, mock_ask):
        mock_ask.return_value = "input_val"
        renderer = RichRenderer()
        res = renderer.prompt("Enter skill name", default="my-skill")
        assert res == "input_val"
        mock_ask.assert_called_once_with("\n[cyan]Enter skill name[/cyan]", default="my-skill")

    @patch("sqaf.ui.rich_renderer.Confirm.ask")
    def test_confirm(self, mock_ask):
        mock_ask.return_value = True
        renderer = RichRenderer()
        res = renderer.confirm("Confirm deletion", default=False)
        assert res is True
        mock_ask.assert_called_once_with("\n[cyan]Confirm deletion[/cyan]", default=False)

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_success(self, mock_print):
        renderer = RichRenderer()
        renderer.success("Passed")
        mock_print.assert_called_once_with("[green]✓[/green] Passed")

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_error(self, mock_print):
        renderer = RichRenderer()
        renderer.error("Failed")
        mock_print.assert_called_once_with("[red]✗[/red] Failed")

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_numbered_list(self, mock_print):
        renderer = RichRenderer()
        renderer.numbered_list(["One", "Two"])
        assert mock_print.call_count == 2
        calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert "One" in calls[0]
        assert "Two" in calls[1]

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_blank(self, mock_print):
        renderer = RichRenderer()
        renderer.blank()
        mock_print.assert_called_once_with()

    @patch("sqaf.ui.rich_renderer._console.print")
    def test_paragraph(self, mock_print):
        renderer = RichRenderer()
        renderer.paragraph("Hello Rich")
        mock_print.assert_called_once_with("  Hello Rich")
