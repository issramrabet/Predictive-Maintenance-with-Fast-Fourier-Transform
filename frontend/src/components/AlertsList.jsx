import { useEffect, useState } from "react";
import Badge from "./Badge";
import { api } from "../api/client";

export default function AlertsList({ refreshKey, limit = 20 }) {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getAlerts(limit)
      .then(setAlerts)
      .catch((err) => setError(err.message));
  }, [refreshKey, limit]);

  if (error) return <div className="empty-state">Error: {error}</div>;
  if (alerts.length === 0) return <div className="empty-state">No alerts recorded — the machine has stayed in the normal zone.</div>;

  return (
    <div>
      {alerts.map((a) => (
        <div className="list-row" key={a.id}>
          <Badge severity={a.severity} />
          <span className="list-row__message">{a.message}</span>
          <span className="list-row__time">{new Date(a.timestamp).toLocaleString("en-US")}</span>
        </div>
      ))}
    </div>
  );
}
