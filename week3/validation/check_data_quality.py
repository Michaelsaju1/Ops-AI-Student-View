"""
Data Quality Validation Framework Template

This file is a starting point for your validation code.
Modify or replace as needed based on the issues you identify.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class DataQualityValidator:
    """Validates data against quality expectations."""

    def __init__(self, baseline_df: pd.DataFrame = None):
        """
        Initialize validator.

        Args:
            baseline_df: Clean reference data for comparison
        """
        self.baseline = baseline_df
        self.issues = []

    def validate(self, df: pd.DataFrame) -> Dict:
        """
        Run all validation checks.

        Returns:
            Dictionary with:
            - is_valid: boolean
            - num_issues: count of issues found
            - issues: list of issue details
        """
        self.issues = []

        # TODO: Add your validation checks here
        # Example structure:
        self.check_null_rates(df)
        self.check_value_ranges(df)
        self.check_duplicates(df)
        self.check_distributions(df)

        return {
            "is_valid": len(self.issues) == 0,
            "num_issues": len(self.issues),
            "issues": self.issues,
        }

    def check_null_rates(self, df: pd.DataFrame):
        """Check if any column has excessive nulls."""
        # TODO: Implement
        # What threshold is acceptable? (depends on your data)
        # Which columns are critical (can't have any nulls)?
        if self.baseline is None or len(self.baseline) == 0:
            # No reference data, skip check rather than crash. The startup
            # path can still validate ranges/duplicates/distributions, just
            # not relative null shifts.
            return

        NULL_RATE_DELTA = 0.05  # 5 percentage points

        baseline_nulls = self.baseline.isna().mean()
        current_nulls = df.isna().mean()

        # Only compare columns that exist in both frames
        shared_cols = baseline_nulls.index.intersection(current_nulls.index)

        for col in shared_cols:
            delta = current_nulls[col] - baseline_nulls[col]
            if delta > NULL_RATE_DELTA:
                self._add_issue(
                    issue_type="null_rate_spike",
                    severity="high",
                    description=(
                        f"Column '{col}' null rate jumped from "
                        f"{baseline_nulls[col]*100:.1f}% (baseline) to "
                        f"{current_nulls[col]*100:.1f}% (current), "
                        f"a {delta*100:.1f} pp increase."
                    ),
                    count=int(df[col].isna().sum()),
                    column=col,
                    baseline_null_rate=float(baseline_nulls[col]),
                    current_null_rate=float(current_nulls[col]),
                )

    def check_value_ranges(self, df: pd.DataFrame):
        """Check if values fall within expected ranges."""
        # TODO: Implement
        # Examples:
        # - trip_count should be >= 0
        # - hour should be 0-23
        # - dayofweek should be 0-6
        # - zone IDs should be valid
        if "trip_count" in df.columns:
            neg = df["trip_count"] < 0
            if neg.any():
                bad_values = sorted(df.loc[neg, "trip_count"].unique().tolist())
                self._add_issue(
                    issue_type="negative_trip_count",
                    severity="critical",
                    description=(
                        f"trip_count has {int(neg.sum())} negative values "
                        f"(impossible). Distinct negatives seen: {bad_values}"
                    ),
                    count=int(neg.sum()),
                    column="trip_count",
                )

            # --- trip_count: plausible upper bound ---
            UPPER_BOUND = 500
            high = df["trip_count"] > UPPER_BOUND
            if high.any():
                max_seen = int(df.loc[high, "trip_count"].max())
                self._add_issue(
                    issue_type="outlier_trip_count",
                    severity="critical",
                    description=(
                        f"trip_count has {int(high.sum())} values above {UPPER_BOUND} "
                        f"(max seen: {max_seen}). Likely sentinel/error codes "
                        f"(e.g., 99999) leaking from upstream."
                    ),
                    count=int(high.sum()),
                    column="trip_count",
                )

        # --- hour: must be 0-23 ---
        if "hour" in df.columns:
            bad_hour = (df["hour"] < 0) | (df["hour"] > 23)
            if bad_hour.any():
                self._add_issue(
                    issue_type="invalid_hour",
                    severity="high",
                    description=f"hour column has {int(bad_hour.sum())} values outside 0-23",
                    count=int(bad_hour.sum()),
                    column="hour",
                )

        # --- dayofweek: must be 0-6 ---
        if "dayofweek" in df.columns:
            bad_dow = (df["dayofweek"] < 0) | (df["dayofweek"] > 6)
            if bad_dow.any():
                self._add_issue(
                    issue_type="invalid_dayofweek",
                    severity="high",
                    description=f"dayofweek column has {int(bad_dow.sum())} values outside 0-6",
                    count=int(bad_dow.sum()),
                    column="dayofweek",
                )

    def check_distributions(self, df: pd.DataFrame):
        """Detect distribution drift on binary feature columns vs baseline.

        Two failure modes are checked, both specific to binary (0/1) features:

        - Variance collapse: a column that historically varied (baseline std
          > 0.05) is now constant or near-constant (current std < 0.01).
          Suggests an upstream flag got stuck or a transformation is dropping
          variation. The feature loses signal for the model even if no row
          is technically "wrong".

        - Rate inflation: a binary feature's positive rate has shifted by
          more than 2x and the absolute change is > 5 percentage points.
          Tight enough to ignore random fluctuations, loose enough to avoid
          over-firing on noisy low-rate features.

        Only applied to binary columns (values strictly in {0, 1}); continuous
        columns like lag_*/roll_* legitimately drift between time windows.
        """

        if self.baseline is None or len(self.baseline) == 0:
            return

        # Identify binary columns present in both frames
        shared_cols = self.baseline.columns.intersection(df.columns)
        for col in shared_cols:
            b_series = self.baseline[col].dropna()
            c_series = df[col].dropna()
            if len(b_series) == 0 or len(c_series) == 0:
                continue
            # Require strictly binary values
            b_uniques = set(pd.unique(b_series))
            if not b_uniques.issubset({0, 1}):
                continue

            b_mean = float(b_series.mean())
            c_mean = float(c_series.mean())
            b_std = float(b_series.std())
            c_std = float(c_series.std())

            # --- Variance collapse ---
            if b_std > 0.05 and c_std < 0.01:
                self._add_issue(
                    issue_type="variance_collapse",
                    severity="medium",
                    description=(
                        f"Column '{col}' lost variance: baseline std={b_std:.3f}, "
                        f"current std={c_std:.3f}. Column is effectively constant "
                        f"(mean={c_mean:.3f}). Likely a stuck upstream flag."
                    ),
                    count=int(len(c_series)),
                    column=col,
                    baseline_std=b_std,
                    current_std=c_std,
                    current_mean=c_mean,
                )
                continue  # already flagged; skip rate-shift check for this col

            # --- Rate inflation ---
            abs_delta = abs(c_mean - b_mean)
            ratio = (c_mean / b_mean) if b_mean > 0 else float("inf")
            if abs_delta > 0.05 and ratio > 2.0:
                self._add_issue(
                    issue_type="rate_shift",
                    severity="high",
                    description=(
                        f"Column '{col}' positive rate shifted from "
                        f"{b_mean*100:.1f}% (baseline) to {c_mean*100:.1f}% "
                        f"(current), a {ratio:.1f}x increase. Likely "
                        f"misclassification or overpropagation upstream."
                    ),
                    count=int(c_series.sum()),
                    column=col,
                    baseline_rate=b_mean,
                    current_rate=c_mean,
                    ratio=ratio,
                )

    def check_duplicates(self, df: pd.DataFrame):
        """Check for duplicate rows on natural keys and full rows.
        Two flavors are checked because they point at different upstream bugs:
        - Full-row duplicates: a row repeated verbatim. Usually indicates a
          re-ingestion or backfill that didn't dedupe at the source.
        - Key-only duplicates: the natural key (time_bucket, PULocationID)
          appears twice with potentially different feature values. Usually
          indicates non-deterministic upstream aggregation. Downstream joins
          would produce a row multiplication.
        """
        KEY = ["time_bucket", "PULocationID"]

        # --- full-row duplicates ---
        full_dups = df.duplicated().sum()
        if full_dups > 0:
            self._add_issue(
                issue_type="duplicate_rows",
                severity="high",
                description=(
                    f"{int(full_dups)} fully identical duplicate rows. "
                    f"Suggests re-ingestion or backfill without dedup."
                ),
                count=int(full_dups),
            )

        # --- key duplicates (only if both key columns exist) ---
        if all(c in df.columns for c in KEY):
            key_dups = df.duplicated(subset=KEY).sum()
            if key_dups > 0:
                self._add_issue(
                    issue_type="duplicate_keys",
                    severity="high",
                    description=(
                        f"{int(key_dups)} rows share a {KEY} key with another row. "
                        f"Natural key must be unique — duplicates will multiply rows "
                        f"in downstream joins."
                    ),
                    count=int(key_dups),
                    key_columns=KEY,
                )


    def check_schema(self, df: pd.DataFrame):
        """Check that required columns exist with correct types."""
        # TODO: Implement
        # What columns are required?
        # What types should they be?
        pass

    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        description: str,
        count: int = None,
        **details
    ):
        """Helper to add issue to list."""
        issue = {
            "type": issue_type,
            "severity": severity,  # 'critical', 'high', 'medium', 'low'
            "description": description,
            "count": count,
            **details,
        }
        self.issues.append(issue)


# Optional: Utility functions


def compare_distributions(
    baseline: pd.Series, current: pd.Series, threshold: float = 2.0
) -> bool:
    """
    Compare distributions using standard deviations.

    Returns True if distributions are significantly different.
    """
    # TODO: Implement comparison logic
    pass


def detect_outliers(
    series: pd.Series, baseline_series: pd.Series = None, sigma: float = 3.0
) -> pd.Series:
    """
    Detect outliers in a numeric series.

    Returns boolean Series indicating which values are outliers.
    """
    # TODO: Implement outlier detection
    pass
