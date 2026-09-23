
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ims_loader import list_ims_files, load_ims_samples  # noqa: E402
from features import extract_features, FEATURE_NAMES  # noqa: E402


def build(data_dir: str, bearing_index: int, axis: str, run_id: str) -> pd.DataFrame:
    files = list_ims_files(data_dir)
    if not files:
        raise SystemExit(f"No IMS snapshot files found in {data_dir} — check the path.")

    failure_time = files[-1].timestamp
    rows = []
    for f in files:
        samples = load_ims_samples(f.path, bearing_index=bearing_index, axis=axis)
        feats = extract_features(samples)
        remaining_seconds = (failure_time - f.timestamp).total_seconds()
        rows.append({
            "run_id": run_id,
            "timestamp": f.timestamp,
            **feats,
            "remaining_days": remaining_seconds / 86400.0,
        })
        if len(rows) % 100 == 0:
            print(f"  processed {len(rows)}/{len(files)} files…")

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Path to one IMS test-run folder (e.g. ./data/1st_test)")
    parser.add_argument("--bearing", type=int, required=True, choices=[0, 1, 2, 3], help="Bearing index (0-3)")
    parser.add_argument("--axis", default="x", choices=["x", "y"], help="Channel axis (only matters for test set 1, which has x+y per bearing)")
    parser.add_argument("--run-id", default=None, help="Label for this run (defaults to '<folder>_b<bearing>_<axis>')")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()

    run_id = args.run_id or f"{Path(args.data_dir).name}_b{args.bearing}_{args.axis}"
    print(f"Building dataset for {run_id} from {args.data_dir} …")
    df = build(args.data_dir, args.bearing, args.axis, run_id)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")
    print(f"Remaining-days range: {df['remaining_days'].min():.2f} -> {df['remaining_days'].max():.2f}")


if __name__ == "__main__":
    main()
