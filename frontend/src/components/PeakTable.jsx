import DataTable from "./DataTable";
import Badge from "./Badge";

const COLUMNS = [
  { key: "label", header: "Fault" },
  { key: "freq", header: "Frequency", render: (r) => `${r.freq?.toFixed(1) ?? "—"} Hz` },
  { key: "amplitude", header: "Measured amplitude", render: (r) => `${r.amplitude?.toFixed(2) ?? "—"} mm/s²` },
  { key: "thresholds", header: "Thresholds (normal / danger)", render: (r) => `${r.v_normal ?? "—"} · ${r.v_danger ?? "—"}` },
  { key: "severity", header: "Status", render: (r) => <Badge severity={r.severity} /> },
];

export default function PeakTable({ peaks, onSelect, selectedRow }) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={peaks}
      getRowId={(r) => r.row}
      selectedId={selectedRow}
      onRowClick={onSelect}
    />
  );
}
