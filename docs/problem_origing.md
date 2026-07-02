# Problem Origin& Background

## 1. Current situation

AI agents are becoming increasingly capable, but often don’t have the context they need to do real work reliably.Skills solve this by packaging procedural knowledge and company-, team-, and user-specific context into portable, version-controlled folders that agents load on demand. 

### Market Context

The companies are starting to build libraries of skills for:

* Claude Code
* Cursor Agents
* GitHub Copilot Agents
* Windsurf
* OpenAI Codex Agents
* IDE Agents
* Plataformas multiagente

The problem is that normally we validate:

```txt
Skill
 ↓
Agent
 ↓
Result
```

but there is no mature discipline to answer:

- Design & Maintainability:
    - Is the skill well designed?
    - Does the skill induce errors?
    - Is the skill's instruction set clear, or is it ambiguous and prone to degradation?
- Robustness:
    - Does the skill introduce subtle context consumption inefficiencies or hallucination risks?
    - Does the skill have ambiguous instructions?
- Consistency:
    - Does the skill produce consistent results?
    - Does the skill behave reliably under varied context lengths or models?


In other words: *We need QA over the skills.*


---
## 2. What is an Agent Skill?

A standardized way to give AI agents new capabilities and expertise to dfevelope specifics tasks.

Agent Skills are a lightweight, open format for extending AI agent capabilities with specialized knowledge and workflows.
At its core, a skill is a folder containing a SKILL.md file. This file includes metadata (name and description, at minimum) and instructions that tell an agent how to perform a specific task. Skills can also bundle scripts, reference materials, templates, and other resources.

```txt
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```
**Why Agent Skills?**

This gives agents:

- **Domain expertise**: Capture specialized knowledge — from legal review processes to data analysis pipelines to presentation formatting — as reusable instructions and resources.
- **Repeatable workflows**: Turn multi-step tasks into consistent, auditable procedures.
- **Cross-product reuse**: Build a skill once and use it across any skills-compatible agent.

**How do Agent Skills work?**

Agents load skills through progressive disclosure, in three stages:

- **Discovery**: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.
- **Activation**: When a task matches a skill’s description, the agent reads the full SKILL.md instructions into context.
- **Execution**: The agent follows the instructions, optionally executing bundled code or loading referenced files as needed.

Full instructions load only when a task calls for them, so agents can keep many skills on hand with only a small context footprint.

​
**Where can I use Agent Skills?**

Agent Skills are supported by a large number of AI tools and agentic clients (e.g: claude code, cursor agents, kiro, vita, opencode, Gemini CLI, GitHub Copilot Agents, Databricks Genie Code, Windsurf, OpenAI Codex Agents, Antigravity, Roo Code, ...) 

**Open development**

The Agent Skills format was originally developed by Anthropic, released as an open standard, and has been adopted by a growing number of agent products. The standard is open to contributions from the broader ecosystem.

---

## 3. Problem Solution: Skill Quality Assurance Framework

### Goal

Provide a systematic approach to evaluating the quality of skills used by AI agents in AI-Native Workflows. It includes:

1. Input Validation: Ensures that the skill is well-designed and meets the required standards.
2. Reviewer Execution: Triggers independent reviewers to assess the skill.
3. Artifact Validation: Ensures that the assessment artifacts are complete and accurate.
4. Aggregation: Generates a final skill quality report.
5. Reproducibility: Ensures that the assessment can be reproduced.


### Which are  Skill Reviewer Limits

* Does not review the system under test.
* Does not review the LLM.
* Does not review the agent.
* It must be agnostic to the business logic and the skill application domain.

Reviews:

```txt
Skill
 ↓
Quality
 ↓
Risk
 ↓
Expected Reliability
```

###  Beneficts 

- Improve skill quality, reliability and performance.
- Improve skill reproducibility.
- Establish a standard for skill evaluation.
- Provide a framework for skill assessment.
- By applying the shift left paradigm, using the design assessment layer, it can improve the quality of the skills and reduce the cost of the errors.
- Simplify resource consumption instead of several runs and iterations to improve the skill quality it can be done in a single or less runs.
- Support the development of new skills by providing a framework for skill evaluation.

---
## 4. Project Implementation Decisions
This Project will be implemented in two generations of reviewers:
- General Skills Reviewers (current)
- Domain Specific Skills Reviewers for QA process (future)

>Note: At this point the project is only focused in General Skills Reviewers.

### First generation of reviewers (General Skills Reviewers)

This generation tries to answer two main questions:

1. Is the skill well designed?
2. Does the skill produce good results when executed?

**Basic Universal Reviewers**

- Intent Reviewer
- Instruction Reviewer
- QA Reviewer 
- Eval Reviewer 

This model allows answer main questions with 3 categories of outputs:
- The skill is well designed but executes poorly.
- The skill executes well but is poorly designed and difficult to maintain.
- The skill executes well, is well designed and is efficient.

**Assessment Overview**
By applyin 2 layers: Design Assessment and execution Assessment

                   Skill
                       │
                       ▼

          ┌───────────────────────┐
          │ Skill Design Review   │
          └───────────────────────┘

               │      │      │
               ▼      ▼      ▼

         Intent Reviewer
         Instruction Reviewer
         QA Reviewer (Context, Hallucination prevention, output contract, and evaluation methodology)

                       │
                       ▼

              Skill Execution

                       │
                       ▼

              Eval Results Reviewer

                       │
                       ▼

             Assessment Aggregator

                       │
                       ▼

              Skill Quality Report



### Second generation of reviewers (Domain Specific Skills Reviewers for QA process)

This generation tries to answer two main questions:

1. Is the skill well designed according the domain QA process, including, fundamentals, methodologies, standards and best practices?
2. Does the skill produce good results when executed according to Software QA purpose?

**Especialized Reviewers**

- Requirements Reviewer
- Test Design Reviewer
- Automation Reviewer
- Code Reviewer
- Defect Analysis Reviewer
- Test Strategy Reviewer
- AI-Assisted QA Reviewer

#### 4.1 QA Domains where Skills Exist (For Future Implementations)

**Initial Taxonomy.**

Agrupación de las tareas QA en dominios funcionales.

| Dominio | Skills description |Ejemplos |
| :--- | :--- | :--- |
| 1- Requirements Analysis | Skills orientadas a: analizar historias, detectar ambigüedades, detectar inconsistencias, identificar criterios faltantes | `Review User Story`, `Generate Acceptance Criteria`, `Find Ambiguities`, `Find Missing Requirements |
| 2- Test Design | Skills que generan: test cases, test scenarios, decision tables, pairwise combinations | `Generate Test Cases`, `Generate Boundary Tests`, `Generate Exploratory Scenarios`, `Generate Negative Tests` |
| 3- Test Automation | Skills que generan: Selenium, Playwright, Cypress, API tests | `Generate Playwright Test`, `Generate Page Object`, `Generate API Test`, `Generate Test Data Builder |
| 4- Code Review | Skills para revisar: test code, framework architecture, maintainability | `Review Playwright Architecture`, `Review Test Maintainability`, `Review Selector Strategy |
| 5- Defect Analysis | Skills para: analizar bugs, identificar root causes | `Bug Analysis`, `Root Cause Analysis`, `Failure Classification |
| 6- Test Strategy | Skills para: planes QA, cobertura, riesgos | `Generate Test Plan`, `Risk Analysis`, `Coverage Review |
| AI-Assisted QA | Muy importante. Skills específicas para IA. | Prompt Review, Agent Workflow Review, Skill Review, Agent Contract Review |


#### 4.2 Reviewers Architecture (ROADMAP-1-SKILL-REVIEWER for QA Process)

Decision: Do not build one giant reviewer, but build reviewers by domain.
Justification:
* Efficiency through parallel processing of reviews.
* Improved precision of verification criteria over specific domain objectives.
* Better control of the context window and token economy.
* Avoids hallucination and context contamination or false positives/negatives (e.g., the reviewer validates a skill that analyzes framework architecture and also the tests and interfaces produced by another skill).
* For greater coverage and quality, given that the domains are different and require different approaches.
* Maintainability of the components.
* Reusability of the components.
* Scalability.

```txt
                    Skill
                       │
                       ▼
             Reviewer Orchestrator
                       │
      ┌────────────────┼────────────────┐
      │                │                │
      ▼                ▼                ▼

Requirement      Test Design      Automation
Reviewer          Reviewer         Reviewer

      ▼                ▼                ▼

Prompt         Architecture      Skill Logic
Reviewer       Reviewer          Reviewer
```
