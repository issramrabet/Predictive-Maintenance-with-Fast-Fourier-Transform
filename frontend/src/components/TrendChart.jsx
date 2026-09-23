import { LineChart } from "@carbon/charts-react";
import "@carbon/charts/styles.css";

export default function TrendChart({ trend, vNormal, vDanger, height = "320px" }) {
  if (!trend || trend.length === 0) {
    return <div className="peak-detail-empty">En attente de données…</div>;
  }

  const data = [];
  trend.forEach((point) => {
    const date = new Date(point.timestamp);
    data.push({ group: "Axe X (radial)", date, value: point.rms_x });
    data.push({ group: "Axe Y (vertical)", date, value: point.rms_y });
    data.push({ group: "Axe Z (axial)", date, value: point.rms_z });
    if (vNormal) data.push({ group: "Seuil normal (B/C)", date, value: vNormal });
    if (vDanger) data.push({ group: "Seuil danger (C/D)", date, value: vDanger });
  });

  const options = {
    title: "",
    axes: {
      bottom: { mapsTo: "date", scaleType: "time" },
      left: { mapsTo: "value", title: "Vitesse RMS (mm/s)", scaleType: "linear" },
    },
    curve: "curveMonotoneX",
    height,
    theme: "g100",
    color: {
      scale: {
        "Axe X (radial)": "#0f62fe",
        "Axe Y (vertical)": "#42be65",
        "Axe Z (axial)": "#8a3ffc",
        "Seuil normal (B/C)": "#f1c21b",
        "Seuil danger (C/D)": "#da1e28",
      },
    },
    legend: { alignment: "left" },
    toolbar: { enabled: false },
    grid: { x: { enabled: false } },
  };

  return <LineChart data={data} options={options} />;
}
