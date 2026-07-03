# Governance & Contributing Guide

Welcome to Skill Quality Assurance Framework.

This document defines how the project is governed, how contributions are reviewed, the expected standards of conduct, and the security principles that guide development.

The goal is to maintain a collaborative, professional, and sustainable open-source project focused on evaluating the quality, structure, and execution of AI agent skills.

---

# Project Mission

Skill Quality Assurance Framework (SQAF) exists to provide a systematic, "shift-left" approach to validating AI-native skill artifacts before deploying them to agent libraries.

The project prioritizes:

* Shift-Left Quality Assurance
* Defect Prevention
* Deterministic Assessments
* Specialized Expert Review
* CI/CD Ready Architecture
* Maintainable and Extensible Framework

---

# Governance Model

The project follows a Maintainer-Led Governance model.

Maintainers are responsible for:

* Reviewing pull requests
* Managing releases
* Approving architectural changes
* Maintaining project documentation
* Ensuring alignment with project principles

Contributors are encouraged to propose improvements, but acceptance is based on technical merit, maintainability, project scope, and architectural consistency.

---

# Architectural Principles

All contributions should respect the following principles.

## AI-Agent-Driven Processing

The framework is an AI-agent-driven validation system. It depends on existing LLM preconditions being set up in the execution environment. Contributions should integrate seamlessly with executing sub-agents and orchestration logic.

---

## Deterministic Processing

Given the same input, the system should produce reproducible, evidence-based reviews with identical results for identical inputs.

Non-deterministic behavior should be avoided whenever possible, enforcing structured output validation schemas.

---

## Minimal Dependencies

Dependencies should be carefully evaluated.

Every new dependency increases:

* maintenance burden;
* security surface;
* installation complexity.

---

## Reviewer Isolation Rules

To prevent cognitive bias and context contamination:
1. Reviewers operate completely independently.
2. Reviewers do not inspect other reviewers' assessments.
3. The Assessment Summarizer strictly functions as a reporting aggregator.

---

## Security by Design

Evaluation of skills and test execution must prioritize safety and isolated execution logic over convenience.

---

# How to Contribute

Contributions are welcome from:

* Developers
* QA Engineers
* Technical Writers
* Architects
* AI Practitioners
* Open Source Contributors

Examples include:

* Bug fixes
* Documentation improvements
* Test enhancements
* Validation improvements
* Performance optimizations
* Reviewer sub-agent improvements
* New assessment quality dimensions

---

# Development Workflow

## 1. Fork the Repository

Create a personal fork of the project.

## 2. Create a Branch

**Branch Source**
As a branch source to create a new branch, use the branch `contribution`

Recommended naming conventions:

feature/<description>

bugfix/<description>

docs/<description>

Example:

feature/artifact-validator

---

## 3. Implement Changes

Keep changes focused.

Avoid mixing unrelated improvements in a single pull request.

---

## 4. Add Tests

New functionality should include tests whenever practical.

Bug fixes should include regression tests whenever possible.

---

## 5. Submit a Pull Request

Pull requests should include:

* Description of changes
* Motivation
* Testing evidence
* Documentation updates if required

---

# Pull Request Requirements

A pull request should:

* Build successfully
* Pass all automated tests
* Maintain existing functionality
* Include appropriate documentation
* Preserve deterministic execution
* Respect project architecture
* Avoid introducing security regressions

Maintainers may request revisions before approval.

---

# Architecture Changes

Major architectural changes should be discussed before implementation.

Examples include:

* New processing pipelines
* Changes to validation philosophy
* Changes to document models
* External service integrations
* Significant dependency additions

Maintainers may request an ADR (Architecture Decision Record) before approving such changes.

---

# Community Standards

All participants are expected to behave professionally and respectfully.

The project values:

* Constructive feedback
* Technical discussion
* Evidence-based decisions
* Collaborative problem solving

Disagreements are normal.

Personal attacks are not.

---

# Unacceptable Behavior

The following behaviors are not tolerated:

* Harassment
* Discrimination
* Personal attacks
* Threats
* Intimidation
* Trolling
* Offensive or abusive language
* Publishing private information without consent

Maintainers may remove content or restrict participation when necessary.

---

# Security Principles

The project evaluates potentially untrusted AI agent skills and their execution logic.

Security is therefore a core concern.

Contributors should follow secure development practices and consider the impact of every change on skill evaluation and isolated execution safety.

---

# Security Expectations

Contributors should:

* Validate inputs
* Handle malformed or ambiguous skills safely
* Avoid unsafe execution techniques in eval validation
* Minimize dependency risk
* Follow least-complexity solutions
* Preserve framework validation mechanisms and gates

---

# Vulnerability Reporting

Please do not publicly disclose security vulnerabilities before maintainers have an opportunity to investigate.

Security reports should include:

* Affected version
* Reproduction steps
* Potential impact
* Supporting evidence

Maintainers will review reports and determine appropriate remediation.

---

# Supported Scope

This project is primarily intended for:

* AI agent skill assessment
* Skill instructions and quality gates evaluation
* Intent and QA review automation
* Execution result validation
* AI agent workflow enhancement
* CI/CD agentic quality integration

The project is not intended to be:

* A general-purpose LLM benchmarking suite
* A code generation framework
* A generic testing library
* A standalone agent execution platform

---

# Decision-Making Philosophy

When multiple solutions exist, preference should be given to the option that best preserves:

1. Simplicity
2. Determinism
3. Security
4. Maintainability
5. Local-first execution

Features that significantly increase complexity without proportional value may be rejected.

---

# Final Note

By contributing to this project, you agree to follow this guide, respect fellow contributors, and help maintain a secure, professional, and sustainable open-source project.

Thank you for contributing to the Skill Quality Assurance Framework (SQAF).
