# Data Test Proof of Concept (PoC)

Welcome to the Data Test PoC directory. This folder contains sample, self-contained AI Agent Skills designed specifically for testing and demonstrating the capabilities of the Skill Quality Assurance Framework (SQAF). 

## Purpose

The primary intention of this folder is to provide developers, QA engineers, and AI practitioners with immediate, ready-to-use artifacts to validate the framework's execution without needing to write a skill from scratch. You can use these sample skills to trigger the orchestrator, observe the sub-agent reviews, and understand the resulting assessment reports.

## Available Sample Skills

1. **`data-pipeline-etl`**: A skill designed to extract security-related events from application logs and transform them into structured JSON. This skill is useful for testing how the framework evaluates data processing logic and JSON output schemas.
2. **`containerized-environment-setup`**: A skill focused on infrastructure automation, validating a local orchestration layer using Docker Compose. This helps in testing how SQAF handles infrastructure and DevOps-related instructions.

## How to Test

You can test the framework using either the IDE Chat (Agent Embedded) mode or the CLI Runner.

### Option A: IDE Chat (Agent Embedded)

1. Open your IDE agent chat window (e.g., Claude Code, Antigravity, Cursor, Windsurf).
2. Point the agent at the `orchestrator.md` file.
3. Provide the path to one of the PoC skills to trigger the assessment:

```txt
Assess the quality of the following skill: ./data-test-poc/data-pipeline-etl/SKILL.md
```
or
```txt
Assess the quality of the following skill: ./data-test-poc/containerized-environment-setup/SKILL.md
```

### Option B: CLI Runner (`sqaf`)

You can also run the SQAF CLI directly against these directories. For example:

```bash
sqaf data-test-poc/data-pipeline-etl
```
or 
```bash
sqaf data-test-poc/containerized-environment-setup
```

Enjoy exploring the evaluation capabilities of SQAF!
