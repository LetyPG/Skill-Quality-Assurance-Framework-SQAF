# SQAF CLI User Guide

## Why This Feature Exists

The Skill Quality Assurance Framework was originally designed to be used by AI coding assistants embedded in IDEs (Claude Code, Antigravity, Cursor, Windsurf, etc.). In that mode, the user triggers an assessment by typing a prompt in the chat window, and the embedded agent orchestrates the entire workflow conversationally.

This worked well for developers working directly inside an IDE. But as the framework matured, a new requirement emerged:

> **AI agent CLI tools** — tools like Claude Code CLI, Codex CLI, Antigravity CLI, and Gemini CLI — run outside the IDE as standalone processes. They need to invoke SQAF programmatically, not through a chat window.

Without a CLI entry point, those tools had no deterministic way to trigger an assessment. They would need to synthesize the correct trigger prompt from memory or documentation — an unreliable, fragile approach.

The `sqaf` CLI solves this by providing a **stable, version-controlled entry point** that any agent (or human) can call identically:

```bash
sqaf
```

The CLI collects the necessary information through a guided conversation (or reads it from flags in automated mode), constructs a valid `AssessmentSession`, and emits the orchestrator trigger to stdout — which the embedding agent then acts on.

---

## Architecture Overview

```
Human / Agent CLI
       │
       ▼
    sqaf                          ← thin entry point
       │
       ▼
    cli.py                        ← argv parsing only, no logic
       │
       ▼
    session_builder.py            ← collects inputs (args → prompts → defaults)
       │
       ▼
    AssessmentSession             ← immutable, validated session object
       │
       ▼
    orchestrator.py               ← receives session, never prompts
       │
       ▼
    runner.py (print-trigger)     ← emits orchestrator trigger to stdout
```

**Key design constraint:** The CLI contains zero assessment logic. It only collects information and delegates.

---

## Installation

### Recommended: Virtual Environment (for developers and AI practitioners)

```bash
cd skill-quality-assurance-framework
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

pip install -e .
```

### Global Install

```bash
pip install sqaf
```

> [!NOTE]
> For AI practitioners, developers, and contributors, using a virtual environment is strongly recommended. It isolates `sqaf` and its dependencies (`rich`) from your system Python and other projects.

---

## Commands Reference

### Show help

```bash
sqaf --help
```

Output:

```
usage: sqaf [-h] [--eval y|n] [--output DIR] [--non-interactive] [SKILL_PATH]

Skill Quality Assessment Framework

positional arguments:
  SKILL_PATH         Path to the skill directory (must contain SKILL.md)

options:
  -h, --help         show this help message and exit
  --eval y|n         Run execution review (y/n)
  --output DIR       Output directory for assessment artifacts (default: assessment/)
  --non-interactive  Disable interactive prompts; all required values must be provided via flags

Examples:
  sqaf                                        # interactive guided mode
  sqaf skills/my-skill                        # pre-fill skill, prompt for the rest
  sqaf skills/my-skill --eval y               # pre-fill skill + eval flag
  sqaf skills/my-skill --eval y --non-interactive  # fully automated
```

---

## Usage Modes

### Mode 1 — Fully Interactive (human-guided)

Run `sqaf` with no arguments. The CLI guides you step by step: you provide the skill path, it validates it, then collects eval and output preferences before starting.

```bash
sqaf
```

```
╭─────────────────────────────────────────────╮
│  Skill Quality Assessment Framework (SQAF)  │
╰─────────────────────────────────────────────╯

  Welcome! I'll guide you through a structured skill quality assessment.

  SQAF uses a shift-left QA approach: it evaluates your AI skill's design
  quality before execution — identifying ambiguities, hallucination risks,
  and instruction gaps early, at significantly lower cost.

  After your assessment, use the quality report to refine your skill with
  an improvement agent, then re-assess once. This is far more efficient
  than running multiple full assessments iteratively.

  ⚠ Precondition    sqaf must be run inside an active AI agent CLI session.
                    (Claude Code, Antigravity, Gemini CLI, etc.)
                    The assessment trigger is printed to stdout for your agent to act on.
                    Without an active agent, no assessment artifacts will be produced.

── Step 1 of 4 — Select the skill to review ──
  Note    Only one skill can be assessed at a time.

Enter the path to the skill directory (must contain SKILL.md) (): /path/to/skills/my-skill

✓ Skill selected: my-skill

── Step 2 of 4 — Execution Review ──
  Note    No evals/ directory or eval.json found — execution review skipped.

── Step 3 of 4 — Output Directory ──
Assessment output directory (assessment/):

── Step 4 of 4 — Review Summary ──
  Skill                    my-skill
  Execution Review         Skipped
  Output                   assessment/
  Mode                     interactive

Start Assessment? [y/n] (y): y

✓ Starting Skill Assessment...

Assess the quality of the following skill: /absolute/path/to/skills/my-skill/SKILL.md
(execution review skipped — no evals provided)
Store results in: assessment/
```

---

### Mode 2 — Partially Pre-filled (path provided, prompts for the rest)

Provide the skill path as a positional argument. The CLI skips the skill selection step and prompts only for the remaining information.

```bash
sqaf skills/assessment-aggregator
```

```bash
sqaf skills/assessment-aggregator --eval y
```

---

### Mode 3 — Fully Non-Interactive (automated / CI / agent-driven)

Provide all required values as flags. No prompts are shown. Suitable for CI/CD pipelines and autonomous agent execution.

```bash
sqaf skills/assessment-aggregator --eval y --non-interactive
```

```bash
sqaf skills/assessment-aggregator --eval n --output reports/ --non-interactive
```

> [!IMPORTANT]
> In `--non-interactive` mode, `SKILL_PATH` is required. If it is missing or the path does not contain a `SKILL.md` file, the CLI exits with an error.

---

## Agent Precondition

> [!IMPORTANT]
> `sqaf` is a **trigger emitter**, not an assessment executor.

When you run `sqaf`, the CLI collects information, builds a session, and prints the orchestrator trigger to stdout:

```
Assess the quality of the following skill: /absolute/path/to/SKILL.md
(execution review skipped — no evals provided)
Store results in: assessment/
```

**No assessment files are produced by `sqaf` itself.** The trigger must be read and acted on by an active AI agent CLI session — Claude Code, Antigravity, Gemini CLI, or any compatible agent runner configured to watch its tool's stdout.


### Expected setup

| Scenario | What happens |
|---|---|
| `sqaf` run standalone in terminal | Trigger printed to stdout — no artifacts |
| `sqaf` run inside Claude Code CLI | Agent reads trigger, executes orchestrator, produces report |
| `sqaf` run in CI with agent subprocess | Agent reads trigger, executes orchestrator, produces report |

The agent must be **initialized and authorized** before calling `sqaf`. Configure `sqaf` as a tool or startup command in your agent's settings so it is available within the agent's execution context.

---

## Output

In all modes, once the session is confirmed, `sqaf` prints the orchestrator trigger to stdout:

```
Assess the quality of the following skill: /absolute/path/to/SKILL.md
with evals at /absolute/path/to/eval.json   ← only if --eval y
Store results in: assessment/
```

The embedding AI agent (Claude Code, Antigravity, Gemini CLI, etc.) reads this output and executes the assessment workflow as defined in `orchestrator.md`.

---

## Rendering Behavior

| Execution Context | Output Style |
|---|---|
| Interactive terminal (human) | Rich panels, colors, step indicators |
| AI agent subprocess | Plain UTF-8 text, no ANSI codes |
| CI/CD pipeline | Plain UTF-8 text, no ANSI codes |
| Piped output (`sqaf \| ...`) | Plain UTF-8 text, no ANSI codes |

The CLI auto-detects the context via `sys.stdout.isatty()`. No configuration is required.

---

## Integration with Agent CLI Tools

When an agentic CLI tool (Claude Code, Antigravity, Codex CLI, Gemini CLI) runs `sqaf`, the recommended flow is:

1. **Interactive mode** — the agent calls `sqaf` as a subprocess and streams stdout to the terminal. The human responds to prompts. The final trigger is captured and fed to the orchestrator.

2. **Automated mode** — the agent calls `sqaf <skill-path> --eval y --non-interactive`. It reads the clean trigger from stdout and submits it directly to the orchestrator agent.

This approach requires no hardcoding of skill paths or orchestrator syntax inside the agent's own logic. The CLI handles it.

### CLI Agents Setup Recomendations

### Option A — Local Project Config (Recommended)

Add a project-level instruction file so the agent automatically understands how to use `sqaf` when working in this repository.

**Claude Code → `.claude/CLAUDE.md`**

```markdown
## SQAF Skill Assessment

To assess a skill, use the `sqaf` CLI runner:

```bash
sqaf <path/to/skill> --eval y --non-interactive
```

Read the printed trigger from stdout and execute the orchestrator workflow
as defined in `skill-quality-assurance-framework/orchestrator.md`.

- Only one skill can be assessed per run.
- `--eval y` includes execution review (requires an `eval.json` file).
- `--eval n` runs design-only assessment (faster, lower token cost).
```

**Antigravity / Gemini CLI → `.gemini/GEMINI.md`**

```markdown
## SQAF Skill Assessment

When assessing a skill's quality, invoke the CLI runner:

```bash
sqaf <path/to/skill> --eval n --non-interactive
```

The command prints the orchestrator trigger to stdout.
Execute the workflow following `skill-quality-assurance-framework/orchestrator.md`.
```

---

### Option B — Global Agent Config

Configure `sqaf` once at the user level so it is available across all your projects.

**Claude Code → `~/.claude/CLAUDE.md`**

```markdown
## SQAF — Skill Quality Assessment Framework

When asked to assess a skill, use:

```bash
sqaf <skill-path> --eval y --non-interactive
```

Follow the printed trigger with the orchestrator defined in the project's
`skill-quality-assurance-framework/orchestrator.md`.
```

**Antigravity → `~/.gemini/GEMINI.md`**

```markdown
## SQAF — Skill Quality Assessment Framework

Assess AI agent skills using the sqaf CLI:

```bash
sqaf <skill-path> --eval n --non-interactive
```

Read the stdout trigger and execute the orchestrator workflow.
```

---

### Option C — CI/CD Pipeline (GitHub Actions)

Automate skill assessment on every pull request that modifies a skill directory.

```yaml
# .github/workflows/sqaf-assessment.yml
name: Skill Quality Assessment

on:
  pull_request:
    paths:
      - 'skills/**'
  push:
    branches: [main]
    paths:
      - 'skills/**'

jobs:
  generate-trigger:
    name: Generate Assessment Trigger
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install sqaf
        run: pip install sqaf

      - name: Generate orchestrator trigger
        id: trigger
        run: |
          sqaf skills/my-skill --eval n --non-interactive > trigger.txt
          cat trigger.txt

      - name: Upload trigger artifact
        uses: actions/upload-artifact@v4
        with:
          name: sqaf-trigger
          path: trigger.txt
```

> [!NOTE]
> In CI/CD, the trigger output (`trigger.txt`) is consumed by a downstream agent job configured with the appropriate API keys and orchestrator context. The pipeline above shows the trigger generation step; the agent execution step depends on your CI agent setup.

---

## Running the Test Suite

The CLI runner ships with a dedicated test suite. Run it from the framework root:

```bash
# Using the virtual environment
./venv/bin/python -m pytest tests/ -v

# Or with the activated venv
pytest tests/ -v
```

To run only CLI-related tests:

```bash
pytest tests/test_session.py tests/test_session_builder.py tests/test_skills_discovery.py -v
```

---

## Related Documentation

- [Development Guidelines](development_guideline.md) — engineering principles governing the framework
- [Problem Origin & Background](problem_origing.md) — why SQAF exists
- [Orchestrator Reference](../orchestrator.md) — the orchestrator rules and workflow
