import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Waves, Thermometer, Gauge, AlertTriangle, Clock, ListChecks } from "lucide-react";
import { api } from "../api/client";
import Card from "../components/Card";
import Badge from "../components/Badge";
import GradientTrendChart from "../components/GradientTrendChart";
import AlertsList from "../components/AlertsList";
import DataTable from "../components/DataTable";
import SelectField from "../components/SelectField";
import { useMachineConfig } from "../context/MachineConfigContext";

const RANGE_OPTIONS = [
  { value: "15", text: "Last 15 minutes" },
  { value: "60", text: "Last hour" },
  { value: "1440", text: "Last 24 hours" },
  { value: "all", text: "All recorded history" },
];

const TABLE_COLUMNS = [
  { key: "timestamp", header: "Timestamp", render: (r) => new Date(r.timestamp).toLocaleString("en-US") },
  { key: "rms_x", header: "RMS X", render: (r) => r.rms_x?.toFixed(2) },
  { key: "rms_y", header: "RMS Y", render: (r) => r.rms_y?.toFixed(2) },
  { key: "rms_z", header: "RMS Z", render: (r) => r.rms_z?.toFixed(2) },
  { key: "temperature_c", header: "Temp (°C)", render: (r) => r.temperature_c?.toFixed(1) },
  { key: "health_score", header: "Health", render: (r) => r.health_score?.toFixed(0) ?? "—" },
  { key: "overall_severity", header: "Status", render: (r) => <Badge severity={r.overall_severity} /> },
];

export default function HistoryPage() {
  const { defectFrequencies } = useMachineConfig();
  const [range, setRange] = useState("60");
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = { limit: 500 };
    if (range !== "all") params.since_minutes = range;
    api
      .getSnapshots(params)
      .then((rows) => {
        setSnapshots(rows);
        setPage(1);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [range]);

  const rangeLabel = RANGE_OPTIONS.find((r) => r.value === range)?.text;
  const totalPages = Math.max(1, Math.ceil(snapshots.length / pageSize));
  const paginated = snapshots.slice((page - 1) * pageSize, page * pageSize).reverse();

  return (
    <div>
      <div className="topbar">
        <div>
          <h1 className="topbar__title">History</h1>
          <p className="topbar__subtitle">
            Persisted readings and severity transitions — every N-th live frame is snapshotted to the database
          </p>
        </div>
      </div>

      <div className="grid">
        <div className="col-3">
          <Card tight>
            <SelectField id="history-range" label="Time range" value={range} onChange={setRange} options={RANGE_OPTIONS} />
          </Card>
        </div>

        <div className="col-9">
          <Card title="RMS Velocity Trend" subtitle={rangeLabel} icon={Waves} glow="blue">
            <GradientTrendChart
              data={snapshots.map((s) => ({ timestamp: s.timestamp, rms_x: s.rms_x, rms_y: s.rms_y, rms_z: s.rms_z }))}
              series={[
                { key: "rms_x", name: "X axis", color: "blue" },
                { key: "rms_y", name: "Y axis", color: "green" },
                { key: "rms_z", name: "Z axis", color: "purple" },
              ]}
              thresholds={[
                { value: defectFrequencies?.v_normal, label: "Normal", color: "yellow" },
                { value: defectFrequencies?.v_danger, label: "Danger", color: "red" },
              ].filter((t) => t.value)}
            />
          </Card>
        </div>

        <div className="col-6">
          <Card title="Thermal Trend" subtitle={rangeLabel} icon={Thermometer} glow="orange">
            <GradientTrendChart
              data={snapshots.map((s) => ({ timestamp: s.timestamp, temperature_c: s.temperature_c }))}
              series={[{ key: "temperature_c", name: "Temperature", color: "orange" }]}
            />
          </Card>
        </div>

        <div className="col-6">
          <Card title="Health Score Trend" subtitle="Formula-based composite index over time" icon={Gauge} glow="green">
            <GradientTrendChart
              data={snapshots.map((s) => ({ timestamp: s.timestamp, health_score: s.health_score }))}
              series={[{ key: "health_score", name: "Health score", color: "green" }]}
            />
          </Card>
        </div>

        <div className="col-6">
          <Card title="Kurtosis Trend — X axis" subtitle="Early impulsive-fault indicator (healthy ≈ 3.0)" icon={AlertTriangle} glow="purple">
            <GradientTrendChart
              data={snapshots.map((s) => ({ timestamp: s.timestamp, kurtosis_x: s.kurtosis_x }))}
              series={[{ key: "kurtosis_x", name: "Kurtosis — X", color: "purple" }]}
            />
          </Card>
        </div>

        <div className="col-12">
          <Card
            title="Snapshot Log"
            subtitle={error ? `Error: ${error}` : loading ? "Loading…" : `${snapshots.length} readings in range`}
            icon={ListChecks}
            glow="cyan"
          >
            <DataTable columns={TABLE_COLUMNS} rows={paginated} getRowId={(r) => r.id} />
            <div className="pagination">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="pagination__controls">
                <button className="icon-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <ChevronLeft size={15} />
                </button>
                <button className="icon-btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </Card>
        </div>

        <div className="col-12">
          <Card title="Full Alert Log" subtitle="All severity transitions recorded" icon={Clock} glow="red">
            <AlertsList limit={100} />
          </Card>
        </div>
      </div>
    </div>
  );
}
