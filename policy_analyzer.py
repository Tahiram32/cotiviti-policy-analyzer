"""Healthcare billing policy change analyzer proof of concept.

The demo intentionally uses fictional policy text and synthetic claims. It shows
the basic workflow for comparing policy versions, extracting machine-readable
rules, and validating claims against those rules.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

NUMBER_WORDS = {
    "once": 1,
    "twice": 2,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
}


def read_policy(filename: str) -> str:
    return (DATA_DIR / filename).read_text(encoding="utf-8").strip()


def find_sentence(policy_text: str, phrase: str) -> str:
    for sentence in re.split(r"(?<=\.)\s+", policy_text.strip()):
        if phrase.lower() in sentence.lower():
            return sentence
    return ""


def extract_rules(policy_text: str) -> dict:
    """Extract a small rules object from the fictional policy language."""
    procedure_match = re.search(r"Procedure\s+([A-Z]{2}\d{3})", policy_text)
    frequency_match = re.search(
        r"may be billed\s+(\w+)\s+per patient per day", policy_text, re.IGNORECASE
    )
    age_match = re.search(r"age\s+(\d+)\s+and older", policy_text, re.IGNORECASE)

    if not procedure_match or not frequency_match:
        raise ValueError("Policy text is missing the expected procedure or frequency language.")

    frequency_text = frequency_match.group(1).lower()
    maximum_daily_units = NUMBER_WORDS.get(frequency_text)
    if maximum_daily_units is None:
        raise ValueError(f"Unsupported frequency wording: {frequency_text}")

    authorization_required = "prior authorization is required" in policy_text.lower()
    frequency_sentence = find_sentence(policy_text, "may be billed")
    authorization_sentence = find_sentence(policy_text, "prior authorization is required")

    return {
        "procedure_code": procedure_match.group(1),
        "maximum_daily_units": maximum_daily_units,
        "authorization_required": authorization_required,
        "authorization_minimum_age": int(age_match.group(1)) if age_match else None,
        "rules": [
            {
                "rule_name": "daily_unit_limit",
                "value": maximum_daily_units,
                "source_sentence": frequency_sentence,
                "confidence_score": 0.95,
                "review_status": "needs_human_review",
            },
            {
                "rule_name": "prior_authorization",
                "required": authorization_required,
                "minimum_age": int(age_match.group(1)) if age_match else None,
                "source_sentence": authorization_sentence,
                "confidence_score": 0.95,
                "review_status": "needs_human_review",
            },
        ],
    }


def compare_policies(old_rules: dict, new_rules: dict) -> list[dict]:
    changes = []

    if old_rules["maximum_daily_units"] != new_rules["maximum_daily_units"]:
        changes.append(
            {
                "change_type": "frequency_changed",
                "description": (
                    f"Daily billing frequency changed from "
                    f"{old_rules['maximum_daily_units']} to "
                    f"{new_rules['maximum_daily_units']} procedures per patient per day."
                ),
                "old_value": old_rules["maximum_daily_units"],
                "new_value": new_rules["maximum_daily_units"],
            }
        )

    if old_rules["authorization_minimum_age"] != new_rules["authorization_minimum_age"]:
        old_scope = (
            "all patients"
            if old_rules["authorization_minimum_age"] is None
            else f"patients age {old_rules['authorization_minimum_age']} and older"
        )
        new_scope = (
            "all patients"
            if new_rules["authorization_minimum_age"] is None
            else f"patients age {new_rules['authorization_minimum_age']} and older"
        )
        changes.append(
            {
                "change_type": "authorization_scope_changed",
                "description": f"Authorization requirement changed from {old_scope} to {new_scope}.",
                "old_value": old_scope,
                "new_value": new_scope,
            }
        )

    return changes


def claim_requires_authorization(claim: dict, rules: dict) -> bool:
    if not rules["authorization_required"]:
        return False

    minimum_age = rules["authorization_minimum_age"]
    if minimum_age is None:
        return True

    return int(claim["patient_age"]) >= minimum_age


def validate_claims(rules: dict) -> list[dict]:
    results = []

    with (DATA_DIR / "sample_claims.csv").open(newline="", encoding="utf-8") as claim_file:
        reader = csv.DictReader(claim_file)
        for claim in reader:
            reasons = []

            if claim["procedure_code"] != rules["procedure_code"]:
                reasons.append("Procedure code does not match extracted policy rule")

            if int(claim["units"]) > rules["maximum_daily_units"]:
                reasons.append("Daily unit limit exceeded")

            has_prior_auth = claim["prior_authorization"].strip().lower() == "yes"
            if claim_requires_authorization(claim, rules) and not has_prior_auth:
                reasons.append("Missing prior authorization")

            results.append(
                {
                    "claim_id": claim["claim_id"],
                    "patient_id": claim["patient_id"],
                    "procedure_code": claim["procedure_code"],
                    "units": claim["units"],
                    "status": "FLAGGED" if reasons else "PASS",
                    "reason": "; ".join(reasons) if reasons else "Meets extracted policy rules",
                }
            )

    return results


def write_json(filename: str, data: object) -> None:
    (OUTPUT_DIR / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_claim_results(results: list[dict]) -> None:
    output_path = OUTPUT_DIR / "claim_results.csv"
    with output_path.open("w", newline="", encoding="utf-8") as results_file:
        fieldnames = ["claim_id", "patient_id", "procedure_code", "units", "status", "reason"]
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    old_policy = read_policy("policy_v1.txt")
    new_policy = read_policy("policy_v2.txt")

    old_rules = extract_rules(old_policy)
    new_rules = extract_rules(new_policy)
    changes = compare_policies(old_rules, new_rules)
    claim_results = validate_claims(new_rules)

    write_json("policy_changes.json", changes)
    write_json("extracted_rules.json", new_rules)
    write_claim_results(claim_results)

    print("Healthcare Policy Change Analyzer POC")
    print(f"Detected policy changes: {len(changes)}")
    print(f"Claims checked: {len(claim_results)}")
    print("Generated output/policy_changes.json")
    print("Generated output/extracted_rules.json")
    print("Generated output/claim_results.csv")


if __name__ == "__main__":
    main()
