"""
CLI entrypoint for the data-quality validator.

Used by .github/workflows/validate-data.yml. Loads the corrupted parquet,
splits on the Jan 16 2026 cutoff, runs the validator, prints findings,
and exits non-zero if any issues were found so the workflow is marked
as failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from validation.check_data_quality import DataQualityValidator


CUTOFF = pd.Timestamp("2026-01-16")
PARQUET_PATH = Path(__file__).parent.parent / "data" / "demand_enriched_corrupted.parquet"


def main() -> int:
    if not PARQUET_PATH.exists():
        print(f"ERROR: Parquet not found at {PARQUET_PATH}", file=sys.stderr)
        return 1

    print(f"Loading parquet: {PARQUET_PATH}")
    df = pd.read_parquet(PARQUET_PATH)

    baseline_df = df[df["time_bucket"] < CUTOFF]
    incoming_df = df[df["time_bucket"] >= CUTOFF]

    print(f"Baseline rows:  {len(baseline_df):,}")
    print(f"Incoming rows:  {len(incoming_df):,}")

    validator = DataQualityValidator(baseline_df=baseline_df)
    result = validator.validate(incoming_df)

    print()
    print("=" * 70)
    if result["is_valid"]:
        print("PASS: No data quality issues found.")
        print("=" * 70)
        return 0

    print(f"FAIL: {result['num_issues']} data quality issue(s) detected.")
    print("=" * 70)
    for i, issue in enumerate(result["issues"], 1):
        print(
            f"  [{i}] [{issue['severity'].upper()}] {issue['type']}"
            f" (count={issue.get('count')})"
        )
        print(f"      {issue['description']}")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(main())
