"""Workspace scanner — discovers skill directories containing SKILL.md."""
from __future__ import annotations

from pathlib import Path


def discover_skills(root: str = ".", max_depth: int = 4) -> list[str]:
    """
    Returns a sorted list of absolute directory paths that contain a SKILL.md,
    searched up to *max_depth* levels below *root*.

    Hidden directories (name starting with '.') are skipped.
    """
    root_path = Path(root).resolve()
    results: list[str] = []

    def _walk(path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            for child in sorted(path.iterdir()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                if (child / "SKILL.md").exists():
                    results.append(str(child))
                _walk(child, depth + 1)
        except PermissionError:
            pass

    _walk(root_path, 0)
    return results


def skill_has_evals(skill_path: str) -> bool:
    """
    Returns True when the skill directory contains an evals/ sub-directory
    or an eval.json file — either signals that execution review is possible.
    """
    p = Path(skill_path)
    return (p / "evals").is_dir() or (p / "eval.json").exists()
