import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import Card from "./Card";
import { api } from "../api/client";

export default function RulCard({ refreshKey }) {
  const [rul, setRul] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getRul().then(setRul).catch((err) => setError(err.message));
  }, [refreshKey]);

  return (
    <Card title="Remaining Useful Life" icon={Clock} glow="pink" badge={rul?.model_available ? "model" : "not trained"}>
      {error && <div className="empty-state">Error: {error}</div>}

      {!error && rul && !rul.model_available && (
        <div className="roadmap-note">
          No trained model found yet. Run the pipeline in <code>ml/</code>
          {" "}(see <code>ml/README.md</code>) against the NASA IMS bearing
          dataset, then restart the backend — this card picks it up
          automatically.
        </div>
      )}

      {!error && rul?.model_available && (
        <>
          <div className="stat-card__value-row" style={{ marginTop: "0.5rem" }}>
            <span className="stat-card__value">
              {rul.remaining_days != null ? rul.remaining_days.toFixed(1) : "—"}
            </span>
            <span className="stat-card__unit">days</span>
          </div>
          {rul.metadata && (
            <div className="stat-card__meta">
              Held-out validation MAE: {rul.metadata.mae_days?.toFixed(1)} days
              {" · "}trained on {rul.metadata.trained_on_runs?.length ?? 0} run(s)
            </div>
          )}
        </>
      )}
    </Card>
  );
}
