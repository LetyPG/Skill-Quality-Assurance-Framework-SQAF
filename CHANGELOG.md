# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2026-10-06

### Features
- Added `AGENT.md` root system manifest and discovery registry implementing multi-agent discovery and execution across CLI harnesses and IDE extensions.
- Implemented deterministic security and performance hook validation pipeline (`UserPromptSubmit`) with injection attack prevention, PII compliance checks, and complexity evaluations.
- Enforced deterministic skill path matchers within agent settings and orchestrator configuration.
- Added GitHub Actions CI pipeline with Ruff linting enforcement, isolated hook test steps, and automated Mermaid diagram rendering.
- Built interactive web documentation portal (`docs/index.html`) featuring dynamic Marked.js parsing, Mermaid.js execution, and SVG vector diagram compilation scripts.
- Introduced proof-of-concept data test suite (`data-test-poc/`) and contribution governance guidelines (`GOVERNACE_CONTRIBUTING.md`).

### Updates
- Enhanced orchestrator with ISO timestamped output artifacts and expanded trigger exclusion patterns.
- Added YAML frontmatter metadata and CLI usage specifications across all sub-agents.
- Updated documentation and `README.md` with single-session runtime constraints, system prompt immutability rules, and architecture decision records.
- Refactored CLI testing suite to leverage Python's `sys.executable` with module execution flags for cross-environment stability.

### Patches
- Resolved Ruff lint violations (`UP017`, `BLE001`, `S110`, `I001`, `SIM117`, `C408`, `PLW1510`, `RUF100`, `LOG015`) across hooks, tests, and core framework modules.
- Fixed Marked.js v12+ token compatibility, Highlight.js block mangling, and CDN asset fetching fallbacks in the web documentation portal.
- Fixed Mermaid diagram generation workflow permissions in GitHub Actions CI.
- Patched language detection exception handling in hook test fixtures to stabilize CI pipelines.

## [1.0.0] - 2026-07-02

### Features
- Initial release of the Skill Quality Assurance Framework (SQAF).
- Implemented core CLI runner, orchestrator engine, session builder, and markdown/JSON quality report renderers.
- Added multi-agent evaluation suites and test calculators for skill quality scoring.

### Updates
- Added framework documentation, architectural scaling roadmap, and licensing credentials.

### Patches
- Not applicable.
