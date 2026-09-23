"""
Train a "days until failure" regressor on features built by build_dataset.py.

IMPORTANT — data leakage: split train/test by `run_id` (whole bearing runs),
never by row. Rows from the same bearing run are highly correlated (adjacent
snapshots are seconds apart), so a random row-level split would let the
model "see" a run during training and get an unrealistically good score on
held-out rows from that same run. Splitting by run is the only honest
evaluation here — it tells you how the model does on a bearing it has never
seen, which is the actual real-world use case.

Usage:
    python train_rul_model.py --in features_b1.csv features_b2.csv features_b3.csv --test-run 1st_test_b3_x
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from features import FEATURE_NAMES

DEFAULT_MODEL_OUT = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml_models" / "model.joblib"
DEFAULT_META_OUT = DEFAULT_MODEL_OUT.parent / "feature_names.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="inputs", nargs="+", required=True, help="One or more feature CSVs from build_dataset.py")
    parser.add_argument("--test-run", required=True, help="run_id to hold out entirely for evaluation (must match a run_id in the data)")
    parser.add_argument("--model-out", default=str(DEFAULT_MODEL_OUT))
    parser.add_argument("--meta-out", default=str(DEFAULT_META_OUT))
    args = parser.parse_args()

    df = pd.concat([pd.read_csv(p) for p in args.inputs], ignore_index=True)
    print(f"Loaded {len(df)} rows across {df['run_id'].nunique()} run(s): {sorted(df['run_id'].unique())}")

    if args.test_run not in df["run_id"].unique():
        raise SystemExit(f"--test-run '{args.test_run}' not found. Available: {sorted(df['run_id'].unique())}")

    train_df = df[df["run_id"] != args.test_run]
    test_df = df[df["run_id"] == args.test_run]
    if train_df.empty:
        raise SystemExit("No training rows left after holding out --test-run — pass more than one run in --in.")

    X_train, y_train = train_df[FEATURE_NAMES], train_df["remaining_days"]
    X_test, y_test = test_df[FEATURE_NAMES], test_df["remaining_days"]

    model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )
    print("Training GradientBoostingRegressor…")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    print(f"\nHeld-out run: {args.test_run} ({len(test_df)} snapshots)")
    print(f"  MAE:  {mae:.2f} days")
    print(f"  RMSE: {rmse:.2f} days")
    print(f"  Actual remaining-days range in test run: {y_test.min():.2f} -> {y_test.max():.2f}")

    importances = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1])
    print("\nFeature importances:")
    for name, imp in importances:
        print(f"  {name:14s} {imp:.3f}")

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)
    with open(args.meta_out, "w") as f:
        json.dump({"feature_names": FEATURE_NAMES, "trained_on_runs": sorted(train_df["run_id"].unique().tolist()),
                    "held_out_run": args.test_run, "mae_days": mae, "rmse_days": rmse}, f, indent=2)
    print(f"\nSaved model to {args.model_out}")
    print(f"Saved metadata to {args.meta_out}")


if __name__ == "__main__":
    main()
