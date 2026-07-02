"""
PlainRenderer — zero-dependency renderer for non-TTY contexts.
Used by AI agents, CI/CD pipelines, and piped output.
Produces clean UTF-8 text with no ANSI escape codes.
"""
from __future__ import annotations


class PlainRenderer:
    """Clean, zero-dependency output for automated contexts."""

    def header(self, title: str) -> None:
        line = "─" * (len(title) + 4)
        print(f"\n{line}")
        print(f"  {title}")
        print(f"{line}\n")

    def step(self, n: int, total: int, label: str) -> None:
        print(f"\nStep {n} of {total} — {label}\n")

    def info(self, label: str, value: str) -> None:
        print(f"  {label:<24} {value}")

    def prompt(self, question: str, default: str | None = None) -> str:
        if default:
            raw = input(f"{question} [{default}]: ").strip()
            return raw if raw else default
        return input(f"{question}: ").strip()

    def confirm(self, question: str, default: bool = True) -> bool:
        hint = "[Y/n]" if default else "[y/N]"
        raw = input(f"{question} {hint}: ").strip().lower()
        if not raw:
            return default
        return raw in ("y", "yes")

    def success(self, message: str) -> None:
        print(f"✓ {message}")

    def error(self, message: str) -> None:
        print(f"✗ {message}")

    def numbered_list(self, items: list[str]) -> None:
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")

    def blank(self) -> None:
        print()

    def paragraph(self, text: str) -> None:
        print(f"  {text}")
