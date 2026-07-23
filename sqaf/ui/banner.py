"""
Startup banner — displayed only in interactive TTY sessions.

pyfiglet is an optional dependency (install with: pip install sqaf[interactive]).
If unavailable, a plain-text fallback is used automatically.

Design constraints (from spec):
  - Purely decorative — must not affect workflow execution.
  - Never raises an exception — any failure is silently swallowed.
  - Suppressed when stdout is not a TTY (agents, CI, pipes, redirects).
"""
from __future__ import annotations

import logging
import sys

_FONT = "standard"
_TITLE = "SQAF"
_VERSION = "v1.0.0"


def _figlet_text() -> str | None:
    """Return ASCII art string, or None if pyfiglet is unavailable."""
    try:
        from pyfiglet import Figlet  # type: ignore
        return Figlet(font=_FONT).renderText(_TITLE)
    except ImportError:
        return None


def render_banner() -> None:
    """
    Render the branded startup banner to the Rich console.

    Silently skipped when:
      - stdout is not a TTY (AI agents, CI/CD pipelines, piped output)
      - pyfiglet is not installed (falls back to plain text)
      - any rendering error occurs (framework execution continues normally)
    """
    if not sys.stdout.isatty():
        return

    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        ascii_art = _figlet_text()

        if ascii_art:
            content = f"[bold cyan]{ascii_art.rstrip()}[/bold cyan]"
        else:
            # Graceful fallback — no pyfiglet installed
            content = f"[bold cyan]{_TITLE}[/bold cyan]"

        console.print(
            Panel.fit(
                content,
                border_style="cyan",
                title=f"[dim]{_VERSION}[/dim]",
                padding=(0, 4),
            )
        )
        console.print()

    except Exception as exc:  # noqa: BLE001
        # Banner failure must never prevent framework execution.
        logging.debug("Banner rendering failed (suppressed): %s", exc)
