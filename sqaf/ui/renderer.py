"""
Renderer Protocol + factory function.

Both RichRenderer and PlainRenderer must implement this interface.
The session builder and orchestrator reference only Renderer — never a
concrete implementation — keeping them fully testable without a terminal.
"""
from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderer(Protocol):
    """Common interface for all output renderers."""

    def header(self, title: str) -> None: ...
    def step(self, n: int, total: int, label: str) -> None: ...
    def info(self, label: str, value: str) -> None: ...
    def prompt(self, question: str, default: str | None = None) -> str: ...
    def confirm(self, question: str, default: bool = True) -> bool: ...
    def success(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def numbered_list(self, items: list[str]) -> None: ...
    def blank(self) -> None: ...
    def paragraph(self, text: str) -> None: ...


def get_renderer() -> Renderer:
    """
    Factory — returns RichRenderer for interactive TTY sessions,
    PlainRenderer for agents, CI/CD, and pipes.

    Detection rule (from spec):
        sys.stdout.isatty() == True  →  RichRenderer
        sys.stdout.isatty() == False →  PlainRenderer
    """
    if sys.stdout.isatty():
        from sqaf.ui.rich_renderer import RichRenderer
        return RichRenderer()
    from sqaf.ui.plain_renderer import PlainRenderer
    return PlainRenderer()
