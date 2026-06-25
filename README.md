# Automated Healthcare Policy Change Analyzer

This repository contains an internship assessment proof of concept for Topic 3: Content Management in Health Care.

## Project Title

Automated Healthcare Policy Change Analyzer: Converting Written Billing Policies into Machine-Readable Rules

## Purpose

The project demonstrates how a simple Python program can compare two fictional healthcare billing policy versions, identify policy changes, convert written requirements into structured JSON rules, and test synthetic healthcare claims against those rules.

All policies and claims in this repository are fictional. No real patient information is used.

## Repository Structure

```text
cotiviti-policy-analyzer/
├── README.md
├── requirements.txt
├── policy_analyzer.py
├── data/
│   ├── policy_v1.txt
│   ├── policy_v2.txt
│   └── sample_claims.csv
├── output/
│   └── .gitkeep
├── report/
│   └── .gitkeep
├── presentation/
│   └── .gitkeep
└── video/
    └── .gitkeep
```

## Planned Deliverables

- Word report
- Python proof of concept
- PowerPoint presentation
- MP4 presentation recording

## How to Run

Run the proof of concept from the repository root:

```bash
python3 policy_analyzer.py
```

The script reads:

- `data/policy_v1.txt`
- `data/policy_v2.txt`
- `data/sample_claims.csv`

The script generates:

- `output/policy_changes.json`
- `output/extracted_rules.json`
- `output/claim_results.csv`

## Current Demo Scenario

The fictional policy update changes procedure `HC100` from once per patient per day to twice per patient per day. It also changes the prior authorization rule from all patients to patients age 18 and older.

The sample claims demonstrate:

- A passing claim
- A claim flagged for exceeding the daily unit limit
- A claim flagged for missing prior authorization
- A minor patient claim that passes because the revised authorization rule applies only to patients age 18 and older
