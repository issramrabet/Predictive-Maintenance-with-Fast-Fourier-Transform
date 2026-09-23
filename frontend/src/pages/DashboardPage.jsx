import { useState } from "react";
import { Thermometer, Zap, AlertTriangle, Gauge, Activity, Waves, Clock } from "lucide-react";
import { useLiveFeedContext } from "../context/LiveFeedContext";
import { useMachineConfig } from "../context/MachineConfigContext";
import Card from "../components/Card";
import StatCard from "../components/StatCard";
import Badge from "../components/Badge";
import GradientTrendChart from "../components/GradientTrendChart";
import DonutChart from "../components/DonutChart";
import AlertsList from "../components/AlertsList";
import DemoFaultControl from "../components/DemoFaultControl";
import HealthGauge from "../components/HealthGauge";
import RulCard from "../components/RulCard";
import { useEffect } from "react";
import { api } from "../api/client";

export default function DashboardPage() {
  const { frame, connected, trend } = useLiveFeedContext();
  const { defectFrequencies } = useMachineConfig();
  const [refreshKey, setRefreshKey] = useState(0);
  const [severitySummary, setSeveritySummary] = useState(null);

  useEffect(() => {
    api.getSeveritySummary().then(setSeveritySummary).catch(() => {});
  }, [refreshKey]);

  const vNormal = defectFrequencies?.v_normal;
  const vDanger = defectFrequencies?.v_danger;
  const maxRms = frame ? Math.max(frame.rms_velocity_mm_s.x, frame.rms_velocity_mm_s.y, frame.rms_velocity_mm_s.z) : null;

  return (
    <div>
      <div className="topbar">
        <div>
          <h1 className="topbar__title">Real-Time Dashboard</h1>
          <p className="topbar__subtitle">
            Asynchronous motor — HS-173HT (triaxial accelerometer + temperature) — monitored bearing
          </p>
        </div>
        <span className="status-pill">
          <span className="status-pill__dot" style={{ background: connected ? "#4ade80" : "#f87171" }} />
          {connected ? "Sensor connected (simulation)" : "Disconnected"}
        </span>
      </div>

      <div className="grid">
        <div className="col-3">
          <Card title="Health Score" badge="formula-based" glow="green">
            <div style={{ display: "flex", justifyContent: "center", marginTop: "0.5rem" }}>
              <HealthGauge score={frame?.health_score} />
            </div>
          </Card>
        </div>

        <div className="col-3">
          <Card title="Overall Status" subtitle="ISO 20816-3 severity zone" icon={Activity} glow="blue">
            <div style={{ marginTop: "0.4rem" }}>{frame ? <Badge severity={frame.overall_severity} /> : "—"}</div>
            <div className="stat-card__meta" style={{ marginTop: "0.7rem" }}>
              {frame ? `Max RMS velocity ${maxRms.toFixed(2)} mm/s` : "Waiting for data…"}
            </div>
            <div className="stat-card__meta" style={{ marginTop: "0.3rem" }}>
              Active simulated fault: <strong style={{ color: "#f4f3f9" }}>{frame?.active_fault ? `Row ${frame.active_fault}` : "None"}</strong>
            </div>
          </Card>
        </div>

        <div className="col-3">
          <StatCard
            label="RMS Velocity — X (radial)"
            value={frame ? frame.rms_velocity_mm_s.x.toFixed(2) : "—"}
            unit="mm/s"
            meta={vNormal ? `Thresholds ${vNormal} / ${vDanger} mm/s` : ""}
            icon={Waves}
            glow="blue"
          />
        </div>
        <div className="col-3">
          <StatCard
            label="RMS — Y (vertical)"
            value={frame ? frame.rms_velocity_mm_s.y.toFixed(2) : "—"}
            unit="mm/s"
            icon={Waves}
            glow="green"
          />
        </div>

        <div className="col-3">
          <StatCard
            label="RMS — Z (axial)"
            value={frame ? frame.rms_velocity_mm_s.z.toFixed(2) : "—"}
            unit="mm/s"
            icon={Waves}
            glow="purple"
          />
        </div>
        <div className="col-3">
          <StatCard
            label="Bearing Temperature"
            value={frame ? frame.temperature_c.toFixed(1) : "—"}
            unit="°C"
            icon={Thermometer}
            glow="orange"
          />
        </div>
        <div className="col-3">
          <StatCard
            label="Crest Factor — X"
            value={frame ? frame.crest_factor.x.toFixed(2) : "—"}
            meta="Healthy ≈ 1.4 (√2)"
            icon={Zap}
            glow="cyan"
          />
        </div>
        <div className="col-3">
          <StatCard
            label="Kurtosis — X"
            value={frame ? frame.kurtosis.x.toFixed(2) : "—"}
            meta="Healthy ≈ 3.0 — impacts push it higher"
            icon={AlertTriangle}
            glow="yellow"
          />
        </div>

        <div className="col-6">
          <Card title="RMS Velocity Trend (ISO 20816-3)" subtitle="Live rolling window, with zone B/C and C/D thresholds overlaid" icon={Waves} glow="blue">
            <GradientTrendChart
              data={trend.map((t) => ({ timestamp: t.timestamp, rms_x: t.rms_x, rms_y: t.rms_y, rms_z: t.rms_z }))}
              series={[
                { key: "rms_x", name: "X axis (radial)", color: "blue" },
                { key: "rms_y", name: "Y axis (vertical)", color: "green" },
                { key: "rms_z", name: "Z axis (axial)", color: "red" },
              ]}
              thresholds={[
                { value: vNormal, label: "Normal", color: "yellow" },
                { value: vDanger, label: "Danger", color: "red" },
              ].filter((t) => t.value)}
              yLabel="mm/s"
            />
          </Card>
        </div>

        <div className="col-3">
          <Card title="Severity Distribution" subtitle="All persisted readings so far" icon={Gauge} glow="purple">
            {severitySummary && (
              <DonutChart
                centerLabel="Readings"
                slices={[
                  { label: "Normal", value: severitySummary.ok, color: "green" },
                  { label: "Monitor", value: severitySummary.warn, color: "yellow" },
                  { label: "Danger", value: severitySummary.danger, color: "red" },
                ]}
              />
            )}
          </Card>
        </div>

        <div className="col-3">
          <StatCard
            label="Peak Acceleration — X"
            value={frame ? frame.peak_accel_g.x.toFixed(3) : "—"}
            unit="g"
            icon={Zap}
            glow="cyan"
          />
        </div>

        <div className="col-3">
          <RulCard refreshKey={refreshKey} />
        </div>

        <div className="col-6">
          <Card title="Thermal Drift" subtitle="Monitored bearing temperature" icon={Thermometer} glow="orange">
            <GradientTrendChart
              data={trend.map((t) => ({ timestamp: t.timestamp, temperature_c: t.temperature_c }))}
              series={[{ key: "temperature_c", name: "Temperature", color: "orange" }]}
              yLabel="°C"
            />
          </Card>
        </div>

        <div className="col-6">
          <Card title="Alert Log" subtitle="Severity transitions recorded" icon={AlertTriangle} glow="red">
            <AlertsList refreshKey={refreshKey} />
          </Card>
        </div>

        <div className="col-12">
          <Card title="Demo Mode" subtitle="No physical sensor required to explore the dashboard" icon={Activity} glow="purple">
            <DemoFaultControl onChange={() => setRefreshKey((k) => k + 1)} />
          </Card>
        </div>
      </div>
    </div>
  );
}
