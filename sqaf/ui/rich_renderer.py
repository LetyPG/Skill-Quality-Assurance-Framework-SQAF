"""
RichRenderer — rich-based renderer for interactive TTY sessions.
Only imported when sys.stdout.isatty() is True (see renderer.get_renderer).
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

_console = Console()


class RichRenderer:
    """Visual, rich-formatted output for human interactive sessions."""

    def header(self, title: str) -> None:
        _console.print()
        _console.print(Panel.fit(
            f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        ))
        _console.print()

    def step(self, n: int, total: int, label: str) -> None:
        _console.print(Rule(
            f"[bold]Step {n} of {total}[/bold] — {label}",
            style="cyan",
        ))
        _console.print()

    def info(self, label: str, value: str) -> None:
        _console.print(f"  [dim]{label:<24}[/dim] [bold]{value}[/bold]")

    def prompt(self, question: str, default: str | None = None) -> str:
        return Prompt.ask(
            f"\n[cyan]{question}[/cyan]",
            default=default or "",
        )

    def confirm(self, question: str, default: bool = True) -> bool:
        return Confirm.ask(
            f"\n[cyan]{question}[/cyan]",
            default=default,
        )

    def success(self, message: str) -> None:
        _console.print(f"[green]✓[/green] {message}")

    def error(self, message: str) -> None:
        _console.print(f"[red]✗[/red] {message}")

    def numbered_list(self, items: list[str]) -> None:
        for i, item in enumerate(items, 1):
            _console.print(f"  [cyan]{i}.[/cyan] {item}")

    def blank(self) -> None:
        _console.print()

    def paragraph(self, text: str) -> None:
        _console.print(f"  {text}")
