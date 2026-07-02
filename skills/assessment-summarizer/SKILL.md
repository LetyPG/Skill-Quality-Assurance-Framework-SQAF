---
name: assessment-summarizer
description: Aggregates validated reviewer assessments into a consolidated Skill Quality Report. This skill performs deterministic score aggregation and report generation only. It never validates assessment artifacts or executes quality reviews.
---

# Purpose

Generate the final Skill Quality Assessment Report after the Orchestrator has completed workflow validation.

This skill is responsible only for:

* aggregating reviewer results;
* calculating overall quality metrics;
* determining the final recommendation;
* generating the final assessment artifacts.

The Orchestrator is solely responsible for validating workflow completion and assessment artifacts before invoking this skill.

---

# Responsibility
- This skill acts as the reporting layer of the Skill Quality Assurance Framework.
- It does not perform assessments.
- It does not validate artifacts.
- It does not repair missing information.
- It assumes every input artifact has already been validated by the Orchestrator.

---

# Goals

Generate:

* `assessment/assessment-summarizer.json`
* `assessment/skill-quality-report.md`

using the validated reviewer assessments provided by the Orchestrator.

---

# Inputs

## Rules
- The Orchestrator provides validated assessment artifacts.
- The presence of the execution assessment depends on whether execution review was requested.
- If the execution assessment is absent, the aggregation proceeds using Design Quality only.

## Input Artifacts 
- **Mandatory**: Reviewer assessments `<SKILL-NAME>-assessment/<agent-name>.json`
- **Optional**: If were executed the execution assessment made  by eval review `<SKILL-NAME>-assessment/eval-review.json`

---

# Responsibilities

The skill SHALL:

* read reviewer scores;
* aggregate reviewer findings;
* aggregate recommendations;
* calculate Design Quality;
* calculate Execution Quality (if available);
* calculate Overall Quality;
* determine the overall risk level;
* determine the final recommendation;
* summarize reviewer results;
* generate JSON report;
* generate Markdown report.

---

# Aggregation Instructions

| Steps | Description |
|-------|-------------|
| **Step 1:** | Load the validated assessment artifacts. |
| **Step 2:** | Extract reviewer information.<br>For each completed reviewer collect:<br>- score<br>- risk level<br>- findings<br>- recommendations<br>- resource consumption|
| **Step 3:** | Calculate Design Quality. <br>**Rules:**<br>Use `scripts/calculator.py`, provide as arguments the scores of the `intent-review`, `instruction-review`, `qa-review`, and recive Design Quality score.<br>**Note:** Only completed reviewers participate in the calculation. |
| **Step 4:** | Calculate Execution Quality. If an execution assessment exists, provide the `execution-review` score to the `scripts/calculator.py` script and recive Execution Quality score. Otherwise, Execution Quality is reported as `NOT ASSESSED`.<br>**Note:** No score shall be calculated. |
| **Step 5:** | Calculate Overall Quality.<br>**Rules:**<br>Use `scripts/calculator.py`, provide as arguments the scores of the `intent-review`, `instruction-review`, `qa-review`, `execution-review`, and recive Overall Quality score. |
| **Step 6:** | Calculate  Overall Risk.Use the `scripts/calculator.py` script, provide as arguments the risk levels,of all completed reviewers, and recive Overall Risk score. |
| **Step 7:** | Determine Final Recommendation.The recommendation shall be computed by
`script/calculator.py.` (see **Recomendation Suggested Mapping**) .

 |
| **Step 8:** | Aggregate Findings. Merge reviewer findings preserving:<br>- reviewer<br>- severity<br>- message<br>- evidence. <br> **Rule:** 
Do not modify reviewer findings. |
| **Step 9:** | Aggregate Recommendations.<br>- Merge reviewer recommendations.<br>- Duplicate recommendations should be consolidated.(see **Recommendation Consolidation**) |
| **Step 10:** | Calculate Resource Consumption.<br>- Aggregate the resources consumed by all completed reviewers:<br>  * input tokens<br>  * output tokens<br>  * total tokens<br>  * execution time<br>- Include the Aggregator's own resource usage.<br> **Rule:** Resource total are computed by Σ reviewer values + Aggregator values |
| **Step 11:** | Generate Reports (see **Output Artifacts**) |

---

### Recomendation Suggested Mapping (calculate using the script/calculator.py)

The calculator implements:
- recommendation thresholds;
- downgrade rules;
- future framework versions

The Aggregator must never reimplement this logic.

### Recommendation Consolidation

Recommendations shall be consolidated by:

1. Exact duplicate removal.

2. Semantic duplicate detection
(case-insensitive normalized text).

3. Grouping by category. Ordering:
- CRITICAL
- HIGH
- MEDIUM
- LOW

---
### Reviewers are processed in the following order:

1. Intent Review
2. Instruction Review
3. QA Review
4. Eval Review

The generated report preserves this ordering.

---

## Output Artifacts

1. **Generate the JSON report**: in `<SKILL-NAME>-assessment/assesssment-summarizer.json`. 
   - See **JSON Schema**.Use the schema provided in `assets/assessment-summarizer-schema.json` 
   - Populate all mandatory fields defined by the framework.

2. **Generate the Markdown report**: in `<SKILL-NAME>-assessment/skill-quality-report.md`. 
   - See **Markdown Format**.Use the format provided in `assets/skill-quality-report-template.md` 
   - Populate all mandatory fields defined by the framework.

**The reports should include:**

* Assessment Summary
* Overall Scores
* Skill Classification
* Reviewer Summary
* Executive Findings
* Reviewer Findings
* Validation Summary
* Resource Consumption
* Final Recommendation
* Assessment Artifacts

---

# Constraints

| Type   | Rule  |
| ------ | ----- |
| Must   | Aggregate only validated reviewer outputs.<br>Preserve reviewer findings without modification.<br>Generate both JSON and Markdown reports.<br>Calculate scores deterministically using the `scripts/calculator.py` script.<br>Aggregate resource consumption.<br>Produce reproducible reports from identical inputs.<br>It only summarizes, aggregates, and computes framework-level metrics.<br>Do not estimate missing metrics.<br>Preserve reviewer evidence.<br> Reference Reference original reviewer artifacts instead of rewriting evidence.<bnr>Use canonical framework artifact names.|
| Should | Consolidate duplicate recommendations.<br>Present findings in a consistent order.<br>Keep report formatting deterministic.     |
| Could  | Sort recommendations by severity.<br>Highlight the strongest reviewer strengths separately.          |
| Won't  | Validate assessment artifacts.<br>Verify workflow completion.<br>Repair missing artifacts.<br>Recalculate or modify reviewer scores.<br>Modify reviewer findings.<br>Generate new findings.<br>Perform quality reviews.<br>Invoke external resources.<br>Execute another reviewer.<br>Never reinterpret reviewer conclusions. <br> Reimplement calculator algorithms or modify the `scripts/calculator.py` script.<br>Perform mathematical calculations independently, except the resources consumption mentioned in step 10<br> Change reviewer ordering.   |

---

# Design Principles

The Aggregator follows these principles:

* Single Responsibility
* Deterministic Processing
* Evidence Preservation
* Read-only Assessment Consumption
* Reproducible Report Generation
---

# Completion Criteria

The skill completes successfully when:

* both report artifacts are generated;
* aggregation calculations are completed;
* overall recommendation is determined;
* resource consumption is reported.

No additional validation shall be performed by this skill.

The Orchestrator is responsible for validating the generated reports after completion.
