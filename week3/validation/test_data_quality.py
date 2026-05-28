"""
Data Quality Validation Tests

Mixes two styles:
- Smoke tests against the real parquet (baseline passes; corrupted fails).
- Per-issue tests against synthetic DataFrames (each test isolates one check).

Run from week3/:
    python -m pytest validation/test_data_quality.py -v
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from validation.check_data_quality import DataQualityValidator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CUTOFF = pd.Timestamp("2026-01-16")
PARQUET_PATH = Path(__file__).parent.parent / "data" / "demand_enriched_corrupted.parquet"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_clean_frame(n: int = 200) -> pd.DataFrame:
    """Construct a synthetic 'baseline-shaped' DataFrame with no quality issues.

    Each row is a (time_bucket, PULocationID) combo with plausible values
    matching what the real baseline looks like.
    """
    rng = np.random.default_rng(42)
    times = pd.date_range("2025-01-01", periods=n, freq="15min")
    return pd.DataFrame(
        {
            "time_bucket": times,
            "PULocationID": rng.integers(4, 264, size=n),
            "trip_count": rng.integers(0, 100, size=n).astype("int32"),
            "hour": times.hour.astype("int32"),
            "dayofweek": times.dayofweek.astype("int32"),
            "is_holiday": rng.choice([0, 1], size=n, p=[0.96, 0.04]).astype("int8"),
            "cbd_pricing_active": rng.choice([0, 1], size=n, p=[0.66, 0.34]).astype("int8"),
        }
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def real_df() -> pd.DataFrame:
    """Load the corrupted parquet once per test module."""
    if not PARQUET_PATH.exists():
        pytest.skip(f"Parquet not present at {PARQUET_PATH}")
    return pd.read_parquet(PARQUET_PATH)


@pytest.fixture(scope="module")
def baseline_data(real_df) -> pd.DataFrame:
    """Clean historical window (pre-Jan 16, 2026)."""
    return real_df[real_df["time_bucket"] < CUTOFF].copy()


@pytest.fixture(scope="module")
def corrupted_data(real_df) -> pd.DataFrame:
    """Corrupted window (Jan 16, 2026 and after)."""
    return real_df[real_df["time_bucket"] >= CUTOFF].copy()


@pytest.fixture
def validator(baseline_data) -> DataQualityValidator:
    """Validator initialized with the real baseline."""
    return DataQualityValidator(baseline_data)


@pytest.fixture
def clean_synth() -> pd.DataFrame:
    """A small, clean, synthetic frame for per-issue tests."""
    return _make_clean_frame()


@pytest.fixture
def synth_validator(clean_synth) -> DataQualityValidator:
    """Validator initialized with the synthetic clean frame as baseline."""
    return DataQualityValidator(clean_synth)


# ============================================================================
# Smoke tests: real baseline vs. real corrupted
# ============================================================================
class TestBaselineData:
    """Baseline data must validate cleanly (no false positives)."""

    def test_baseline_passes_validation(self, baseline_data, validator):
        result = validator.validate(baseline_data)
        assert result["is_valid"], (
            f"Baseline failed unexpectedly with {result['num_issues']} issues: "
            f"{result['issues']}"
        )
        assert result["num_issues"] == 0


class TestCorruptedDataFails:
    """The corrupted window must fail validation with multiple issues."""

    def test_corrupted_fails(self, corrupted_data, validator):
        result = validator.validate(corrupted_data)
        assert not result["is_valid"]
        assert result["num_issues"] >= 4, (
            f"Expected at least 4 issues in corrupted window, got "
            f"{result['num_issues']}: {result['issues']}"
        )


# ============================================================================
# Per-issue tests: synthetic data, one bug injected at a time
# ============================================================================
class TestDataQualityIssues:
    """Each test injects exactly one type of bug and asserts the right check fires."""

    def test_detect_negative_trip_count(self, clean_synth, synth_validator):
        """Issue 1a: trip_count must never be negative."""
        bad = clean_synth.copy()
        bad.loc[bad.index[:5], "trip_count"] = -1

        result = synth_validator.validate(bad)

        assert not result["is_valid"]
        types = {i["type"] for i in result["issues"]}
        assert "negative_trip_count" in types

    def test_detect_outlier_trip_count(self, clean_synth, synth_validator):
        """Issue 1b: trip_count above plausible bound (sentinel like 99999)."""
        bad = clean_synth.copy()
        bad.loc[bad.index[:3], "trip_count"] = 99999

        result = synth_validator.validate(bad)

        types = {i["type"] for i in result["issues"]}
        assert "outlier_trip_count" in types

    def test_detect_duplicate_rows(self, clean_synth, synth_validator):
        """Issue 2a: fully identical rows."""
        bad = pd.concat([clean_synth, clean_synth.head(5)], ignore_index=True)

        result = synth_validator.validate(bad)

        types = {i["type"] for i in result["issues"]}
        assert "duplicate_rows" in types

    def test_detect_duplicate_keys(self, clean_synth, synth_validator):
        """Issue 2b: (time_bucket, PULocationID) key collision with different rows."""
        bad = clean_synth.copy()
        # Inject 5 rows that share keys with existing rows but differ elsewhere
        injected = clean_synth.head(5).copy()
        injected["trip_count"] = 999  # different value, same key
        bad = pd.concat([bad, injected], ignore_index=True)

        result = synth_validator.validate(bad)

        types = {i["type"] for i in result["issues"]}
        assert "duplicate_keys" in types

    def test_detect_variance_collapse(self, clean_synth, synth_validator):
        """Issue 3: a binary feature stuck at a single value."""
        bad = clean_synth.copy()
        bad["cbd_pricing_active"] = 1  # all rows stuck at 1, no variance

        result = synth_validator.validate(bad)

        types = {i["type"] for i in result["issues"]}
        assert "variance_collapse" in types

    def test_detect_rate_shift(self, clean_synth, synth_validator):
        """Issue 4: a binary rate shifts way above baseline."""
        bad = clean_synth.copy()
        # Force is_holiday rate from baseline ~4% to ~50%
        bad.loc[bad.index[: len(bad) // 2], "is_holiday"] = 1

        result = synth_validator.validate(bad)

        types = {i["type"] for i in result["issues"]}
        assert "rate_shift" in types


# ============================================================================
# Graceful degradation: validator must never raise, even on garbage input
# ============================================================================
class TestGracefulDegradation:
    """The validator is called from the API startup path — it must never crash."""

    def test_empty_dataframe_does_not_crash(self, synth_validator):
        """An empty frame should be handled silently, not raise."""
        empty = pd.DataFrame(columns=["time_bucket", "PULocationID", "trip_count"])
        result = synth_validator.validate(empty)
        assert isinstance(result, dict)
        assert "is_valid" in result

    def test_missing_columns_does_not_crash(self):
        """Validator must handle frames missing expected columns."""
        v = DataQualityValidator(baseline_df=_make_clean_frame())
        partial = pd.DataFrame({"trip_count": [1, 2, 3]})
        result = v.validate(partial)
        assert isinstance(result, dict)

    def test_no_baseline_does_not_crash(self):
        """Validator instantiated without a baseline should still run."""
        v = DataQualityValidator(baseline_df=None)
        df = _make_clean_frame()
        result = v.validate(df)
        assert isinstance(result, dict)

    def test_validation_logs_on_corrupted(self, caplog, corrupted_data, validator):
        """When issues are detected, downstream code can log them.
        Mirrors what backend/data.py does at startup."""
        with caplog.at_level(logging.WARNING):
            result = validator.validate(corrupted_data)
            if not result["is_valid"]:
                for issue in result["issues"]:
                    logging.warning(
                        "Data quality issue: %s - %s",
                        issue["type"],
                        issue["description"],
                    )
        warning_messages = [r.message for r in caplog.records if r.levelname == "WARNING"]
        assert any("Data quality issue" in m for m in warning_messages)
