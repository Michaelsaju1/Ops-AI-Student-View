"""
Week 3 exploration — diff baseline vs. corrupted windows of demand_enriched_corrupted.parquet
to find data quality issues planted on/after the Jan 16, 2026 cutoff.
"""
import pandas as pd
import numpy as np
from pathlib import Path

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

CUTOFF = pd.Timestamp("2026-01-16")
PATH = Path(__file__).parent.parent / "data" / "demand_enriched_corrupted.parquet"

print(f"\n{'='*80}\nLoading: {PATH}\n{'='*80}")
df = pd.read_parquet(PATH)

baseline = df[df['time_bucket'] < CUTOFF].copy()
corrupted = df[df['time_bucket'] >= CUTOFF].copy()

# ---------- 1. SHAPE & SCHEMA ----------
print(f"\n{'='*80}\n1. SHAPE & SCHEMA\n{'='*80}")
print(f"Total rows:     {len(df):,}")
print(f"Baseline rows:  {len(baseline):,}  (time_bucket < {CUTOFF.date()})")
print(f"Corrupted rows: {len(corrupted):,}  (time_bucket >= {CUTOFF.date()})")
print(f"\nColumns ({len(df.columns)}):")
for col in df.columns:
    print(f"  {col:30s} {str(df[col].dtype):20s}")

# ---------- 2. NULLS ----------
print(f"\n{'='*80}\n2. NULL RATES — baseline vs corrupted (per column)\n{'='*80}")
null_diff = pd.DataFrame({
    'baseline_null_%': (baseline.isna().mean() * 100).round(2),
    'corrupted_null_%': (corrupted.isna().mean() * 100).round(2),
})
null_diff['delta_%'] = (null_diff['corrupted_null_%'] - null_diff['baseline_null_%']).round(2)
null_diff = null_diff.sort_values('delta_%', ascending=False)
print(null_diff)

# ---------- 3. NUMERIC RANGES ----------
print(f"\n{'='*80}\n3. NUMERIC RANGES — baseline vs corrupted\n{'='*80}")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
for col in numeric_cols:
    b = baseline[col].dropna()
    c = corrupted[col].dropna()
    if len(b) == 0 or len(c) == 0:
        continue
    print(f"\n  {col}:")
    print(f"    baseline:  min={b.min():>12.2f}  max={b.max():>12.2f}  "
          f"mean={b.mean():>12.2f}  std={b.std():>12.2f}")
    print(f"    corrupted: min={c.min():>12.2f}  max={c.max():>12.2f}  "
          f"mean={c.mean():>12.2f}  std={c.std():>12.2f}")
    if b.max() > 0 and c.max() > 10 * b.max():
        print(f"    *** OUTLIER FLAG: corrupted max is {c.max()/b.max():.1f}x baseline max")
    if b.mean() != 0 and abs((c.mean() - b.mean()) / b.mean()) > 0.5:
        print(f"    *** DISTRIBUTION SHIFT: mean changed by "
              f"{100*(c.mean()-b.mean())/b.mean():+.1f}%")

# ---------- 4. DUPLICATES ----------
print(f"\n{'='*80}\n4. DUPLICATES\n{'='*80}")
print(f"Baseline  duplicate rows (full row): {baseline.duplicated().sum():,}")
print(f"Corrupted duplicate rows (full row): {corrupted.duplicated().sum():,}")
for key_combo in [['time_bucket', 'PULocationID'], ['time_bucket', 'zone_id'],
                  ['time_bucket', 'pickup_zone']]:
    if all(c in df.columns for c in key_combo):
        b_dups = baseline.duplicated(subset=key_combo).sum()
        c_dups = corrupted.duplicated(subset=key_combo).sum()
        print(f"  Duplicates on {key_combo}: baseline={b_dups:,}  corrupted={c_dups:,}")

# ---------- 5. PER-ZONE CHECKS ----------
print(f"\n{'='*80}\n5. SEGMENTED CHECKS (per-zone null rates)\n{'='*80}")
zone_col = next((c for c in ['PULocationID', 'zone_id', 'pickup_zone'] if c in df.columns), None)
if zone_col:
    print(f"Using zone column: {zone_col}")
    for value_col in numeric_cols[:6]:
        if value_col == zone_col:
            continue
        b_nulls = baseline.groupby(zone_col)[value_col].apply(lambda x: x.isna().mean())
        c_nulls = corrupted.groupby(zone_col)[value_col].apply(lambda x: x.isna().mean())
        diff = (c_nulls - b_nulls).sort_values(ascending=False).head(5)
        if diff.abs().max() > 0.05:
            print(f"\n  {value_col} null-rate diff (corrupted - baseline), top 5 zones:")
            print(diff.to_string())
else:
    print("No zone-like column found")

# ---------- 6. PER-HOUR CHECKS ----------
print(f"\n{'='*80}\n6. SEGMENTED CHECKS (per-hour aggregates)\n{'='*80}")
hour_col = None
if 'hour' in df.columns:
    hour_col = 'hour'
elif 'time_bucket' in df.columns:
    baseline['_hour'] = baseline['time_bucket'].dt.hour
    corrupted['_hour'] = corrupted['time_bucket'].dt.hour
    hour_col = '_hour'
if hour_col and numeric_cols:
    target = next((c for c in ['trip_count', 'demand', 'count'] if c in df.columns),
                  numeric_cols[0])
    print(f"Per-hour mean of '{target}':")
    by_hour = pd.DataFrame({
        'baseline': baseline.groupby(hour_col)[target].mean(),
        'corrupted': corrupted.groupby(hour_col)[target].mean(),
    })
    by_hour['ratio'] = (by_hour['corrupted'] / by_hour['baseline']).round(2)
    print(by_hour)

# ---------- 7. SAMPLES ----------
print(f"\n{'='*80}\n7. SAMPLE ROWS\n{'='*80}")
print("\nBaseline head:")
print(baseline.head(3))
print("\nCorrupted head:")
print(corrupted.head(3))
print("\nCorrupted tail:")
print(corrupted.tail(3))

print(f"\n{'='*80}\nDONE\n{'='*80}")
