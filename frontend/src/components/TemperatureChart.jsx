import { AreaChart } from "@carbon/charts-react";
import "@carbon/charts/styles.css";

export default function TemperatureChart({ trend, height = "240px" }) {
  if (!trend || trend.length === 0) {
    return <div className="peak-detail-empty">En attente de données…</div>;
  }

  const data = trend.map((point) => ({
    group: "Température palier",
    date: new Date(point.timestamp),
    value: point.temperature_c,
  }));

  const options = {
    axes: {
      bottom: { mapsTo: "date", scaleType: "time" },
      left: { mapsTo: "value", title: "°C", scaleType: "linear" },
    },
    curve: "curveMonotoneX",
    height,
    theme: "g100",
    color: { scale: { "Température palier": "#ff832b" } },
    legend: { enabled: false },
    toolbar: { enabled: false },
    grid: { x: { enabled: false } },
  };

  return <AreaChart data={data} options={options} />;
}
