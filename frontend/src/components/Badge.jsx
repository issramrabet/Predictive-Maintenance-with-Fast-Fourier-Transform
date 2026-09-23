const META = {
  ok: { label: "Normal", className: "badge--ok", dot: "#4ade80" },
  warn: { label: "Monitor", className: "badge--warn", dot: "#facc15" },
  danger: { label: "Danger", className: "badge--danger", dot: "#f87171" },
};

export default function Badge({ severity }) {
  const m = META[severity] || META.ok;
  return (
    <span className={`badge ${m.className}`}>
      <span className="badge__dot" style={{ background: m.dot }} />
      {m.label}
    </span>
  );
}
