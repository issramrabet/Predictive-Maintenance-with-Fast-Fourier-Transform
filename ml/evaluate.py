
from __future__ import annotations

import argparse

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from features import FEATURE_NAMES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Feature CSV containing the run to evaluate")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", default="rul_evaluation.png")
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    df = df[df["run_id"] == args.run_id].sort_values("timestamp")
    if df.empty:
        raise SystemExit(f"No rows found for run_id '{args.run_id}' in {args.data}")

    model = joblib.load(args.model)
    preds = model.predict(df[FEATURE_NAMES])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["remaining_days"].values, label="Actual (ground truth)", color="#3b82f6", linewidth=2)
    ax.plot(preds, label="Predicted", color="#a855f7", linewidth=2, linestyle="--")
    ax.set_xlabel("Snapshot index (chronological)")
    ax.set_ylabel("Remaining days until failure")
    ax.set_title(f"RUL prediction vs. ground truth — {args.run_id}")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
