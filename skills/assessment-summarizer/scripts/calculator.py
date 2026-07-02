#!/usr/bin/env python3
import sys
import json
import argparse

# Risk mapping definitions
RISK_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}
INV_RISK_MAP = {v: k for k, v in RISK_MAP.items()}

RECOMMENDATION_LEVELS = [
    "NOT APPROVED",
    "REQUIRES REVISION",
    "APPROVED WITH IMPROVEMENTS",
    "APPROVED"
]

def validate_and_parse_inputs(args):
    """
    Validates scores are between 0 and 100, and risks are valid categories.
    Returns a dictionary of validated parsed values or raises ValueError.
    """
    reviewers = ["intent", "instruction", "qa", "execution"]
    parsed = {}

    for rev in reviewers:
        score_val = getattr(args, f"{rev}_score")
        risk_val = getattr(args, f"{rev}_risk")

        # Check for co-presence (both must be present, or both must be absent)
        if (score_val is not None and risk_val is None) or (score_val is None and risk_val is not None):
            raise ValueError(
                f"Validation error: For reviewer '{rev}', both score and risk must be provided, or both must be omitted."
            )

        if score_val is not None:
            # Validate score range
            try:
                score_num = float(score_val)
            except ValueError:
                raise ValueError(f"Validation error: Score for '{rev}' must be a numeric value. Got '{score_val}'.")

            if not (0 <= score_num <= 100):
                raise ValueError(f"Validation error: Score for '{rev}' must be between 0 and 100. Got {score_num}.")
            
            # Validate risk category
            risk_str = str(risk_val).strip().upper()
            if risk_str not in RISK_MAP:
                raise ValueError(
                    f"Validation error: Risk for '{rev}' must be one of {list(RISK_MAP.keys())}. Got '{risk_val}'."
                )
            
            parsed[f"{rev}_score"] = score_num
            parsed[f"{rev}_risk"] = risk_str
        else:
            parsed[f"{rev}_score"] = None
            parsed[f"{rev}_risk"] = None

    # Check that at least design assessments are present (intent, instruction, qa)
    has_design = any(parsed[f"{rev}_score"] is not None for rev in ["intent", "instruction", "qa"])
    if not has_design:
        raise ValueError("Validation error: At least one design reviewer (intent, instruction, or qa) must be completed.")

    return parsed

def downgrade_recommendation(rec, levels_to_downgrade=1):
    """
    Downgrades recommendation string by a specified number of levels.
    """
    current_idx = RECOMMENDATION_LEVELS.index(rec)
    new_idx = max(0, current_idx - levels_to_downgrade)
    return RECOMMENDATION_LEVELS[new_idx]

def enforce_upper_bound_recommendation(current_rec, max_allowed_rec):
    """
    Ensures recommendation does not exceed a maximum allowed level.
    """
    curr_idx = RECOMMENDATION_LEVELS.index(current_rec)
    max_idx = RECOMMENDATION_LEVELS.index(max_allowed_rec)
    if curr_idx > max_idx:
        return max_allowed_rec
    return current_rec

def calculate_metrics(parsed):
    # 1. Compute Design Quality
    design_scores = [parsed[f"{rev}_score"] for rev in ["intent", "instruction", "qa"] if parsed[f"{rev}_score"] is not None]
    design_quality = round(sum(design_scores) / len(design_scores))

    # 2. Compute Execution Quality
    execution_score = parsed["execution_score"]
    execution_quality = round(execution_score) if execution_score is not None else None

    # 3. Compute Overall Quality
    if execution_quality is not None:
        overall_quality = round(0.5 * design_quality + 0.5 * execution_quality)
    else:
        overall_quality = design_quality

    # 4. Compute Overall Risk (Maximum risk level of completed reviewers)
    all_completed_risks = [parsed[f"{rev}_risk"] for rev in ["intent", "instruction", "qa", "execution"] if parsed[f"{rev}_risk"] is not None]
    overall_risk_val = max(RISK_MAP[r] for r in all_completed_risks)
    overall_risk = INV_RISK_MAP[overall_risk_val]

    # 5. Determine Preliminary Recommendation based on Overall Quality score
    if overall_quality >= 85:
        rec = "APPROVED"
    elif overall_quality >= 70:
        rec = "APPROVED WITH IMPROVEMENTS"
    elif overall_quality >= 50:
        rec = "REQUIRES REVISION"
    else:
        rec = "NOT APPROVED"

    # 6. Apply Downgrade Rules
    
    # Rule 6.1: Risk Escalation Downgrade
    if overall_risk == "CRITICAL":
        rec = "NOT APPROVED"
    elif overall_risk == "HIGH":
        rec = enforce_upper_bound_recommendation(rec, "REQUIRES REVISION")

    # Rule 6.2: Severe Score Deficit Downgrade
    all_completed_scores = [parsed[f"{rev}_score"] for rev in ["intent", "instruction", "qa", "execution"] if parsed[f"{rev}_score"] is not None]
    if any(s < 40 for s in all_completed_scores):
        rec = "NOT APPROVED"
    elif any(s < 60 for s in all_completed_scores):
        rec = enforce_upper_bound_recommendation(rec, "REQUIRES REVISION")

    # Rule 6.3: Design-Execution Discrepancy Downgrade
    if execution_quality is not None:
        discrepancy = abs(design_quality - execution_quality)
        if discrepancy > 40:
            rec = downgrade_recommendation(rec, 1)

    return {
        "design_quality": design_quality,
        "execution_quality": execution_quality,
        "overall_quality": overall_quality,
        "overall_risk": overall_risk,
        "final_recommendation": rec
    }

def main():
    parser = argparse.ArgumentParser(description="Skill Quality Assurance Calculator")
    
    # Score flags
    parser.add_argument("--intent-score", type=float, default=None, help="Intent reviewer score (0-100)")
    parser.add_argument("--instruction-score", type=float, default=None, help="Instruction reviewer score (0-100)")
    parser.add_argument("--qa-score", type=float, default=None, help="QA reviewer score (0-100)")
    parser.add_argument("--execution-score", type=float, default=None, help="Execution reviewer score (0-100)")

    # Risk flags
    parser.add_argument("--intent-risk", type=str, default=None, help="Intent reviewer risk (LOW|MEDIUM|HIGH|CRITICAL)")
    parser.add_argument("--instruction-risk", type=str, default=None, help="Instruction reviewer risk (LOW|MEDIUM|HIGH|CRITICAL)")
    parser.add_argument("--qa-risk", type=str, default=None, help="QA reviewer risk (LOW|MEDIUM|HIGH|CRITICAL)")
    parser.add_argument("--execution-risk", type=str, default=None, help="Execution reviewer risk (LOW|MEDIUM|HIGH|CRITICAL)")

    args = parser.parse_args()

    try:
        parsed_inputs = validate_and_parse_inputs(args)
        results = calculate_metrics(parsed_inputs)
        
        # Print resulting JSON to stdout
        print(json.dumps(results, indent=2))
        sys.exit(0)
    except ValueError as e:
        # Write validation and calculation errors to stderr and exit with non-zero status
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
