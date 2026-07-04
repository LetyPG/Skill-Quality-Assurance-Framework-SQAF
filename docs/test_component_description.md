# SQAF Test Component Description

This document details the testing architecture, component coverage, validation strategies, and execution commands for the Skill Quality Assurance Framework (SQAF).

---

## Testing Strategy & Design Invariants

SQAF is built around high-reliability invariants, and its test suite is designed to enforce:
1. **Determinism:** Tests must be completely deterministic, reproducible, and run in less than a second without external network dependencies.
2. **Strict Isolation:** Evaluators and renderers are decoupled from execution environments. Mocking/patching is used to control environment details (TTY status, process input/output).
3. **Behavioral Integrity:** Edge cases (cancellations, missing files, TTY errors, invalid arguments, scores out of range) must fail gracefully with correct exit status codes.

---

## Test Suites Catalog

The framework contains a total of **122 automated unit and integration tests** distributed across the following test modules:

| Test Module File | Target Component | Core Validation Focus | Number of Tests |
|------------------|------------------|-----------------------|-----------------|
| `tests/test_calculator.py` | `skills/assessment-summarizer/scripts/calculator.py` | Score aggregation, risk mapping, downgrade gates, and metric outputs. | 13 |
| `tests/test_session.py` | `sqaf/session.py` | `AssessmentSession` initialization, mandatory field rules, validation errors, and auto-population. | 14 |
| `tests/test_session_builder.py` | `sqaf/session_builder.py` | Interactive prompts vs. non-interactive command-line session builders. | 10 |
| `tests/test_skills_discovery.py` | `sqaf/skills_discovery.py` | Workspace scanning, nested directory resolution, and eval file/directory presence detection. | 10 |
| `tests/test_cli.py` | `sqaf/cli.py` | Argument parsing (`argparse` schema), flag combinations, and CLI subprocess execution. | 16 |
| `tests/test_orchestrator.py` | `sqaf/orchestrator.py` | Orchestration workflow lifecycle (confirmation, cancellations, summary print, TTY exit codes). | 15 |
| `tests/test_banner.py` | `sqaf/ui/banner.py` | TTY-gated startup banner rendering, fallback when `pyfiglet` is missing, and exception safety. | 8 |
| `tests/test_runner.py` | `sqaf/runner.py` | Trigger prompt building (design-only vs. eval-enabled) and `trigger()` printing modes. | 12 |
| `tests/test_renderer.py` | `sqaf/ui/` (`renderer.py`, `plain_renderer.py`, `rich_renderer.py`) | Renderer factory logic (`get_renderer()`), raw print outputs, mock prompts, and Rich console structure testing. | 24 |

---

## Testing Commands

All testing commands must be executed within the virtual environment from the framework root (`skill-quality-assurance-framework/`):

### 1. Run the Full Test Suite
Runs all 122 tests with detailed verbose output:
```bash
./venv/bin/python -m pytest tests/ -v
```

### 2. Run a Specific Test Module
To run tests only for a particular module, target the file path:
```bash
# Test the score calculator & downgrade gates
./venv/bin/python -m pytest tests/test_calculator.py -v

# Test the orchestrator execution & TTY detection
./venv/bin/python -m pytest tests/test_orchestrator.py -v

# Test the output renderers
./venv/bin/python -m pytest tests/test_renderer.py -v
```

### 3. List / Collect All Tests Without Running Them
Useful for validating the test suite configuration and listing test names:
```bash
./venv/bin/python -m pytest tests/ --collect-only
```

---

## Mocking & Environment Isolation Strategy

To test UI and OS-dependent functionality without introducing flakiness, the test suite leverages standard Python unittest mock patches:

### 1. TTY Gating Simulation
The framework renders high-fidelity Rich panels only inside interactive TTY shells, falling back to plain text for automated pipes. Tests simulate both environments by patching `isatty()`:
```python
with patch.object(sys.stdout, "isatty", return_value=True):
    # Tests interactive TTY branch (e.g. RichRenderer, warning messages)
    ...
```

### 2. User Input Capture
Terminal input prompts are mocked to test interactive flows without hanging the test execution:
```python
with patch("builtins.input", return_value="y"):
    # Simulates the user confirming the prompt
    ...
```

### 3. Subprocess CLI Integration
`test_cli.py` executes the actual `sqaf` entry point in a sandbox subprocess. This ensures:
- The package installation matches the entry point behavior.
- Clean execution when piping stdout to an agent (non-TTY).
- Correct exit status codes on missing parameters (`exit != 0`).

---

## CI Pipeline

Every push and pull request targeting the `main` branch triggers the **GitHub Actions CI workflow** (`.github/workflows/ci.yml`). The pipeline enforces code quality automatically before tests are allowed to run.

### Pipeline Steps

| # | Step | Tool | Purpose |
|---|------|------|---------|
| 1 | **Checkout Repository** | `actions/checkout@v4` | Fetches the full source tree |
| 2 | **Set up Python** | `actions/setup-python@v5` (3.12) | Installs Python with pip cache enabled |
| 3 | **Install Dependencies** | `pip install -e ".[dev,interactive]"` | Installs `sqaf`, `pytest`, `ruff`, and `pyfiglet` |
| 4 | **Lint with ruff** | `ruff check sqaf/ tests/` | Checks style, imports, and code quality — fails fast on violations |
| 5 | **Run Test Suite** | `pytest tests/ -v` | Executes all 122 unit and integration tests |

### Lint Gate

The linting step uses [`ruff`](https://docs.astral.sh/ruff/) — a fast, zero-config Python linter that enforces PEP 8, import ordering, and common style rules. It runs **before** the test suite so that style violations are caught early without consuming test execution time.

```bash
# Run the same lint check locally before pushing
ruff check sqaf/ tests/
```

### Running CI Checks Locally

You can replicate the full CI pipeline locally from the framework root:

```bash
# 1. Install all dev dependencies
pip install -e ".[dev,interactive]"

# 2. Lint (mirrors CI lint step)
ruff check sqaf/ tests/

# 3. Run all tests (mirrors CI test step)
./venv/bin/python -m pytest tests/ -v
```

> [!TIP]
> Running `ruff check` locally before opening a pull request prevents CI failures and keeps the review cycle fast.