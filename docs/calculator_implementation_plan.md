# Implementation Plan: Skill Quality Calculator

This document details the design, mathematical formulas, and implementation strategy for `scripts/calculator.py` as required by the **Skill Quality Assurance Framework (SQAF)**.

---

## 1. Architectural Role
The calculator is a standalone, deterministic utility script designed to:
1. Parse and validate raw reviewer scores and risk levels.
2. Compute aggregated metrics: **Design Quality**, **Execution Quality**, **Overall Quality**, and **Overall Risk**.
3. Apply standard framework-level **Downgrade Rules** to ensure risk is properly represented in recommendations.
4. Output a final, validated **Recommendation** alongside calculated metrics in a machine-readable JSON format.

It operates strictly as a pure function: given the same inputs, it produces the identical outputs. It does not read or write assessment files directly; it acts as the mathematical engine for the `assessment-summarizer` skill.

---

## 2. Input Specification & Validation

The calculator will accept inputs for all four reviewers. Design reviewers are mandatory for calculating Design Quality, whereas the execution reviewer is optional.

### 2.1 Inputs
- **Scores** (`intent_score`, `instruction_score`, `qa_score`, `execution_score`): 
  - Type: Float/Integer (representing a score between `0` and `100`), or `None` if the reviewer was skipped/failed.
- **Risks** (`intent_risk`, `instruction_risk`, `qa_risk`, `execution_risk`):
  - Type: String matching `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` (case-insensitive), or `None` if skipped/failed.

### 2.2 Validation Logic
- All numerical scores must satisfy $0 \le \text{score} \le 100$. Any value outside this range will trigger an immediate execution failure with a descriptive error message.
- All risk levels must belong to the closed set `{"LOW", "MEDIUM", "HIGH", "CRITICAL"}`. Case will be normalized to uppercase.
- If a score is provided, its corresponding risk must also be provided, and vice-versa.
- If all design inputs are missing, the calculator will fail as design assessment is a framework prerequisite.

---

## 3. Mathematical Formulas & Calculation Logic

### 3.1 Design Quality
Design Quality aggregates the Design Review Layer (`intent-review`, `instruction-review`, and `qa-review`).

$$\text{Design Quality} = \text{round}\left( \frac{\sum_{i \in \text{Completed Design Reviewers}} \text{Score}_i}{N_{\text{Completed Design Reviewers}}} \right)$$

- **Rule:** Only completed reviewers participate in the calculation.
- **Rounding:** Rounded to the nearest integer.

### 3.2 Execution Quality
Execution Quality reflects the Execution Review Layer (`eval-review`).

- **Rule:** If the execution assessment exists, Execution Quality is the `execution-review` score (rounded to the nearest integer).
- **Rule:** If the execution assessment is absent, Execution Quality is reported as `null` (representing `NOT ASSESSED` in the output schema).

### 3.3 Overall Quality
Overall Quality blends Design Quality and Execution Quality.

- **Scenario A: Execution Quality is Assessed**
  $$\text{Overall Quality} = \text{round}\left( 0.5 \times \text{Design Quality} + 0.5 \times \text{Execution Quality} \right)$$
- **Scenario B: Execution Quality is `null` (NOT ASSESSED)**
  $$\text{Overall Quality} = \text{Design Quality}$$

### 3.4 Overall Risk
Risk levels are aggregated using an ordinal mapping to identify the highest observed risk:

$$\text{Risk Value} = \max_{r \in \text{Completed Reviewer Risks}} \text{Map}(r)$$

Where:
- $\text{Map}(\text{LOW}) = 1$
- $\text{Map}(\text{MEDIUM}) = 2$
- $\text{Map}(\text{HIGH}) = 3$
- $\text{Map}(\text{CRITICAL}) = 4$

The maximum value is then mapped back to the corresponding string identifier. If no reviewers have completed, the default risk is `LOW`.

---

## 4. Downgrade & Recommendation Logic

### 4.1 Preliminary Recommendation Mapping
A candidate recommendation is first determined using the Overall Quality score:

| Overall Quality Score Range | Candidate Recommendation |
|-----------------------------|--------------------------|
| $85 \le \text{Score} \le 100$ | `APPROVED` |
| $70 \le \text{Score} < 85$  | `APPROVED WITH IMPROVEMENTS` |
| $50 \le \text{Score} < 70$  | `REQUIRES REVISION` |
| $0 \le \text{Score} < 50$   | `NOT APPROVED` |

### 4.2 Downgrade Rules
The preliminary recommendation is subjected to the following gating rules in sequence:

1. **Risk Escalation Downgrade:**
   - If Overall Risk is `CRITICAL`, the final recommendation is downgraded to `NOT APPROVED`.
   - If Overall Risk is `HIGH`, the final recommendation cannot exceed `REQUIRES REVISION`. If the candidate was `APPROVED` or `APPROVED WITH IMPROVEMENTS`, it is downgraded to `REQUIRES REVISION`.

2. **Severe Score Deficit Downgrade:**
   - If *any* completed individual reviewer score is $< 60$, the final recommendation cannot exceed `REQUIRES REVISION`.
   - If *any* completed individual reviewer score is $< 40$, the final recommendation is downgraded to `NOT APPROVED`.

3. **Design-Execution Discrepancy Downgrade:**
   - If both Design Quality and Execution Quality are assessed, and their absolute difference exceeds 40 points ($|\text{Design Quality} - \text{Execution Quality}| > 40$), the recommendation is downgraded by exactly one level (e.g., from `APPROVED` to `APPROVED WITH IMPROVEMENTS`, or from `APPROVED WITH IMPROVEMENTS` to `REQUIRES REVISION`). This prevents approving a skill that has high design scores but performs poorly, or vice-versa.

---

## 5. Command-Line & Programmatic Interface

The calculator will be written in standard Python (no external dependencies required) and support both a programmatic API and a command-line interface.

### 5.1 CLI Usage
The script will accept arguments as flags. Missing optional flags (e.g., execution parameters) will default to `None`.

```bash
python scripts/calculator.py \
  --intent-score 90 --intent-risk LOW \
  --instruction-score 85 --instruction-risk MEDIUM \
  --qa-score 80 --qa-risk LOW \
  --execution-score 95 --execution-risk LOW
```

### 5.2 CLI JSON Output Format
The CLI will print a single structured JSON object to stdout. All logs or diagnostic messages must go to stderr.

```json
{
  "design_quality": 85,
  "execution_quality": 95,
  "overall_quality": 90,
  "overall_risk": "MEDIUM",
  "final_recommendation": "APPROVED"
}
```

If execution review is skipped:
```json
{
  "design_quality": 85,
  "execution_quality": null,
  "overall_quality": 85,
  "overall_risk": "MEDIUM",
  "final_recommendation": "APPROVED WITH IMPROVEMENTS"
}
```

---

## 6. Verification and Test Plan
To ensure correctness, the implementation will include:
1. **Unit Tests:** A suite of test cases covering all edge cases, score boundaries, risk combinations, and downgrade triggers.
2. **Validation Rules Verification:** Assertions testing that invalid scores (e.g., negative or > 100) or invalid risk strings are properly caught and reported.
3. **Execution Quality Absence:** Verify calculations behave correctly when `--execution-score` and `--execution-risk` are omitted.
